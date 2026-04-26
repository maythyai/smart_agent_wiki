"""Tests for Write Queue Dispatcher."""
from __future__ import annotations

import sqlite3
import uuid
from unittest.mock import MagicMock

import pytest

from saw.write_queue.dispatcher import Dispatcher
from saw.write_queue.queue import SQLiteWriteQueue, WriteOp


@pytest.fixture
def conn(tmp_path):
    """Create a temporary SQLite connection."""
    db_path = tmp_path / "test_dispatcher.db"
    connection = sqlite3.connect(str(db_path))
    yield connection
    connection.close()


@pytest.fixture
def queue(conn):
    """Create a Write Queue instance."""
    return SQLiteWriteQueue(conn)


def _make_op(sink_name: str = "vault", **kwargs) -> WriteOp:
    """Create a test WriteOp."""
    return WriteOp(
        op_id=kwargs.get("op_id", str(uuid.uuid4())),
        session_id=kwargs.get("session_id", "sess-1"),
        sink_name=sink_name,
        payload=kwargs.get("payload", {"data": "test"}),
    )


class TestDispatchPending:
    """Test dispatch_pending processes all pending ops."""

    def test_dispatches_to_matching_sink(self, queue):
        sink = MagicMock()
        sink.name = "vault"
        dispatcher = Dispatcher(queue, [sink])

        op = _make_op(sink_name="vault")
        queue.enqueue([op])

        processed = dispatcher.dispatch_pending()
        assert processed == 1
        sink.write.assert_called_once()

    def test_failed_sink_gets_retried(self, queue):
        sink = MagicMock()
        sink.name = "vault"
        sink.write.side_effect = [Exception("first fail"), None]  # fails first, succeeds second
        dispatcher = Dispatcher(queue, [sink])

        op = _make_op(sink_name="vault")
        queue.enqueue([op])

        # First dispatch: fails
        dispatcher.dispatch_pending()
        pending = queue.get_pending()
        assert len(pending) == 1
        assert pending[0].retry_count == 1

        # Second dispatch: succeeds
        dispatcher.dispatch_pending()
        pending = queue.get_pending()
        assert len(pending) == 0

    def test_no_matching_sink_skips(self, queue):
        sink = MagicMock()
        sink.name = "vault"
        dispatcher = Dispatcher(queue, [sink])

        op = _make_op(sink_name="nonexistent")
        queue.enqueue([op])

        processed = dispatcher.dispatch_pending()
        assert processed == 0


class TestRecover:
    """Test crash recovery."""

    def test_recover_resets_processing_to_pending(self, queue):
        sink = MagicMock()
        sink.name = "vault"
        dispatcher = Dispatcher(queue, [sink])

        op = _make_op(sink_name="vault")
        queue.enqueue([op])

        # Manually mark as processing (simulating crash mid-dispatch)
        queue.mark_processing(op.op_id)

        # get_pending won't return PROCESSING ops
        assert len(queue.get_pending()) == 0

        # recover should reset to pending
        recovered = dispatcher.recover()
        assert recovered == 1

        # Now get_pending should return it
        assert len(queue.get_pending()) == 1


class TestIdempotentSink:
    """Test that dispatching same op twice does not duplicate data."""

    def test_idempotent_dispatch(self, queue):
        sink = MagicMock()
        sink.name = "vault"
        dispatcher = Dispatcher(queue, [sink])

        op = _make_op(sink_name="vault")
        queue.enqueue([op])

        # First dispatch
        dispatcher.dispatch_pending()
        assert sink.write.call_count == 1

        # No more pending
        dispatcher.dispatch_pending()
        assert sink.write.call_count == 1  # Not called again

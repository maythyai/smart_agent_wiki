"""Tests for Write Queue."""
from __future__ import annotations

import sqlite3
import uuid

import pytest

from saw.write_queue.queue import SQLiteWriteQueue, WriteOp


@pytest.fixture
def conn(tmp_path):
    """Create a temporary SQLite connection with Write Queue tables."""
    db_path = tmp_path / "test_queue.db"
    connection = sqlite3.connect(str(db_path))
    yield connection
    connection.close()


@pytest.fixture
def queue(conn):
    """Create a Write Queue instance."""
    return SQLiteWriteQueue(conn)


def _make_op(sink_name: str = "vault", session_id: str = "sess-1", **kwargs) -> WriteOp:
    """Create a test WriteOp."""
    return WriteOp(
        op_id=kwargs.get("op_id", str(uuid.uuid4())),
        session_id=session_id,
        sink_name=sink_name,
        payload=kwargs.get("payload", {"data": "test"}),
    )


class TestEnqueue:
    """Test enqueue operations."""

    def test_enqueue_inserts_all_ops(self, queue):
        ops = [_make_op(), _make_op(), _make_op()]
        queue.enqueue(ops)
        pending = queue.get_pending()
        assert len(pending) == 3

    def test_enqueue_is_atomic(self, queue):
        """If one op fails (duplicate), the whole batch fails."""
        op_id = str(uuid.uuid4())
        ops1 = [_make_op(op_id=op_id)]
        queue.enqueue(ops1)

        # Second batch with duplicate op_id should fail
        ops2 = [_make_op(op_id=op_id)]
        with pytest.raises(Exception):
            queue.enqueue(ops2)

        # Original ops should still be there
        pending = queue.get_pending()
        assert len(pending) == 1

    def test_enqueue_with_duplicate_op_id_raises(self, queue):
        op_id = str(uuid.uuid4())
        queue.enqueue([_make_op(op_id=op_id)])
        with pytest.raises(Exception):
            queue.enqueue([_make_op(op_id=op_id)])


class TestGetPending:
    """Test get_pending returns only pending ops with retry_count < max."""

    def test_returns_only_pending(self, queue):
        queue.enqueue([_make_op(), _make_op()])
        # Mark one as done
        ops = queue.get_pending()
        queue.mark_done(ops[0].op_id)

        pending = queue.get_pending()
        assert len(pending) == 1

    def test_exceeds_retry_count_not_returned(self, queue):
        op = _make_op()
        op.max_retries = 2
        queue.enqueue([op])

        # Fail it 3 times (exceeds max_retries=2)
        for _ in range(3):
            ops = queue.get_pending()
            if not ops:
                break
            queue.mark_failed(ops[0].op_id, "test error")

        pending = queue.get_pending()
        assert len(pending) == 0


class TestMarkTransitions:
    """Test mark_done and mark_failed transitions."""

    def test_mark_done(self, queue):
        op = _make_op()
        queue.enqueue([op])
        queue.mark_done(op.op_id)
        pending = queue.get_pending()
        assert len(pending) == 0

    def test_mark_failed_increments_retry(self, queue):
        op = _make_op()
        queue.enqueue([op])
        queue.mark_failed(op.op_id, "error")

        pending = queue.get_pending()
        assert len(pending) == 1
        assert pending[0].retry_count == 1
        assert pending[0].error_message == "error"


class TestSinkTracking:
    """Test per-sink status tracking."""

    def test_track_sink_records_status(self, queue):
        op = _make_op()
        queue.enqueue([op])
        queue.track_sink(op.op_id, "vault", "done")
        queue.track_sink(op.op_id, "claims", "done")

        status = queue.get_sink_status(op.op_id)
        assert status["vault"] == "done"
        assert status["claims"] == "done"

    def test_track_sink_with_error(self, queue):
        op = _make_op()
        queue.enqueue([op])
        queue.track_sink(op.op_id, "fts5", "failed", "write error")

        status = queue.get_sink_status(op.op_id)
        assert status["fts5"] == "failed"

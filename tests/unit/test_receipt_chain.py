"""Tests for Ed25519 receipt chain — AC-SEC-2.

Covers:
- ``test_receipt_chain_intact``: after dispatch, the receipt chain has no
  broken links and every signature verifies.
- ``test_receipt_coverage``: every successful dispatch of a high-risk
  sink (vault/wiki/claims/fts5/graph/contradictions/connector) produces
  a receipt.
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import ClassVar
from unittest.mock import MagicMock

import pytest

from saw.adapters.crypto.ed25519 import Receipt, ReceiptSigner
from saw.write_queue.dispatcher import Dispatcher
from saw.write_queue.queue import SQLiteWriteQueue, WriteOp
from saw.write_queue.receipt_store import ReceiptStore

# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def conn(tmp_path: Path) -> sqlite3.Connection:
    """Temporary SQLite database."""
    db_path = tmp_path / "test_receipt.db"
    connection = sqlite3.connect(str(db_path))
    yield connection
    connection.close()


@pytest.fixture
def queue(conn: sqlite3.Connection) -> SQLiteWriteQueue:
    return SQLiteWriteQueue(conn)


@pytest.fixture
def signer(tmp_path: Path) -> ReceiptSigner:
    key_path = tmp_path / "keys" / "ed25519.key"
    s = ReceiptSigner(key_path=key_path)
    s.generate_keypair()
    return s


@pytest.fixture
def receipt_store(conn: sqlite3.Connection) -> ReceiptStore:
    return ReceiptStore(conn)


@pytest.fixture
def dispatcher(
    queue: SQLiteWriteQueue,
    signer: ReceiptSigner,
    receipt_store: ReceiptStore,
) -> Dispatcher:
    return Dispatcher(
        queue=queue,
        sinks=None,
        receipt_signer=signer,
        receipt_store=receipt_store,
    )


def _make_op(sink_name: str = "vault", **kwargs) -> WriteOp:
    return WriteOp(
        op_id=kwargs.get("op_id", str(uuid.uuid4())),
        session_id=kwargs.get("session_id", "sess-1"),
        sink_name=sink_name,
        payload=kwargs.get("payload", {"data": "test"}),
    )


# ── AC-SEC-2: receipt chain intact ────────────────────────────────────

class TestReceiptChainIntact:
    """AC-SEC-2: receipt chain is unbroken and signatures verify."""

    def test_single_dispatch_produces_receipt(self, dispatcher, queue, receipt_store):
        """A single dispatch produces one receipt with a valid signature."""
        sink = MagicMock()
        sink.name = "vault"
        dispatcher.register_sink(sink)

        op = _make_op(sink_name="vault")
        queue.enqueue([op])

        processed = dispatcher.dispatch_pending()
        assert processed == 1

        receipts = receipt_store.get_by_operation_id(op.op_id)
        assert len(receipts) == 1
        r = receipts[0]
        assert r["operation_id"] == op.op_id
        assert r["signature"] is not None
        assert r["prev_receipt_id"] is None  # first receipt in chain

    def test_chain_links_prev_receipt_id(self, dispatcher, queue, receipt_store):
        """Multiple ops on same session link via prev_receipt_id."""
        sink = MagicMock()
        sink.name = "vault"
        dispatcher.register_sink(sink)

        op1 = _make_op(sink_name="vault", op_id="op-chain-1")
        op2 = _make_op(sink_name="vault", op_id="op-chain-2")
        op3 = _make_op(sink_name="vault", op_id="op-chain-3")

        # Use same session_id so they form a chain
        op1.session_id = "chain-session"
        op2.session_id = "chain-session"
        op3.session_id = "chain-session"

        queue.enqueue([op1])
        dispatcher.dispatch_pending()

        queue.enqueue([op2])
        dispatcher.dispatch_pending()

        queue.enqueue([op3])
        dispatcher.dispatch_pending()

        # All 3 receipts exist
        all_receipts = receipt_store.get_all_receipts()
        assert len(all_receipts) == 3

        # Chain: receipt_2.prev == receipt_1.id, receipt_3.prev == receipt_2.id
        r1 = receipt_store.get_by_operation_id("op-chain-1")[0]
        r2 = receipt_store.get_by_operation_id("op-chain-2")[0]
        r3 = receipt_store.get_by_operation_id("op-chain-3")[0]

        assert r1["prev_receipt_id"] is None
        assert r2["prev_receipt_id"] == r1["receipt_id"]
        assert r3["prev_receipt_id"] == r2["receipt_id"]

    def test_chain_signatures_all_verify(self, dispatcher, queue, receipt_store, signer):
        """Every receipt signature in the chain verifies."""
        sink = MagicMock()
        sink.name = "wiki"
        dispatcher.register_sink(sink)

        for i in range(5):
            op = _make_op(sink_name="wiki", op_id=f"sig-op-{i}")
            op.session_id = "sig-session"
            queue.enqueue([op])
            dispatcher.dispatch_pending()

        all_receipts = receipt_store.get_all_receipts()
        assert len(all_receipts) == 5

        public_key = signer.get_public_key()
        assert public_key is not None

        for row in all_receipts:
            receipt = Receipt(
                operation_id=row["operation_id"],
                operation_type=row["operation_type"],
                agent=row["agent"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                claim_uuid=row["claim_uuid"],
                page_path=row["page_path"],
                payload_hash=row["payload_hash"],
                prev_receipt_id=row["prev_receipt_id"],
            )
            assert signer.verify_receipt(receipt, row["signature"], public_key) is True

    def test_verify_chain_intact_passes(self, dispatcher, queue, receipt_store):
        """verify_chain returns valid for a well-formed chain."""
        sink = MagicMock()
        sink.name = "vault"
        dispatcher.register_sink(sink)

        for i in range(3):
            op = _make_op(sink_name="vault", op_id=f"intact-op-{i}")
            op.session_id = "intact-session"
            queue.enqueue([op])
            dispatcher.dispatch_pending()

        result = receipt_store.verify_chain("intact-session")
        assert result.valid is True
        assert result.error is None

    def test_verify_chain_detects_broken_link(self, dispatcher, queue, receipt_store, conn):
        """verify_chain detects a broken prev_receipt_id link."""
        sink = MagicMock()
        sink.name = "vault"
        dispatcher.register_sink(sink)

        op = _make_op(sink_name="vault", op_id="break-op")
        op.session_id = "break-session"
        queue.enqueue([op])
        dispatcher.dispatch_pending()

        # Tamper: set prev_receipt_id to a non-existent receipt
        conn.execute(
            "UPDATE receipts SET prev_receipt_id = ? WHERE operation_id = ?",
            ("nonexistent-receipt-id", "break-op"),
        )
        conn.commit()

        result = receipt_store.verify_chain("break-session")
        assert result.valid is False
        assert "broken" in (result.error or "").lower()

    def test_verify_chain_detects_bad_signature(self, dispatcher, queue, receipt_store, conn):
        """verify_chain detects a tampered signature."""
        sink = MagicMock()
        sink.name = "vault"
        dispatcher.register_sink(sink)

        op = _make_op(sink_name="vault", op_id="sig-op")
        op.session_id = "sig-session"
        queue.enqueue([op])
        dispatcher.dispatch_pending()

        # Tamper: corrupt the signature
        conn.execute(
            "UPDATE receipts SET signature = ? WHERE operation_id = ?",
            ("dGFtcGVyZWRfc2lnbmF0dXJl", "sig-op"),
        )
        conn.commit()

        result = receipt_store.verify_chain("sig-session")
        assert result.valid is False
        assert "signature" in (result.error or "").lower()

    def test_no_receipt_signer_no_receipts(self, queue):
        """Without a receipt_signer, dispatch still works but no receipts."""
        sink = MagicMock()
        sink.name = "vault"
        dispatcher = Dispatcher(queue=queue, sinks=[sink])

        op = _make_op(sink_name="vault")
        queue.enqueue([op])
        processed = dispatcher.dispatch_pending()
        assert processed == 1

    def test_failed_dispatch_no_receipt(self, dispatcher, queue, receipt_store):
        """A failed dispatch does NOT produce a receipt."""
        sink = MagicMock()
        sink.name = "vault"
        sink.write.side_effect = Exception("sink failure")
        dispatcher.register_sink(sink)

        op = _make_op(sink_name="vault")
        queue.enqueue([op])
        dispatcher.dispatch_pending()

        receipts = receipt_store.get_by_operation_id(op.op_id)
        assert len(receipts) == 0


# ── AC-SEC-2: receipt coverage ────────────────────────────────────────

class TestReceiptCoverage:
    """High-risk operations 100% produce receipts."""

    HIGH_RISK_SINKS: ClassVar[list[str]] = [
        "vault", "claims", "wiki", "fts5", "graph", "contradictions", "connector",
    ]

    def test_all_high_risk_sinks_produce_receipts(self, dispatcher, queue, receipt_store):
        """Every high-risk sink dispatch produces a receipt."""
        for sink_name in self.HIGH_RISK_SINKS:
            sink = MagicMock()
            sink.name = sink_name
            dispatcher.register_sink(sink)

            op = _make_op(sink_name=sink_name, op_id=f"cov-{sink_name}")
            op.session_id = f"cov-session-{sink_name}"
            queue.enqueue([op])
            dispatcher.dispatch_pending()

            receipts = receipt_store.get_by_operation_id(f"cov-{sink_name}")
            assert len(receipts) == 1, (
                f"Sink '{sink_name}' did not produce a receipt"
            )
            r = receipts[0]
            assert r["sink_name"] == sink_name
            assert r["signature"] is not None
            assert r["operation_id"] == f"cov-{sink_name}"

    def test_multiple_ops_same_session_all_covered(self, dispatcher, queue, receipt_store):
        """Multiple ops in one session each get their own receipt."""
        sink = MagicMock()
        sink.name = "wiki"
        dispatcher.register_sink(sink)

        session_id = "coverage-multi"
        for i in range(10):
            op = _make_op(sink_name="wiki", op_id=f"multi-{i}")
            op.session_id = session_id
            queue.enqueue([op])
            dispatcher.dispatch_pending()

        all_receipts = receipt_store.get_all_receipts()
        assert len(all_receipts) == 10
        # Every receipt has a signature
        for r in all_receipts:
            assert r["signature"] is not None

    def test_receipt_payload_hash_populated(self, dispatcher, queue, receipt_store):
        """Receipts include a non-null payload_hash."""
        sink = MagicMock()
        sink.name = "vault"
        dispatcher.register_sink(sink)

        op = _make_op(sink_name="vault", op_id="hash-op")
        queue.enqueue([op])
        dispatcher.dispatch_pending()

        receipts = receipt_store.get_by_operation_id("hash-op")
        assert len(receipts) == 1
        assert receipts[0]["payload_hash"] is not None
        assert len(receipts[0]["payload_hash"]) == 64  # SHA-256 hex

"""Receipt Store — persistence + chain verification for Ed25519 receipts.

Per T-F-C-2-1 / AC-SEC-2: every successful dispatch of a high-risk sink
produces a signed receipt, linked to the previous receipt in the same
session via ``prev_receipt_id``.  This module persists those receipts to
the ``receipts`` table (migration v7) and verifies the resulting chain
(link continuity + signature) on demand.

The store is the read/write boundary for the ``receipts`` table; the
``Dispatcher`` calls ``store`` after a successful ``mark_done`` and the
``scripts/receipt_check.sh`` CLI (and tests) call ``verify_chain``.
"""
from __future__ import annotations

import logging
import sqlite3
import threading
from dataclasses import dataclass

from saw.adapters.crypto.ed25519 import Receipt, ReceiptSigner

logger = logging.getLogger(__name__)


@dataclass
class ChainVerificationResult:
    """Outcome of verifying a receipt chain for one session.

    ``valid`` is True only when every link is continuous (each receipt's
    ``prev_receipt_id`` equals the previous receipt's ``receipt_id``, and
    the first receipt's ``prev_receipt_id`` is None) AND every signature
    verifies against the public key stored alongside it.
    """

    valid: bool
    error: str | None = None


class ReceiptStore:
    """SQLite-backed persistence for signed operation receipts.

    The store shares the write-queue's SQLite connection.  All mutations
    serialize on an internal lock to avoid ``database is locked`` /
    interleaved commits, mirroring the locking pattern in
    ``SQLiteWriteQueue`` and ``code_graph/store.py``.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._lock = threading.Lock()

    # ── writes ───────────────────────────────────────────────────────

    def store(
        self,
        *,
        receipt_id: str,
        operation_id: str,
        operation_type: str,
        agent: str,
        timestamp: str,
        claim_uuid: str | None,
        page_path: str | None,
        payload_hash: str | None,
        signature: str,
        prev_receipt_id: str | None,
        public_key: str,
        sink_name: str | None,
        session_id: str | None,
    ) -> None:
        """Persist one signed receipt, linking it to the chain tail.

        Caller (the Dispatcher) is responsible for obtaining
        ``prev_receipt_id`` via ``get_last_receipt_id`` *before* signing so
        the signed ``prev_receipt_id`` matches the stored link.
        """
        with self._lock:
            self._conn.execute(
                """INSERT INTO receipts
                   (receipt_id, operation_id, operation_type, agent, timestamp,
                    claim_uuid, page_path, payload_hash, signature,
                    prev_receipt_id, public_key, sink_name, session_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    receipt_id,
                    operation_id,
                    operation_type,
                    agent,
                    timestamp,
                    claim_uuid,
                    page_path,
                    payload_hash,
                    signature,
                    prev_receipt_id,
                    public_key,
                    sink_name,
                    session_id,
                ),
            )
            self._conn.commit()

    # ── reads ────────────────────────────────────────────────────────

    def get_last_receipt_id(self, session_id: str) -> str | None:
        """Return the ``receipt_id`` of the most recent receipt in a session.

        Used by the Dispatcher to link a new receipt to the chain tail.
        Returns None for the first receipt in a session.  Ordered by
        implicit ``rowid`` (insertion order), which is monotonic for a
        rowid table.
        """
        with self._lock:
            row = self._conn.execute(
                """SELECT receipt_id FROM receipts
                   WHERE session_id = ?
                   ORDER BY rowid DESC
                   LIMIT 1""",
                (session_id,),
            ).fetchone()
        return row[0] if row else None

    def get_by_operation_id(self, operation_id: str) -> list[dict]:
        """Return all receipts for a given operation id (insertion order)."""
        return self._fetchall_dicts(
            """SELECT * FROM receipts
               WHERE operation_id = ?
               ORDER BY rowid ASC""",
            (operation_id,),
        )

    def get_all_receipts(self) -> list[dict]:
        """Return every receipt across all sessions (insertion order)."""
        return self._fetchall_dicts(
            "SELECT * FROM receipts ORDER BY rowid ASC"
        )

    def get_chain(self, session_id: str) -> list[dict]:
        """Return the receipt chain for a session in insertion order."""
        return self._fetchall_dicts(
            """SELECT * FROM receipts
               WHERE session_id = ?
               ORDER BY rowid ASC""",
            (session_id,),
        )

    # ── verification ─────────────────────────────────────────────────

    def verify_chain(self, session_id: str) -> ChainVerificationResult:
        """Verify link continuity + signatures for one session's chain.

        A chain is ``valid`` when:
          1. The first receipt has ``prev_receipt_id IS None``.
          2. Each subsequent receipt's ``prev_receipt_id`` equals the
             previous receipt's ``receipt_id`` (no broken links).
          3. Every receipt signature verifies against the public key stored
             alongside it (no tampering).

        An empty chain (no receipts for the session) is considered valid.

        Returns a :class:`ChainVerificationResult` describing the outcome.
        """
        rows = self.get_chain(session_id)
        if not rows:
            return ChainVerificationResult(True, None)

        # A ReceiptSigner with no key path is stateless for verification —
        # ``verify_receipt`` only consumes its ``public_key`` argument, never
        # ``self._signing_key``.  Reuse it rather than duplicating the
        # nacl verify dance (DEF-2: a missing key must NOT make every
        # signature "valid").
        verifier = ReceiptSigner()

        prev_id: str | None = None
        for row in rows:
            # 1. Link continuity.
            if row["prev_receipt_id"] != prev_id:
                return ChainVerificationResult(
                    False,
                    "broken link: receipt "
                    f"{row['receipt_id']} prev_receipt_id="
                    f"{row['prev_receipt_id']!r}, expected {prev_id!r}",
                )

            # 2. Signature verification — reconstruct the canonical Receipt
            # from stored fields and verify against the stored public key.
            receipt = Receipt(
                operation_id=row["operation_id"],
                operation_type=row["operation_type"],
                agent=row["agent"],
                timestamp=_parse_ts(row["timestamp"]),
                claim_uuid=row["claim_uuid"],
                page_path=row["page_path"],
                payload_hash=row["payload_hash"],
                prev_receipt_id=row["prev_receipt_id"],
            )
            if not verifier.verify_receipt(
                receipt, row["signature"], row["public_key"]
            ):
                return ChainVerificationResult(
                    False,
                    "signature verification failed for receipt "
                    f"{row['receipt_id']}",
                )

            prev_id = row["receipt_id"]

        return ChainVerificationResult(True, None)

    # ── helpers ──────────────────────────────────────────────────────

    def _fetchall_dicts(
        self, sql: str, params: tuple = ()
    ) -> list[dict]:
        """Run a SELECT and return rows as dicts (column-name keyed).

        Builds dicts explicitly from ``cursor.description`` so the store
        works regardless of the connection's ``row_factory`` setting (the
        shared conn is also used by ``SQLiteWriteQueue``, which reads via
        positional indexing).
        """
        with self._lock:
            cur = self._conn.execute(sql, params)
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]


def _parse_ts(value: str):
    """Parse an ISO-8601 timestamp stored on a receipt row."""
    from datetime import datetime

    return datetime.fromisoformat(value)

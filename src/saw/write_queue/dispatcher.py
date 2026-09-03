"""Write Queue Dispatcher - parallel sink dispatch with retry and crash recovery.

Per Pitfall 7: idempotent sinks, per-sink tracking, crash recovery resets
PROCESSING ops to PENDING for safe re-dispatch.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from saw.adapters.crypto.ed25519 import Receipt, ReceiptSigner
from saw.write_queue.queue import SQLiteWriteQueue, WriteOp
from saw.write_queue.receipt_store import ReceiptStore

logger = logging.getLogger(__name__)


class Dispatcher:
    """Parallel sink dispatcher with retry and dead letter handling.

    Coordinates dispatching WriteOps to the appropriate Sink implementations.
    Supports exponential backoff via ``next_retry_at`` on each WriteOp and
    promotes exhausted ops to the dead-letter queue automatically (handled
    inside ``SQLiteWriteQueue.mark_failed``).
    """

    def __init__(
        self,
        queue: SQLiteWriteQueue,
        sinks: list | None = None,
        event_bus=None,
        receipt_signer: ReceiptSigner | None = None,
        receipt_store: ReceiptStore | None = None,
    ) -> None:
        self._queue = queue
        self._sinks: dict[str, object] = {}
        self._event_bus = event_bus
        # T-F-C-2-1 / AC-SEC-2: optional Ed25519 receipt production.  When
        # both a signer and a store are attached, every successful dispatch
        # produces a signed receipt linked into the session's chain.  Either
        # missing → dispatch proceeds without receipts (graceful, no
        # behavior change for callers that opted out).
        self._receipt_signer = receipt_signer
        self._receipt_store = receipt_store
        if sinks:
            for sink in sinks:
                self.register_sink(sink)

    def register_sink(self, sink) -> None:
        """Register a sink by its name."""
        self._sinks[sink.name] = sink

    def dispatch_pending(self) -> int:
        """Dispatch all pending operations to their matching sinks.

        Ops whose ``next_retry_at`` is still in the future are skipped
        (exponential backoff).  Ops that exhaust their retries are
        automatically moved to the dead-letter queue by
        ``SQLiteWriteQueue.mark_failed``.

        Returns:
            Number of operations successfully processed.
        """
        pending = self._queue.get_pending()
        processed = 0
        now = datetime.now(timezone.utc)

        for op in pending:
            # Belt-and-suspenders: skip ops whose backoff hasn't elapsed yet.
            # The SQL query in get_pending() already filters these, but an
            # explicit check guards against clock skew or stale caches.
            if op.next_retry_at is not None and op.next_retry_at > now:
                logger.debug(
                    "Skipping op %s — next_retry_at %s is in the future",
                    op.op_id, op.next_retry_at.isoformat(),
                )
                continue

            sink = self._sinks.get(op.sink_name)
            if sink is None:
                # F-DB-02: an op with no registered sink would otherwise stay
                # 'pending' forever (re-fetched every dispatch cycle). Claim
                # it and mark_failed so it progresses toward the dead-letter
                # queue and an operator can see it instead of looping silently.
                logger.warning(
                    "No sink registered for: %s (op %s)", op.sink_name, op.op_id
                )
                if self._queue.mark_processing(op.op_id):
                    err = f"No sink registered for '{op.sink_name}'"
                    self._queue.track_sink(op.op_id, op.sink_name, "failed", err)
                    self._queue.mark_failed(op.op_id, err)
                continue

            if not self._queue.mark_processing(op.op_id):
                # CAS guard (HI-6): another dispatcher already claimed this op.
                continue
            try:
                sink.write(op)
                self._queue.track_sink(op.op_id, op.sink_name, "done")
                self._queue.mark_done(op.op_id)
                processed += 1
                # T-F-C-2-1 / AC-SEC-2: produce a signed receipt for the
                # successful dispatch, linked into the session's chain.
                # Best-effort — a receipt failure must not regress the
                # dispatch (the write already committed).
                self._produce_receipt(op)
                # F-QS-07: invalidate the query cache on content writes so
                # search results don't go stale (best-effort).
                if op.sink_name in ("wiki", "claims", "fts5"):
                    try:
                        from saw.engines.query.cache import get_cache

                        get_cache().clear()
                    except Exception:
                        pass
                # HI-2: emit a write event so the WebSocket broadcaster and
                # plugins are notified. publish_nowait is sync (the dispatcher
                # is not async) and safe — it fans out via queue.put_nowait.
                if self._event_bus is not None:
                    self._event_bus.publish_nowait({
                        "type": "PageUpdated" if op.sink_name == "wiki" else "WriteCompleted",
                        "sink": op.sink_name,
                        "op_id": op.op_id,
                        **(op.payload or {}),
                    })
            except Exception as e:
                error_msg = str(e)
                logger.error(
                    "Sink %s failed for op %s: %s",
                    op.sink_name, op.op_id, error_msg,
                )
                self._queue.track_sink(
                    op.op_id, op.sink_name, "failed", error_msg
                )
                # mark_failed handles exponential backoff scheduling and
                # promotes the op to 'dead_letter' when retries are exhausted.
                self._queue.mark_failed(op.op_id, error_msg)

                if op.retry_count + 1 >= op.max_retries:
                    logger.warning(
                        "Op %s exhausted retries (%d/%d) — moved to dead_letter queue",
                        op.op_id, op.retry_count + 1, op.max_retries,
                    )

        return processed

    def _produce_receipt(self, op: WriteOp) -> None:
        """Produce and persist a signed receipt for a successful dispatch.

        Links the receipt to the previous one in the same session via
        ``prev_receipt_id`` (queried from the store before signing so the
        signed field matches the stored link).  No-op when no signer or
        store is attached.  All errors are logged and swallowed — the
        write already committed, so a receipt failure is a degraded audit
        trail, not a failed dispatch.
        """
        if not self._receipt_signer or not self._receipt_store:
            return

        public_key = self._receipt_signer.get_public_key()
        if public_key is None:
            logger.warning(
                "Cannot produce receipt for op %s — signer has no public "
                "key. Call generate_keypair() / load a key first.",
                op.op_id,
            )
            return

        try:
            payload = op.payload if isinstance(op.payload, dict) else {}
            payload_hash = self._receipt_signer.compute_payload_hash(payload)
            prev_receipt_id = self._receipt_store.get_last_receipt_id(
                op.session_id
            )

            receipt = Receipt(
                operation_id=op.op_id,
                operation_type="write",
                agent="Dispatcher",
                timestamp=datetime.now(timezone.utc),
                claim_uuid=payload.get("claim_uuid"),
                page_path=payload.get("page_path"),
                payload_hash=payload_hash,
                prev_receipt_id=prev_receipt_id,
            )
            signature = self._receipt_signer.sign_receipt(receipt)

            self._receipt_store.store(
                receipt_id=str(uuid.uuid4()),
                operation_id=receipt.operation_id,
                operation_type=receipt.operation_type,
                agent=receipt.agent,
                timestamp=receipt.timestamp.isoformat(),
                claim_uuid=receipt.claim_uuid,
                page_path=receipt.page_path,
                payload_hash=receipt.payload_hash,
                signature=signature,
                prev_receipt_id=receipt.prev_receipt_id,
                public_key=public_key,
                sink_name=op.sink_name,
                session_id=op.session_id,
            )
        except Exception as e:  # noqa: BLE001
            # Best-effort audit trail; never regress a committed dispatch.
            logger.error(
                "Failed to produce receipt for op %s: %s", op.op_id, e
            )

    def recover(self) -> int:
        """Crash recovery: reset PROCESSING ops back to PENDING.

        Per Pitfall 7: sinks are idempotent (op_id dedup) so re-dispatch is safe.

        Returns:
            Number of operations recovered.
        """
        conn = self._queue._conn
        now = datetime.now(timezone.utc).isoformat()
        with self._queue._lock:
            cursor = conn.execute(
                """UPDATE write_outbox
                   SET status = 'pending', updated_at = ?
                   WHERE status = 'processing'""",
                (now,),
            )
            rowcount = cursor.rowcount
            if rowcount > 0:
                conn.commit()
                logger.info("Recovered %d PROCESSING ops to PENDING", rowcount)
        return rowcount

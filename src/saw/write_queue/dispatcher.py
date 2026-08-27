"""Write Queue Dispatcher - parallel sink dispatch with retry and crash recovery.

Per Pitfall 7: idempotent sinks, per-sink tracking, crash recovery resets
PROCESSING ops to PENDING for safe re-dispatch.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from saw.write_queue.queue import SQLiteWriteQueue, WriteOp

logger = logging.getLogger(__name__)


class Dispatcher:
    """Parallel sink dispatcher with retry and dead letter handling.

    Coordinates dispatching WriteOps to the appropriate Sink implementations.
    Supports exponential backoff via ``next_retry_at`` on each WriteOp and
    promotes exhausted ops to the dead-letter queue automatically (handled
    inside ``SQLiteWriteQueue.mark_failed``).
    """

    def __init__(self, queue: SQLiteWriteQueue, sinks: list | None = None, event_bus=None) -> None:
        self._queue = queue
        self._sinks: dict[str, object] = {}
        self._event_bus = event_bus
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
                logger.warning("No sink registered for: %s", op.sink_name)
                continue

            if not self._queue.mark_processing(op.op_id):
                # CAS guard (HI-6): another dispatcher already claimed this op.
                continue
            try:
                sink.write(op)
                self._queue.track_sink(op.op_id, op.sink_name, "done")
                self._queue.mark_done(op.op_id)
                processed += 1
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

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
    """

    def __init__(self, queue: SQLiteWriteQueue, sinks: list | None = None) -> None:
        self._queue = queue
        self._sinks: dict[str, object] = {}
        if sinks:
            for sink in sinks:
                self.register_sink(sink)

    def register_sink(self, sink) -> None:
        """Register a sink by its name."""
        self._sinks[sink.name] = sink

    def dispatch_pending(self) -> int:
        """Dispatch all pending operations to their matching sinks.

        Returns:
            Number of operations processed.
        """
        pending = self._queue.get_pending()
        processed = 0

        for op in pending:
            sink = self._sinks.get(op.sink_name)
            if sink is None:
                logger.warning("No sink registered for: %s", op.sink_name)
                continue

            self._queue.mark_processing(op.op_id)
            try:
                sink.write(op)
                self._queue.track_sink(op.op_id, op.sink_name, "done")
                self._queue.mark_done(op.op_id)
                processed += 1
            except Exception as e:
                error_msg = str(e)
                logger.error(
                    "Sink %s failed for op %s: %s",
                    op.sink_name, op.op_id, error_msg,
                )
                self._queue.track_sink(
                    op.op_id, op.sink_name, "failed", error_msg
                )
                self._queue.mark_failed(op.op_id, error_msg)
                # If retry_count < max_retries, status is 'failed' and will be
                # picked up again by get_pending() on next dispatch cycle

        return processed

    def recover(self) -> int:
        """Crash recovery: reset PROCESSING ops back to PENDING.

        Per Pitfall 7: sinks are idempotent (op_id dedup) so re-dispatch is safe.

        Returns:
            Number of operations recovered.
        """
        conn = self._queue._conn
        now = datetime.now(timezone.utc).isoformat()
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

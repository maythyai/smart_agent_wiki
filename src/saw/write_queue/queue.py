"""Write Queue - SQLite-backed outbox with atomic enqueue and per-sink tracking.

Per D-04: Single durable entry point, parallel distribution, per-sink tracking.
Per Pitfall 7: op_id deduplication, idempotent sinks, per-sink state tracking.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone

from saw.domain.exceptions import WriteQueueError
from saw.domain.value_objects import WriteOpStatus


@dataclass
class WriteOp:
    """A single write operation in the outbox queue."""
    op_id: str
    session_id: str
    sink_name: str
    payload: dict = field(default_factory=dict)
    status: WriteOpStatus = WriteOpStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = None
    next_retry_at: datetime | None = None


# Outbox table DDL
OUTBOX_DDL = """
CREATE TABLE IF NOT EXISTS write_outbox (
    op_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    sink_name TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    next_retry_at TEXT,
    UNIQUE(op_id)
);

-- Per-sink completion tracking (per Pitfall 7 recommendation 1)
CREATE TABLE IF NOT EXISTS sink_tracking (
    op_id TEXT NOT NULL,
    sink_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    completed_at TEXT,
    error_message TEXT,
    PRIMARY KEY (op_id, sink_name)
);

CREATE INDEX IF NOT EXISTS idx_outbox_status ON write_outbox(status);
CREATE INDEX IF NOT EXISTS idx_outbox_session ON write_outbox(session_id);
"""


class SQLiteWriteQueue:
    """SQLite-backed Write Queue with atomic enqueue and per-sink tracking.

    Implements the WriteQueue protocol.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._create_tables()

    def _create_tables(self) -> None:
        """Ensure outbox tables exist (delegates to the migration framework).

        C4: the outbox tables are part of the claims DB schema, managed by
        ``saw.db.migrations.apply_migrations``. The previous ad-hoc
        ``ALTER TABLE write_outbox ADD COLUMN next_retry_at`` is now
        migration v2.
        """
        try:
            from saw.db.migrations import apply_migrations

            apply_migrations(self._conn)
        except sqlite3.Error as e:
            raise WriteQueueError(f"Failed to apply DB migrations: {e}") from e

    def enqueue(self, ops: list[WriteOp]) -> None:
        """Atomically enqueue all operations. All-or-nothing."""
        try:
            with self._conn:
                for op in ops:
                    self._conn.execute(
                        """INSERT INTO write_outbox
                           (op_id, session_id, sink_name, payload, status,
                            retry_count, max_retries, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            op.op_id,
                            op.session_id,
                            op.sink_name,
                            json.dumps(op.payload),
                            op.status.name.lower(),
                            op.retry_count,
                            op.max_retries,
                            op.created_at.isoformat(),
                        ),
                    )
        except sqlite3.IntegrityError as e:
            raise WriteQueueError(f"Duplicate op_id in enqueue: {e}") from e
        except sqlite3.Error as e:
            raise WriteQueueError(f"Failed to enqueue operations: {e}") from e

    def enqueue_atomic(self, ops: list[WriteOp]) -> None:
        """Enqueue then immediately dispatch to sinks."""
        self.enqueue(ops)
        # Dispatcher is set externally; caller should invoke dispatch_pending
        # after enqueue_atomic. This method exists for the protocol contract.

    def get_pending(self) -> list[WriteOp]:
        """Get pending and retryable operations.

        Skips ops whose ``next_retry_at`` timestamp is in the future
        (exponential backoff).  Also excludes ops that have exhausted
        their retries (moved to ``dead_letter``).
        """
        now = datetime.now(timezone.utc).isoformat()
        rows = self._conn.execute(
            """SELECT op_id, session_id, sink_name, payload, status,
                      retry_count, max_retries, error_message, created_at,
                      updated_at, next_retry_at
               FROM write_outbox
               WHERE status IN ('pending', 'failed')
                 AND retry_count < max_retries
                 AND (next_retry_at IS NULL OR next_retry_at <= ?)
               ORDER BY created_at ASC""",
            (now,),
        ).fetchall()
        return [self._row_to_op(row) for row in rows]

    def mark_processing(self, op_id: str) -> None:
        """Mark an operation as processing."""
        self._conn.execute(
            """UPDATE write_outbox
               SET status = 'processing', updated_at = ?
               WHERE op_id = ?""",
            (datetime.now(timezone.utc).isoformat(), op_id),
        )
        self._conn.commit()

    def mark_done(self, op_id: str) -> None:
        """Mark an operation as done."""
        self._conn.execute(
            """UPDATE write_outbox
               SET status = 'done', updated_at = ?
               WHERE op_id = ?""",
            (datetime.now(timezone.utc).isoformat(), op_id),
        )
        self._conn.commit()

    def mark_failed(self, op_id: str, error: str) -> None:
        """Mark an operation as failed, apply exponential backoff, or move to dead letter.

        Increments ``retry_count`` and sets ``next_retry_at`` to
        ``now + 2^retry_count`` seconds.  When ``retry_count >= max_retries``
        the op is moved to ``dead_letter`` status instead of remaining
        ``failed`` indefinitely.
        """
        now = datetime.now(timezone.utc)
        # Read current retry_count and max_retries
        row = self._conn.execute(
            "SELECT retry_count, max_retries FROM write_outbox WHERE op_id = ?",
            (op_id,),
        ).fetchone()
        if row is None:
            return

        current_retry = row[0]
        max_retries = row[1]
        new_retry_count = current_retry + 1

        if new_retry_count >= max_retries:
            # Exhausted retries — move to dead letter queue
            self._conn.execute(
                """UPDATE write_outbox
                   SET status = 'dead_letter',
                       retry_count = ?,
                       error_message = ?,
                       updated_at = ?,
                       next_retry_at = NULL
                   WHERE op_id = ?""",
                (new_retry_count, error, now.isoformat(), op_id),
            )
        else:
            # Schedule next retry with exponential backoff.
            # First failure (new_retry_count == 1) is NOT delayed so the
            # dispatcher can retry immediately — this avoids a dead window
            # where the op is 'failed' but not yet visible to get_pending.
            # Subsequent failures get 2^retry_count seconds of backoff.
            from datetime import timedelta

            next_retry_at = None
            if new_retry_count > 1:
                next_retry_at = (now + timedelta(seconds=2 ** new_retry_count)).isoformat()
            self._conn.execute(
                """UPDATE write_outbox
                   SET status = 'failed',
                       retry_count = ?,
                       error_message = ?,
                       updated_at = ?,
                       next_retry_at = ?
                   WHERE op_id = ?""",
                (new_retry_count, error, now.isoformat(), next_retry_at, op_id),
            )
        self._conn.commit()

    def track_sink(self, op_id: str, sink_name: str, status: str,
                   error: str | None = None) -> None:
        """Record per-sink completion status."""
        completed_at = datetime.now(timezone.utc).isoformat() if status == "done" else None
        self._conn.execute(
            """INSERT INTO sink_tracking (op_id, sink_name, status, completed_at, error_message)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(op_id, sink_name)
               DO UPDATE SET status=excluded.status,
                             completed_at=excluded.completed_at,
                             error_message=excluded.error_message""",
            (op_id, sink_name, status, completed_at, error),
        )
        self._conn.commit()

    def get_sink_status(self, op_id: str) -> dict[str, str]:
        """Return per-sink completion status for an operation."""
        rows = self._conn.execute(
            "SELECT sink_name, status FROM sink_tracking WHERE op_id = ?",
            (op_id,),
        ).fetchall()
        return {row[0]: row[1] for row in rows}

    @staticmethod
    def _row_to_op(row) -> WriteOp:
        """Convert a database row to a WriteOp dataclass."""
        next_retry_at = None
        if len(row) > 10 and row[10]:
            next_retry_at = datetime.fromisoformat(row[10])
        return WriteOp(
            op_id=row[0],
            session_id=row[1],
            sink_name=row[2],
            payload=json.loads(row[3]),
            status=WriteOpStatus[row[4].upper()],
            retry_count=row[5],
            max_retries=row[6],
            error_message=row[7],
            created_at=datetime.fromisoformat(row[8]),
            updated_at=datetime.fromisoformat(row[9]) if row[9] else None,
            next_retry_at=next_retry_at,
        )

    def get_dead_letter(self) -> list[WriteOp]:
        """Return all operations that have been moved to the dead letter queue.

        These are ops whose ``retry_count >= max_retries`` and have been
        permanently parked for manual inspection or retry.
        """
        rows = self._conn.execute(
            """SELECT op_id, session_id, sink_name, payload, status,
                      retry_count, max_retries, error_message, created_at,
                      updated_at, next_retry_at
               FROM write_outbox
               WHERE status = 'dead_letter'
               ORDER BY created_at ASC"""
        ).fetchall()
        return [self._row_to_op(row) for row in rows]

    def retry_dead_letter(self, op_id: str) -> None:
        """Reset a dead-letter op so it can be retried from scratch.

        Sets ``retry_count`` back to 0, clears ``next_retry_at``, and
        restores status to ``pending``.

        Raises:
            WriteQueueError: If the op_id is not found or is not in dead_letter status.
        """
        now = datetime.now(timezone.utc).isoformat()
        cursor = self._conn.execute(
            """UPDATE write_outbox
               SET status = 'pending',
                   retry_count = 0,
                   error_message = NULL,
                   updated_at = ?,
                   next_retry_at = NULL
               WHERE op_id = ?
                 AND status = 'dead_letter'""",
            (now, op_id),
        )
        self._conn.commit()
        if cursor.rowcount == 0:
            raise WriteQueueError(
                f"Op {op_id} not found in dead_letter queue"
            )

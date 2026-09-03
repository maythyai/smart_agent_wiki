"""PRAGMA user_version-based migration framework.

Every SQLite database used by SAW (claims DB, plus the outbox tables that
live in the same file) registers its schema version via ``PRAGMA
user_version``.  On startup, ``apply_migrations(conn)`` runs any
unapplied migrations in order, within a single transaction, and bumps the
version.

This replaces the previous ad-hoc ``ALTER TABLE`` try/except spots and
``CREATE TABLE IF NOT EXISTS`` scatter that silently ignored schema
changes on existing databases (the C4 audit finding).

**Usage:**

    conn = sqlite3.connect(db_path)
    apply_migrations(conn)

All callers — ``SQLiteClaimsRepository._init_schema``,
``SQLiteWriteQueue._create_tables``, ``saw init`` — delegate to this
single entry point.
"""
from __future__ import annotations

import logging
import sqlite3
from typing import Callable

logger = logging.getLogger(__name__)

# ── Migration registry ────────────────────────────────────────────────
# Each entry is (version_number, ddl_or_callable).
# Every migration MUST be idempotent (use IF NOT EXISTS, IF DOES NOT EXIST,
# or guard with a column-existence check).
#
# When adding a new migration:
#   1. Append a tuple (next_version, ddl) at the END of the list.
#   2. Document the change in the C4 migration log comment.
#   3. The version integer is the target ``user_version`` AFTER the
#      migration is applied.
#      E.g. version 1 is the initial baseline, version 2 adds column X, etc.

_MIGRATIONS: list[tuple[int, str | Callable[[sqlite3.Connection], None]]] = []


def _register(version: int, ddl: str | Callable[[sqlite3.Connection], None]) -> None:
    _MIGRATIONS.append((version, ddl))


# v1: baseline schema — claims, entities, relations, FTS5, outbox, contradictions.
# Every ``CREATE TABLE`` uses IF NOT EXISTS so the migration is idempotent
# when run on a fresh DB (v0 → v1) or re-run on an existing one.

_register(
    1,
    """CREATE TABLE IF NOT EXISTS claim (
    uuid TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    source_uuid TEXT NOT NULL,
    page_number INTEGER,
    line_number INTEGER,
    timestamp TEXT,
    confidence TEXT NOT NULL DEFAULT 'unverified',
    source_mark TEXT NOT NULL DEFAULT 'extracted',
    tags TEXT NOT NULL DEFAULT '[]',
    entities TEXT NOT NULL DEFAULT '[]',
    content_hash TEXT NOT NULL,
    session_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS claim_relation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_claim_uuid TEXT NOT NULL,
    target_claim_uuid TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (source_claim_uuid) REFERENCES claim(uuid),
    FOREIGN KEY (target_claim_uuid) REFERENCES claim(uuid)
);

CREATE TABLE IF NOT EXISTS entity (
    uuid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    aliases TEXT NOT NULL DEFAULT '[]',
    entity_type TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS entity_relation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_uuid TEXT NOT NULL,
    target_uuid TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (source_uuid) REFERENCES entity(uuid),
    FOREIGN KEY (target_uuid) REFERENCES entity(uuid)
);

CREATE VIRTUAL TABLE IF NOT EXISTS fts_index
USING fts5(
    title,
    content,
    tags,
    original UNINDEXED,
    tokenize='unicode61',
    detail=column
);

-- Partial indexes
CREATE INDEX IF NOT EXISTS idx_claim_source ON claim(source_uuid) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_claim_confidence ON claim(confidence) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_claim_hash ON claim(content_hash) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_entity_name ON entity(name);

-- Outbox tables
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

-- Contradictions table
CREATE TABLE IF NOT EXISTS contradictions (
    uuid TEXT PRIMARY KEY,
    claim_a_uuid TEXT NOT NULL,
    claim_b_uuid TEXT NOT NULL,
    contradiction_type TEXT NOT NULL,
    resolution TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    resolved_at TEXT,
    blast_radius TEXT
);
""",
)

# v2: add next_retry_at column to write_outbox (previously an ad-hoc ALTER TABLE
# in queue.py:84-89). Guarded by a column-existence check so the migration is
# idempotent — re-running it on an already-upgraded DB is a no-op.
def _add_next_retry_at(conn: sqlite3.Connection) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(write_outbox)")}
    if "next_retry_at" not in cols:
        conn.execute("ALTER TABLE write_outbox ADD COLUMN next_retry_at TEXT")

_register(2, _add_next_retry_at)


# v3: add last_accessed column to claim. Enables FreshnessTracker.refresh_on_access
# (D-13) to persist access timestamps so freshness actually decreases on read.
# Previously refresh_on_access was a no-op ("Would update last_accessed to now()
# in production"). Idempotent via column-existence check.
def _add_last_accessed(conn: sqlite3.Connection) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(claim)")}
    if "last_accessed" not in cols:
        conn.execute("ALTER TABLE claim ADD COLUMN last_accessed TEXT")

_register(3, _add_last_accessed)

# v4: workflow_executions — durable per-run state for crash recovery (HI-9).
# Stores progress so a process killed mid-workflow leaves a stranded
# status='running' row that startup recovery can detect and mark, rather than
# silently losing the execution (and its audit trail).
def _create_workflow_executions(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS workflow_executions (
    workflow_id TEXT PRIMARY KEY,
    definition_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    steps_completed INTEGER NOT NULL DEFAULT 0,
    steps_total INTEGER NOT NULL DEFAULT 0,
    context_json TEXT,
    errors_json TEXT,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT,
    finished_at TEXT
)"""
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_workflow_exec_status "
        "ON workflow_executions(status)"
    )


_register(4, _create_workflow_executions)

# v5: FK / filter indexes for the graph tables (M-13). claim_relation,
# entity_relation, and contradictions had no indexes on their FK/filter
# columns, so govern blast-radius, contradiction listing, and graph
# traversal degraded to full table scans as the KB grew.
def _add_graph_fk_indexes(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
CREATE INDEX IF NOT EXISTS idx_claim_relation_source
    ON claim_relation(source_claim_uuid);
CREATE INDEX IF NOT EXISTS idx_claim_relation_target
    ON claim_relation(target_claim_uuid);
CREATE INDEX IF NOT EXISTS idx_entity_relation_source
    ON entity_relation(source_uuid);
CREATE INDEX IF NOT EXISTS idx_entity_relation_target
    ON entity_relation(target_uuid);
CREATE INDEX IF NOT EXISTS idx_contradictions_resolved
    ON contradictions(resolved_at);
CREATE INDEX IF NOT EXISTS idx_contradictions_claim_a
    ON contradictions(claim_a_uuid);
CREATE INDEX IF NOT EXISTS idx_contradictions_claim_b
    ON contradictions(claim_b_uuid);
"""
    )


_register(5, _add_graph_fk_indexes)

# v6: source_platform / source_id on claim — lets SyncEngine look up an
# existing claim for a connector item for conflict detection (F-CONN-04).
# Idempotent via column-existence checks.
def _add_connector_source_columns(conn: sqlite3.Connection) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(claim)")}
    if "source_platform" not in cols:
        conn.execute("ALTER TABLE claim ADD COLUMN source_platform TEXT")
    if "source_id" not in cols:
        conn.execute("ALTER TABLE claim ADD COLUMN source_id TEXT")


_register(6, _add_connector_source_columns)

# v7: receipts — Ed25519 signed receipt persistence for the write queue
# dispatch chain (T-F-C-2-1, AC-SEC-2).  Each row stores a Receipt produced
# by ``ReceiptSigner.sign_receipt`` after a successful sink dispatch, linked
# to the previous receipt in the same session via ``prev_receipt_id``.
# Idempotent via IF NOT EXISTS.
def _create_receipts_table(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """CREATE TABLE IF NOT EXISTS receipts (
    receipt_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    agent TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    claim_uuid TEXT,
    page_path TEXT,
    payload_hash TEXT,
    signature TEXT NOT NULL,
    prev_receipt_id TEXT,
    public_key TEXT NOT NULL,
    sink_name TEXT,
    session_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_receipts_operation ON receipts(operation_id);
CREATE INDEX IF NOT EXISTS idx_receipts_session ON receipts(session_id);
CREATE INDEX IF NOT EXISTS idx_receipts_prev ON receipts(prev_receipt_id);
"""
    )


_register(7, _create_receipts_table)

# ── Public API ────────────────────────────────────────────────────────

TARGET_VERSION = max(v for v, _ in _MIGRATIONS) if _MIGRATIONS else 1


def apply_migrations(conn: sqlite3.Connection) -> int:
    """Run all unapplied migrations in order and return the new version.

    Returns the database's ``user_version`` after migration.
    Raises ``sqlite3.Error`` if any migration fails.
    """
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    if current >= TARGET_VERSION:
        return current

    # Apply missing migrations inside a single transaction — if any
    # migration fails the whole batch is rolled back.
    try:
        with conn:
            for version, ddl_or_fn in _MIGRATIONS:
                if version <= current:
                    continue
                if callable(ddl_or_fn):
                    ddl_or_fn(conn)
                else:
                    conn.executescript(ddl_or_fn)
                conn.execute(f"PRAGMA user_version = {version}")
                current = version
                logger.info("Applied migration v%d", version)
    except sqlite3.Error as e:
        logger.error("Migration v%d failed: %s", current + 1, e)
        raise

    return current


def get_version(conn: sqlite3.Connection) -> int:
    """Return the current ``user_version`` (read-only)."""
    return conn.execute("PRAGMA user_version").fetchone()[0]
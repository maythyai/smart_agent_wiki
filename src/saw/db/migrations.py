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
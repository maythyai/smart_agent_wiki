"""Claims DB schema and SQLite repository implementation.

Per D-03: FTS5 with unicode61 tokenizer, detail=column, automerge=8.
Per Pitfall 7: INSERT OR IGNORE for idempotent writes.

CJK support: fts_index.content/tags store *tokenized* text (see
saw.adapters.storage.fts_tokenize) so Chinese content is searchable;
the pre-tokenization text is kept in the UNINDEXED ``original`` column
for display purposes.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

from saw.adapters.storage.fts_tokenize import build_match_query, tokenize_for_fts
from saw.domain.claims import Claim
from saw.domain.exceptions import ClaimsDBError
from saw.domain.value_objects import ConfidenceLevel, SourceMark

logger = logging.getLogger(__name__)

# FTS5 virtual table (per D-03). ``original`` is UNINDEXED: it stores the
# pre-tokenization text so search results can display verbatim content.
FTS_INDEX_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS fts_index
USING fts5(
    title,
    content,
    tags,
    original UNINDEXED,
    tokenize='unicode61',
    detail=column
);
"""

# Claims DB schema initialization SQL
_CLAIMS_CORE_SCHEMA = """
-- Core claims table
CREATE TABLE IF NOT EXISTS claim (
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

-- Claim relations table
CREATE TABLE IF NOT EXISTS claim_relation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_claim_uuid TEXT NOT NULL,
    target_claim_uuid TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (source_claim_uuid) REFERENCES claim(uuid),
    FOREIGN KEY (target_claim_uuid) REFERENCES claim(uuid)
);

-- Entity registry table
CREATE TABLE IF NOT EXISTS entity (
    uuid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    aliases TEXT NOT NULL DEFAULT '[]',
    entity_type TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Entity relations (knowledge graph edges)
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
"""

_CLAIMS_INDEX_SCHEMA = """
-- Partial indexes for performance
CREATE INDEX IF NOT EXISTS idx_claim_source ON claim(source_uuid) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_claim_confidence ON claim(confidence) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_claim_hash ON claim(content_hash) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_entity_name ON entity(name);
"""

CLAIMS_DB_SCHEMA = _CLAIMS_CORE_SCHEMA + FTS_INDEX_DDL + _CLAIMS_INDEX_SCHEMA


def _tags_to_text(tags_json: str | None) -> str:
    """Convert a claim's tags JSON column into searchable plain text."""
    if not tags_json:
        return ""
    try:
        parsed = json.loads(tags_json)
    except (json.JSONDecodeError, TypeError):
        return str(tags_json)
    if isinstance(parsed, list):
        return " ".join(str(t) for t in parsed)
    return str(parsed)


class SQLiteClaimsRepository:
    """Claims DB repository backed by SQLite with FTS5.

    Implements the ClaimsRepository protocol.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._init_schema()

    def _init_schema(self) -> None:
        """Run DB migrations to bring the claims schema up to date.

        C4: delegates to ``saw.db.migrations.apply_migrations``, which uses
        ``PRAGMA user_version`` to track the applied version. The previous
        ``executescript(CLAIMS_DB_SCHEMA)`` + ad-hoc ``_migrate_fts_schema``
        are now handled by the v1 migration.
        """
        try:
            from saw.db.migrations import apply_migrations

            apply_migrations(self._conn)
        except sqlite3.Error as e:
            raise ClaimsDBError(f"Failed to apply DB migrations: {e}") from e

    def get_by_id(self, uuid: str) -> Claim | None:
        """Retrieve a claim by its UUID."""
        row = self._conn.execute(
            "SELECT * FROM claim WHERE uuid = ? AND deleted_at IS NULL",
            (uuid,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_claim(row)

    def insert(self, claim: Claim) -> str:
        """Insert a new claim. Idempotent via INSERT OR IGNORE."""
        try:
            self._conn.execute(
                """INSERT OR IGNORE INTO claim
                   (uuid, content, source_uuid, page_number, line_number,
                    timestamp, confidence, source_mark, tags, entities,
                    content_hash, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    claim.uuid,
                    claim.content,
                    claim.source_uuid,
                    claim.page_number,
                    claim.line_number,
                    claim.timestamp,
                    claim.confidence.name.lower(),
                    claim.source_mark.name.lower(),
                    json.dumps(claim.tags),
                    json.dumps(claim.entities),
                    claim.content_hash,
                    claim.created_at.isoformat(),
                ),
            )
            self._conn.commit()
            return claim.uuid
        except sqlite3.Error as e:
            raise ClaimsDBError(f"Failed to insert claim: {e}") from e

    def search(self, query: str, limit: int = 10) -> list[Claim]:
        """Full-text search via FTS5 MATCH with bm25 ranking."""
        try:
            match_expr = build_match_query(query)
            if not match_expr:
                return []
            rows = self._conn.execute(
                """SELECT c.*
                   FROM claim c
                   JOIN fts_index f ON f.title = c.uuid
                   WHERE f.fts_index MATCH ?
                     AND c.deleted_at IS NULL
                   ORDER BY bm25(fts_index)
                   LIMIT ?""",
                (match_expr, limit),
            ).fetchall()
            return [self._row_to_claim(row) for row in rows]
        except sqlite3.Error as e:
            raise ClaimsDBError(f"FTS5 search failed: {e}") from e

    def get_by_source(self, source_uuid: str) -> list[Claim]:
        """Get all claims originating from a specific source."""
        rows = self._conn.execute(
            "SELECT * FROM claim WHERE source_uuid = ? AND deleted_at IS NULL",
            (source_uuid,),
        ).fetchall()
        return [self._row_to_claim(row) for row in rows]

    def count(self) -> int:
        """Count total non-deleted claims."""
        row = self._conn.execute(
            "SELECT count(*) FROM claim WHERE deleted_at IS NULL"
        ).fetchone()
        return row[0] if row else 0

    @staticmethod
    def _row_to_claim(row) -> Claim:
        """Convert a database row to a Claim dataclass."""
        return Claim(
            uuid=row[0],
            content=row[1],
            source_uuid=row[2],
            page_number=row[3],
            line_number=row[4],
            timestamp=row[5],
            confidence=ConfidenceLevel[row[6].upper()],
            source_mark=SourceMark[row[7].upper()],
            tags=json.loads(row[8]) if row[8] else [],
            entities=json.loads(row[9]) if row[9] else [],
            content_hash=row[10],
        )

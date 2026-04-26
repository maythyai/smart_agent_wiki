"""Claims DB schema and SQLite repository implementation.

Per D-03: FTS5 with unicode61 tokenizer, detail=column, automerge=8.
Per Pitfall 7: INSERT OR IGNORE for idempotent writes.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from saw.domain.claims import Claim
from saw.domain.exceptions import ClaimsDBError
from saw.domain.value_objects import ConfidenceLevel, SourceMark

# Claims DB schema initialization SQL
CLAIMS_DB_SCHEMA = """
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

-- FTS5 virtual table (per D-03)
CREATE VIRTUAL TABLE IF NOT EXISTS fts_index
USING fts5(
    title,
    content,
    tags,
    content='',
    tokenize='unicode61',
    detail=column
);

-- FTS5 segment merge config (per Pitfall 5 in PITFALLS.md)
INSERT INTO fts_index(fts_index, rank) VALUES('automerge', 8);
INSERT INTO fts_index(fts_index, rank) VALUES('crisismerge', 4);

-- Partial indexes for performance
CREATE INDEX IF NOT EXISTS idx_claim_source ON claim(source_uuid) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_claim_confidence ON claim(confidence) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_claim_hash ON claim(content_hash) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_entity_name ON entity(name);
"""


class SQLiteClaimsRepository:
    """Claims DB repository backed by SQLite with FTS5.

    Implements the ClaimsRepository protocol.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize the Claims DB schema."""
        try:
            self._conn.executescript(CLAIMS_DB_SCHEMA)
            self._conn.commit()
        except sqlite3.Error as e:
            raise ClaimsDBError(f"Failed to initialize Claims DB schema: {e}") from e

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
            rows = self._conn.execute(
                """SELECT c.*
                   FROM claim c
                   JOIN fts_index f ON f.title = c.uuid
                   WHERE f.fts_index MATCH ?
                     AND c.deleted_at IS NULL
                   ORDER BY bm25(fts_index)
                   LIMIT ?""",
                (query, limit),
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

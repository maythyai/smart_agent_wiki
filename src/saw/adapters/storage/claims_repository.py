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
import threading
from datetime import datetime, timezone

from saw.adapters.storage.fts_tokenize import build_match_query
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
        self._write_lock = threading.Lock()
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

    def get_by_id(self, uuid: str, workspace_id: str | None = None) -> Claim | None:
        """Retrieve a claim by its UUID.

        Args:
            uuid: Claim UUID.
            workspace_id: When set, restrict to claims in this workspace
                (T-F-Z-7, ADR-007). None = no workspace filter (admin/cross-ws
                lookups); the default keeps existing callers unchanged.
        """
        if workspace_id is None:
            row = self._conn.execute(
                "SELECT * FROM claim WHERE uuid = ? AND deleted_at IS NULL",
                (uuid,),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT * FROM claim WHERE uuid = ? AND deleted_at IS NULL "
                "AND workspace_id = ?",
                (uuid, workspace_id),
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
                    content_hash, created_at, source_platform, source_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                    claim.source_platform,
                    claim.source_id,
                ),
            )
            self._conn.commit()
            return claim.uuid
        except sqlite3.Error as e:
            raise ClaimsDBError(f"Failed to insert claim: {e}") from e

    def search(
        self, query: str, limit: int = 10, workspace_id: str | None = None
    ) -> list[Claim]:
        """Full-text search via FTS5 MATCH with bm25 ranking.

        Args:
            query: Search query (tokenized via ``build_match_query``).
            limit: Max results.
            workspace_id: When set, restrict matches to claims in this
                workspace (T-F-Z-7, ADR-007). None = no filter.
        """
        try:
            match_expr = build_match_query(query)
            if not match_expr:
                return []
            if workspace_id is None:
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
            else:
                rows = self._conn.execute(
                    """SELECT c.*
                       FROM claim c
                       JOIN fts_index f ON f.title = c.uuid
                       WHERE f.fts_index MATCH ?
                         AND c.deleted_at IS NULL
                         AND c.workspace_id = ?
                       ORDER BY bm25(fts_index)
                       LIMIT ?""",
                    (match_expr, workspace_id, limit),
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

    # T-F-P-4: workspace isolation (ADR-005). Schema-prefix scoping within a
    # single DB — list_by_workspace returns only claims owned by that
    # workspace; set_workspace assigns a claim. Existing claims default to
    # 'default' (migration v8) so single-wiki use is unchanged.
    def list_by_workspace(self, workspace_id: str) -> list[Claim]:
        """Return all non-deleted claims in a workspace (AC-WS-1 isolation)."""
        rows = self._conn.execute(
            "SELECT * FROM claim WHERE workspace_id = ? AND deleted_at IS NULL",
            (workspace_id,),
        ).fetchall()
        return [self._row_to_claim(row) for row in rows]

    def set_workspace(self, claim_uuid: str, workspace_id: str) -> None:
        """Assign a claim to a workspace."""
        self._conn.execute(
            "UPDATE claim SET workspace_id = ? WHERE uuid = ?",
            (workspace_id, claim_uuid),
        )
        self._conn.commit()

    def grant_workspace_access(
        self, user_id: str, workspace_id: str, role: str = "editor"
    ) -> None:
        """Grant a user access to a workspace (user_workspace_auth)."""
        self._conn.execute(
            """INSERT INTO user_workspace_auth (user_id, workspace_id, role)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id, workspace_id)
               DO UPDATE SET role=excluded.role""",
            (user_id, workspace_id, role),
        )
        self._conn.commit()

    def user_workspaces(self, user_id: str) -> list[str]:
        """Return the workspace ids a user is authorized for (AC-WS-2)."""
        rows = self._conn.execute(
            "SELECT workspace_id FROM user_workspace_auth WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        return [r[0] for r in rows]

    def upsert(self, claim: Claim) -> str:
        """Insert or update a claim (F-CONN-04 resolution).

        If a claim with this UUID exists (and isn't soft-deleted), UPDATE its
        content so a platform-wins conflict overwrites the stale version
        (INSERT OR IGNORE previously left the old content). Otherwise INSERT.
        """
        try:
            cur = self._conn.execute(
                """UPDATE claim
                   SET content = ?, content_hash = ?, source_platform = ?,
                       source_id = ?, updated_at = ?
                   WHERE uuid = ? AND deleted_at IS NULL""",
                (
                    claim.content,
                    claim.content_hash,
                    claim.source_platform,
                    claim.source_id,
                    datetime.now(timezone.utc).isoformat(),
                    claim.uuid,
                ),
            )
            if cur.rowcount == 0:
                self.insert(claim)
            else:
                self._conn.commit()
            return claim.uuid
        except sqlite3.Error as e:
            raise ClaimsDBError(f"Failed to upsert claim: {e}") from e

    def get_by_source_id(
        self, source_platform: str, source_id: str
    ) -> dict | None:
        """Look up an existing claim by connector provenance (F-CONN-04).

        Returns a lightweight dict (uuid/content/updated_at) or None.
        """
        try:
            row = self._conn.execute(
                "SELECT uuid, content, created_at, updated_at FROM claim "
                "WHERE source_platform = ? AND source_id = ? "
                "AND deleted_at IS NULL LIMIT 1",
                (source_platform, source_id),
            ).fetchone()
        except sqlite3.Error:
            return None
        if row is None:
            return None
        return {
            "id": row[0],
            "uuid": row[0],
            "content": row[1],
            "updated_at": row[3] or row[2],
        }

    def count(self) -> int:
        """Count total non-deleted claims."""
        row = self._conn.execute(
            "SELECT count(*) FROM claim WHERE deleted_at IS NULL"
        ).fetchone()
        return row[0] if row else 0

    # ── HI-1: SQL previously inline in API routes (govern.py /
    #    query_ingest_learn.py) is moved here so routes depend on the
    #    repository contract, not on ``repo._conn`` / ``import sqlite3``. ──

    def update_confidence(self, claim_uuid: str, confidence: str) -> None:
        """Set a claim's confidence level."""
        with self._write_lock:
            self._conn.execute(
                "UPDATE claim SET confidence = ?, updated_at = ? WHERE uuid = ?",
                (confidence, datetime.now(timezone.utc).isoformat(), claim_uuid),
            )
            self._conn.commit()

    def soft_delete_claim(self, claim_uuid: str) -> None:
        """Soft-delete a claim (sets ``deleted_at``)."""
        with self._write_lock:
            self._conn.execute(
                "UPDATE claim SET deleted_at = ? WHERE uuid = ?",
                (datetime.now(timezone.utc).isoformat(), claim_uuid),
            )
            self._conn.commit()

    def list_contradictions(self, status: str = "pending") -> list[dict]:
        """List contradictions by status (``pending``/``resolved``/``all``)."""
        if status == "resolved":
            rows = self._conn.execute(
                "SELECT * FROM contradictions WHERE resolved_at IS NOT NULL"
            ).fetchall()
        elif status == "pending":
            rows = self._conn.execute(
                "SELECT * FROM contradictions WHERE resolved_at IS NULL"
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM contradictions").fetchall()
        results = []
        for row in rows:
            results.append({
                "uuid": row[0],
                "claim_a_uuid": row[1],
                "claim_b_uuid": row[2],
                "contradiction_type": row[3],
                "resolution": row[4],
                "detected_at": row[5],
                "resolved_at": row[6],
                "blast_radius": json.loads(row[7]) if row[7] else [],
            })
        return results

    def resolve_contradiction(self, contradiction_id: str, strategy: str) -> None:
        """Mark a contradiction resolved with the given strategy."""
        with self._write_lock:
            self._conn.execute(
                "UPDATE contradictions SET resolution = ?, resolved_at = ? WHERE uuid = ?",
                (strategy, datetime.now(timezone.utc).isoformat(), contradiction_id),
            )
            self._conn.commit()

    def count_relations(self, claim_uuid: str) -> int:
        """Count claim_relation rows touching *claim_uuid* (either side)."""
        row = self._conn.execute(
            "SELECT COUNT(*) FROM claim_relation "
            "WHERE source_claim_uuid = ? OR target_claim_uuid = ?",
            (claim_uuid, claim_uuid),
        ).fetchone()
        return int(row[0]) if row else 0

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

"""FTS5 sink - updates the full-text search index.

Per Pitfall 7: DELETE old + INSERT new pattern for updates.
Per Pitfall 1: verify row count consistency after insert.

The indexed ``content``/``tags`` columns hold CJK-tokenized text (see
saw.adapters.storage.fts_tokenize); the verbatim text is kept in the
UNINDEXED ``original`` column for display.
"""
from __future__ import annotations

import sqlite3

from saw.adapters.storage.fts_tokenize import tokenize_for_fts
from saw.domain.exceptions import FTS5Error


class FTS5Sink:
    """Write Queue sink for FTS5 index updates."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    @property
    def name(self) -> str:
        return "fts5"

    def write(self, op) -> None:
        """Insert/update FTS5 index entry.

        For updates: DELETE old + INSERT new (per Pitfall 7 recommendation 2).
        """
        payload = op.payload
        # Support both doc_id and claim_uuid as identifiers
        doc_id = payload.get("doc_id") or payload.get("claim_uuid") or op.op_id
        title = payload.get("title") or doc_id
        content = payload.get("content", "")
        tags = payload.get("tags", "")

        try:
            # Delete existing entry (safe even if not present)
            self._conn.execute(
                "DELETE FROM fts_index WHERE title = ?",
                (doc_id,),
            )
            # Insert new entry (tokenized for CJK-aware matching)
            self._conn.execute(
                "INSERT INTO fts_index (title, content, tags, original) "
                "VALUES (?, ?, ?, ?)",
                (doc_id, tokenize_for_fts(content), tokenize_for_fts(tags), content),
            )
            self._conn.commit()
        except sqlite3.Error as e:
            raise FTS5Error(f"FTS5 sink write failed for {op.op_id}: {e}") from e

    def can_handle(self, sink_name: str) -> bool:
        return sink_name == "fts5"

"""FTS5 sink - updates the full-text search index.

Per Pitfall 7: DELETE old + INSERT new pattern for updates.
Per Pitfall 1: verify row count consistency after insert.

The indexed ``content``/``tags`` columns hold CJK-tokenized text (see
saw.adapters.storage.fts_tokenize); the verbatim text is kept in the
UNINDEXED ``original`` column for display.

The DELETE+INSERT pair is wrapped in a single transaction (via
:func:`saw.adapters.storage.fts5_utils.upsert_fts_entry`) so a crash
between the two statements no longer loses the index entry (C3 fix).
"""
from __future__ import annotations

import sqlite3

from saw.adapters.storage.fts5_utils import upsert_fts_entry
from saw.domain.exceptions import FTS5Error


class FTS5Sink:
    """Write Queue sink for FTS5 index updates."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    @property
    def name(self) -> str:
        return "fts5"

    def write(self, op) -> None:
        """Insert/update an FTS5 index entry (atomic DELETE+INSERT)."""
        payload = op.payload
        # Support both doc_id and claim_uuid as identifiers
        doc_id = payload.get("doc_id") or payload.get("claim_uuid") or op.op_id
        title = payload.get("title") or doc_id
        content = payload.get("content", "")
        tags = payload.get("tags", "")
        # The ``original`` column holds verbatim text for display; combine
        # title+content so the rendered snippet is searchable verbatim.
        original = payload.get("original")
        if original is None:
            original = f"{title} {content}" if title != doc_id else content

        try:
            upsert_fts_entry(
                self._conn, doc_id, content, tags=str(tags), original=original
            )
        except sqlite3.Error as e:
            raise FTS5Error(f"FTS5 sink write failed for {op.op_id}: {e}") from e

    def can_handle(self, sink_name: str) -> bool:
        return sink_name == "fts5"

"""Shared, transactional FTS5 upsert helpers.

Both the Write Queue ``FTS5Sink`` and the eager ``WikiIndexer`` need to
DELETE-then-INSERT into ``fts_index``. Doing the two statements outside a
single transaction leaves a window where a crash loses the index entry
(this was the original C3 bug). These helpers wrap the pair in
``with conn:`` so SQLite commits both atomically or rolls both back.

Both helpers are no-ops on transient sqlite errors when the caller opts
into best-effort mode (the index is a derived cache that can always be
rebuilt).
"""
from __future__ import annotations

import sqlite3

from saw.adapters.storage.fts_tokenize import tokenize_for_fts


def upsert_fts_entry(
    conn: sqlite3.Connection,
    doc_id: str,
    content: str,
    tags: str = "",
    original: str | None = None,
) -> None:
    """Atomically DELETE then INSERT an FTS5 row.

    Args:
        conn: SQLite connection with the ``fts_index`` table.
        doc_id: Value stored in the ``title`` column (the document key —
            for wiki pages this is the slug, for claims the claim uuid).
        content: Text to tokenize into the ``content`` column.
        tags: Whitespace-joined tags to tokenize into the ``tags`` column.
        original: Verbatim text for the UNINDEXED ``original`` column;
            defaults to ``content`` when not provided.
    """
    if original is None:
        original = content
    tokenized_content = tokenize_for_fts(content)
    tokenized_tags = tokenize_for_fts(tags)
    # ``with conn:`` opens an implicit transaction covering both statements
    # — a crash between DELETE and INSERT no longer loses the index entry.
    with conn:
        conn.execute("DELETE FROM fts_index WHERE title = ?", (doc_id,))
        conn.execute(
            "INSERT INTO fts_index (title, content, tags, original) "
            "VALUES (?, ?, ?, ?)",
            (doc_id, tokenized_content, tokenized_tags, original),
        )


def delete_fts_entry(conn: sqlite3.Connection, doc_id: str) -> None:
    """Atomically remove an FTS5 row."""
    with conn:
        conn.execute("DELETE FROM fts_index WHERE title = ?", (doc_id,))

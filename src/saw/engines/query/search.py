"""FTS5 search service for full-text search with BM25 ranking.

Per D-13: BM25 + FTS5 as primary search.
Per RESEARCH.md: FTS5 bm25() for ranking, rank-bm25 for supplementary scoring.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

from saw.adapters.storage.fts_tokenize import build_match_query


@dataclass
class SearchResult:
    """Search result from FTS5 query."""
    claim_uuids: list[str] = field(default_factory=list)
    titles: list[str] = field(default_factory=list)
    contents: list[str] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)
    total: int = 0


class FTS5Search:
    """FTS5 search service with BM25 ranking.

    Per D-03: FTS5 with unicode61 tokenizer, detail=column.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Initialize with SQLite connection.

        Args:
            conn: SQLite connection with FTS5 index available.
        """
        self._conn = conn

    def search(
        self, query: str, limit: int = 10, offset: int = 0
    ) -> SearchResult:
        """Execute FTS5 MATCH query with bm25() ranking.

        Args:
            query: Search query string (FTS5 MATCH syntax).
            limit: Maximum number of results.
            offset: Offset for pagination.

        Returns:
            SearchResult with ranked claims.
        """
        if not query or not query.strip():
            return SearchResult()

        try:
            # Escape query for FTS5 MATCH (CJK-aware tokenization)
            escaped_query = self._escape_query(query)
            if not escaped_query:
                return SearchResult()

            # Execute FTS5 search with bm25 ranking
            # The title column in fts_index stores the claim UUID
            # We use rowid mapping: fts_index.rowid maps to claim.uuid
            # For simplicity, we store UUID in title column and query directly
            # Display text comes from the UNINDEXED original column
            # (pre-tokenization); fall back to indexed content for rows
            # written before the CJK migration.
            rows = self._conn.execute(
                """SELECT title, COALESCE(original, content) AS body,
                          bm25(fts_index) as rank
                   FROM fts_index
                   WHERE fts_index MATCH ?
                   ORDER BY rank
                   LIMIT ? OFFSET ?""",
                (escaped_query, limit, offset),
            ).fetchall()

            claim_uuids = []
            contents = []
            scores = []

            for row in rows:
                uuid = row[0]
                content = row[1] or ""
                # bm25 returns negative scores, higher (closer to 0) is better
                score = -row[2] if row[2] else 0.0
                # Check if claim is deleted
                deleted_row = self._conn.execute(
                    "SELECT 1 FROM claim WHERE uuid = ? AND deleted_at IS NULL",
                    (uuid,),
                ).fetchone()
                if deleted_row:
                    claim_uuids.append(uuid)
                    contents.append(content)
                    scores.append(score)

            # Get total count for pagination
            count_row = self._conn.execute(
                """SELECT COUNT(*)
                   FROM fts_index f
                   JOIN claim c ON c.uuid = f.title
                   WHERE f.fts_index MATCH ?
                     AND c.deleted_at IS NULL""",
                (escaped_query,),
            ).fetchone()
            total = count_row[0] if count_row else 0

            return SearchResult(
                claim_uuids=claim_uuids,
                titles=claim_uuids,  # Use UUID as title since we don't store separate title
                contents=contents,
                scores=scores,
                total=total,
            )
        except sqlite3.Error:
            # If FTS5 query fails, return empty result
            return SearchResult()

    def search_with_snippets(
        self, query: str, limit: int = 10
    ) -> SearchResult:
        """Execute FTS5 search with highlighted snippets.

        Args:
            query: Search query string.
            limit: Maximum number of results.

        Returns:
            SearchResult with snippet-highlighted content.
        """
        if not query or not query.strip():
            return SearchResult()

        try:
            escaped_query = self._escape_query(query)
            if not escaped_query:
                return SearchResult()

            # snippet()/highlight() would render CJK-tokenized text with
            # inserted spaces, so display the verbatim original column.
            rows = self._conn.execute(
                """SELECT title, COALESCE(original, content) AS body,
                          bm25(fts_index) as rank
                   FROM fts_index
                   WHERE fts_index MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (escaped_query, limit),
            ).fetchall()

            claim_uuids = []
            contents = []
            scores = []

            for row in rows:
                uuid = row[0]
                content = row[1] or ""
                score = -row[2] if row[2] else 0.0
                # Check if claim is deleted
                deleted_row = self._conn.execute(
                    "SELECT 1 FROM claim WHERE uuid = ? AND deleted_at IS NULL",
                    (uuid,),
                ).fetchone()
                if deleted_row:
                    claim_uuids.append(uuid)
                    contents.append(content)
                    scores.append(score)

            return SearchResult(
                claim_uuids=claim_uuids,
                titles=claim_uuids,
                contents=contents,
                scores=scores,
                total=len(claim_uuids),
            )
        except sqlite3.Error:
            return SearchResult()

    def count(self, query: str) -> int:
        """Get total matching results for pagination.

        Args:
            query: Search query string.

        Returns:
            Total number of matching claims.
        """
        if not query or not query.strip():
            return 0

        try:
            escaped_query = self._escape_query(query)
            if not escaped_query:
                return 0
            row = self._conn.execute(
                """SELECT COUNT(*)
                   FROM fts_index f
                   JOIN claim c ON c.uuid = f.title
                   WHERE f.fts_index MATCH ?
                     AND c.deleted_at IS NULL""",
                (escaped_query,),
            ).fetchone()
            return row[0] if row else 0
        except sqlite3.Error:
            return 0

    def _escape_query(self, query: str) -> str:
        """Escape query for FTS5 MATCH syntax (CJK-aware).

        Latin words are AND-joined; CJK runs are segmented (jieba when
        available, else unigram+bigram fallback) and OR-joined so Chinese
        queries match regardless of exact word boundaries. See
        saw.adapters.storage.fts_tokenize for details.

        Args:
            query: Raw query string.

        Returns:
            FTS5-safe MATCH expression (may be empty).
        """
        return build_match_query(query)

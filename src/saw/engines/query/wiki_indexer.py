"""Wiki page FTS5 indexer.

Indexes wiki pages into the fts_index table for full-text search.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from saw.adapters.storage.fts_tokenize import tokenize_for_fts
from saw.engines.query.wiki_links import extract_unique_targets

if TYPE_CHECKING:
    from saw.adapters.storage.wiki_repository import WikiRepository


class WikiIndexer:
    """Indexes wiki pages into FTS5 search index."""

    def __init__(self, conn: sqlite3.Connection, wiki_repo: WikiRepository) -> None:
        """Initialize wiki indexer.

        Args:
            conn: SQLite connection with fts_index table.
            wiki_repo: Wiki repository to index.
        """
        self._conn = conn
        self._wiki_repo = wiki_repo

    def index_all(self) -> int:
        """Index all wiki pages into FTS5.

        Returns:
            Number of pages indexed.
        """
        count = 0
        for slug in self._wiki_repo.list_pages():
            page = self._wiki_repo.read(slug)
            if page is None:
                continue

            self._index_page(slug, page.title, page.content, page.tags)
            count += 1

        return count

    def index_page(self, slug: str) -> bool:
        """Index a single wiki page.

        Args:
            slug: Page slug to index.

        Returns:
            True if indexed, False if page not found.
        """
        page = self._wiki_repo.read(slug)
        if page is None:
            return False

        self._index_page(slug, page.title, page.content, page.tags)
        return True

    def _index_page(self, slug: str, title: str, content: str, tags: list[str]) -> None:
        """Index a wiki page into fts_index.

        Uses slug as the doc_id (title column in fts_index).

        Args:
            slug: Page slug/identifier.
            title: Page title.
            content: Page markdown content.
            tags: Page tags.
        """
        try:
            # Delete existing entry (safe even if not present)
            self._conn.execute(
                "DELETE FROM fts_index WHERE title = ?",
                (slug,),
            )

            # Combine title + content + tags for search
            tags_str = " ".join(tags) if tags else ""
            searchable = f"{title} {content} {tags_str}"

            # Insert new entry (tokenized for CJK-aware matching; the
            # verbatim text goes into the UNINDEXED original column)
            self._conn.execute(
                "INSERT INTO fts_index (title, content, tags, original) "
                "VALUES (?, ?, ?, ?)",
                (
                    slug,
                    tokenize_for_fts(searchable),
                    tokenize_for_fts(tags_str),
                    searchable,
                ),
            )
            self._conn.commit()
        except sqlite3.Error as e:
            # Log error but don't fail - indexing is best-effort
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to index wiki page {slug}: {e}")

    def remove_page(self, slug: str) -> None:
        """Remove a wiki page from FTS5 index.

        Args:
            slug: Page slug to remove.
        """
        try:
            self._conn.execute(
                "DELETE FROM fts_index WHERE title = ?",
                (slug,),
            )
            self._conn.commit()
        except sqlite3.Error:
            pass  # Best-effort removal

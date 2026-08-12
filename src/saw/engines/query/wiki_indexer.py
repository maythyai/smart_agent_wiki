"""Wiki page FTS5 indexer.

Indexes wiki pages into the fts_index table for full-text search.

C3: previously duplicated the FTS5 DELETE+INSERT logic that lives in
``saw.write_queue.sinks.fts5_sink``; both now share the transactional
helpers in ``saw.adapters.storage.fts5_utils`` so the index update is
atomic and there is a single source of truth for the upsert.
"""
from __future__ import annotations

import logging
import sqlite3
from typing import TYPE_CHECKING

from saw.adapters.storage.fts5_utils import delete_fts_entry, upsert_fts_entry

if TYPE_CHECKING:
    from saw.adapters.storage.wiki_repository import WikiRepository

logger = logging.getLogger(__name__)


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
        """Index a wiki page into fts_index (atomic upsert).

        Uses slug as the doc_id (the ``title`` column in fts_index).
        """
        tags_str = " ".join(tags) if tags else ""
        searchable = f"{title} {content} {tags_str}"
        try:
            upsert_fts_entry(
                self._conn,
                doc_id=slug,
                content=searchable,
                tags=tags_str,
                original=searchable,
            )
        except sqlite3.Error as e:
            # Best-effort: indexing is a derived cache, rebuildable.
            logger.warning("Failed to index wiki page %s: %s", slug, e)

    def remove_page(self, slug: str) -> None:
        """Remove a wiki page from the FTS5 index (atomic delete)."""
        try:
            delete_fts_entry(self._conn, slug)
        except sqlite3.Error:
            # Best-effort removal.
            pass

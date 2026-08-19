"""Regression tests for FTS5 search returning wiki-only content.

WikiIndexer stores wiki pages in ``fts_index`` with the page slug as the
``title`` (doc_id), while claims use their UUID. The old search code did
``JOIN claim c ON c.uuid = f.title`` and a per-row ``SELECT 1 FROM claim
WHERE uuid = ?`` filter, which dropped every wiki-only row — so wiki pages
were unsearchable. These tests lock the fixed behaviour: wiki slugs are
returned, and soft-deleted claims are still filtered out.
"""
from __future__ import annotations

import sqlite3

import pytest

from saw.engines.query.search import FTS5Search, SearchResult


@pytest.fixture
def db_with_wiki_and_claims() -> sqlite3.Connection:
    """In-memory DB with one claim, one deleted claim, and one wiki page."""
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS claim (
            uuid TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            source_uuid TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS fts_index
        USING fts5(
            title,
            content,
            tags,
            original UNINDEXED,
            tokenize='unicode61',
            detail=column
        )
    """)

    # A live claim, indexed under its UUID.
    conn.execute(
        "INSERT INTO claim (uuid, content, source_uuid, content_hash) "
        "VALUES ('claim-1', 'Machine learning uses neural networks.', 'src', 'h1')"
    )
    conn.execute(
        "INSERT INTO fts_index (title, content, tags, original) "
        "VALUES ('claim-1', 'Machine learning uses neural networks.', '', 'Machine learning uses neural networks.')"
    )

    # A soft-deleted claim, indexed under its UUID — must NOT be returned.
    conn.execute(
        "INSERT INTO claim (uuid, content, source_uuid, content_hash, deleted_at) "
        "VALUES ('claim-deleted', 'Machine learning is deprecated here.', 'src', 'h2', '2026-01-01')"
    )
    conn.execute(
        "INSERT INTO fts_index (title, content, tags, original) "
        "VALUES ('claim-deleted', 'Machine learning is deprecated here.', '', 'Machine learning is deprecated here.')"
    )

    # A wiki page indexed under its SLUG (no claim row). Must be returned.
    conn.execute(
        "INSERT INTO fts_index (title, content, tags, original) "
        "VALUES ('wiki-react-hooks', 'React hooks useState useEffect', '', 'React hooks useState useEffect')"
    )

    conn.commit()
    return conn


class TestSearchWikiAndClaims:
    def test_wiki_only_slug_is_searchable(self, db_with_wiki_and_claims) -> None:
        """A wiki page with no backing claim must appear in results."""
        search = FTS5Search(db_with_wiki_and_claims)
        result = search.search("react hooks")
        assert isinstance(result, SearchResult)
        assert "wiki-react-hooks" in result.claim_uuids
        assert result.total >= 1

    def test_live_claim_still_searchable(self, db_with_wiki_and_claims) -> None:
        """Non-deleted claims are still returned."""
        search = FTS5Search(db_with_wiki_and_claims)
        result = search.search("machine learning")
        assert "claim-1" in result.claim_uuids

    def test_deleted_claim_filtered_out(self, db_with_wiki_and_claims) -> None:
        """Soft-deleted claims must not appear in results or count."""
        search = FTS5Search(db_with_wiki_and_claims)
        result = search.search("machine learning")
        assert "claim-deleted" not in result.claim_uuids

    def test_count_includes_wiki_and_live_claims(self, db_with_wiki_and_claims) -> None:
        """count() must reflect wiki + live claims, excluding deleted ones."""
        search = FTS5Search(db_with_wiki_and_claims)
        # "machine learning" matches: claim-1 (live), claim-deleted (deleted),
        # and the wiki page does NOT mention "machine learning" -> total 1.
        assert search.count("machine learning") == 1
        # "react hooks" matches only the wiki page -> total 1.
        assert search.count("react hooks") == 1

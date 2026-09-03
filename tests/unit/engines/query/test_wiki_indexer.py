"""WikiIndexer + FTS5 utils coverage — T-F-Z-9 (AC-COV-1)."""
from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock

from saw.db.migrations import apply_migrations
from saw.domain.wiki import WikiPage
from saw.domain.value_objects import ConfidenceLevel, PageType


def _conn():
    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    return conn


def _page(slug, title="T", content="alpha beta", tags=("a",)):
    return WikiPage(
        path=slug, title=title, page_type=PageType.SUMMARY,
        tags=list(tags), confidence=ConfidenceLevel.UNVERIFIED, content=content,
    )


def test_index_all_indexes_pages():
    from saw.engines.query.wiki_indexer import WikiIndexer

    conn = _conn()
    wiki = MagicMock()
    pages = {"p1": _page("p1", "First", "alpha beta"), "p2": _page("p2", "Second", "gamma delta")}
    wiki.read.side_effect = lambda s: pages.get(s)
    wiki.list_pages.return_value = list(pages.keys())

    n = WikiIndexer(conn, wiki).index_all()
    assert n == 2
    # FTS index now has 2 rows (title column holds the slug/doc_id).
    rows = conn.execute("SELECT count(*) FROM fts_index").fetchone()[0]
    assert rows == 2


def test_index_page_missing_returns_false():
    from saw.engines.query.wiki_indexer import WikiIndexer

    conn = _conn()
    wiki = MagicMock()
    wiki.read.return_value = None
    assert WikiIndexer(conn, wiki).index_page("nope") is False


def test_index_page_then_remove():
    from saw.engines.query.wiki_indexer import WikiIndexer

    conn = _conn()
    wiki = MagicMock()
    wiki.read.return_value = _page("p1", "First", "alpha beta")
    idx = WikiIndexer(conn, wiki)
    assert idx.index_page("p1") is True
    assert conn.execute("SELECT count(*) FROM fts_index").fetchone()[0] == 1
    idx.remove_page("p1")
    assert conn.execute("SELECT count(*) FROM fts_index").fetchone()[0] == 0
    conn.close()


def test_index_page_handles_fts_error_gracefully():
    """A sqlite error during upsert is caught (best-effort indexing)."""
    from saw.engines.query.wiki_indexer import WikiIndexer

    conn = _conn()
    wiki = MagicMock()
    wiki.read.return_value = _page("p1", "First", "alpha")
    idx = WikiIndexer(conn, wiki)
    # Corrupt the fts_index table name resolution by dropping it mid-flight:
    conn.execute("DROP TABLE fts_index")
    # Should not raise; indexing is best-effort.
    idx._index_page("p1", "First", "alpha", ["a"])
    conn.close()

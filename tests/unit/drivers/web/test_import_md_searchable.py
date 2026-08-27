"""DEF-6: imported wiki pages must be searchable after import.

Previously the import routes called ``wiki_repo.write(page)`` directly and
never updated the FTS5 index, so imported pages were invisible to search
until a full re-index. The ``_index_page`` helper indexes the page on write.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from saw.adapters.storage.wiki_repository import WikiRepository
from saw.domain.value_objects import ConfidenceLevel, FreshnessLevel, PageType
from saw.domain.wiki import WikiPage
from saw.drivers.web.routes.import_md import _index_page
from saw.engines.query.search import FTS5Search
from saw.write_queue.queue import SQLiteWriteQueue


def _page(slug: str, title: str, content: str) -> WikiPage:
    return WikiPage(
        path=f"imported/{slug}.md",
        title=title,
        page_type=PageType.SUMMARY,
        tags=["arch"],
        confidence=ConfidenceLevel.UNVERIFIED,
        freshness=FreshnessLevel.LEVEL_0,
        content=content,
    )


def test_imported_page_is_searchable_after_write(tmp_path: Path) -> None:
    wiki = WikiRepository(tmp_path)
    conn = sqlite3.connect(str(tmp_path / "q.db"))
    wq = SQLiteWriteQueue(conn)  # migrations create fts_index

    page = _page("design", "Foo Design", "arch decision: reuse token cache")
    wiki.write(page)
    _index_page(wq, wiki, page)

    # Row exists in fts_index under the page slug (title column = doc_id)
    row = conn.execute(
        "SELECT 1 FROM fts_index WHERE title = ?", ("imported/design.md",)
    ).fetchone()
    assert row is not None

    # And the real search path returns it
    result = FTS5Search(conn).search("token cache")
    assert "imported/design.md" in result.claim_uuids


def test_page_not_yet_written_is_not_searchable(tmp_path: Path) -> None:
    wiki = WikiRepository(tmp_path)
    conn = sqlite3.connect(str(tmp_path / "q.db"))
    wq = SQLiteWriteQueue(conn)

    # Index without writing first — index_page returns False (page not found)
    page = _page("missing", "Missing", "never written content")
    # Don't write to wiki_repo first; _index_page reads via wiki_repo → not found
    _index_page(wq, wiki, page)  # best-effort no-op
    result = FTS5Search(conn).search("never written")
    assert "imported/missing.md" not in result.claim_uuids


def test_import_markdown_route_end_to_end_indexes_page(tmp_path: Path) -> None:
    """The real route handler must successfully import + index a .md file.

    Regression: the route used ``PageType.CONCEPT`` (no such enum member),
    so every import raised AttributeError inside the try/except and was
    recorded as an error instead of being imported. Now uses SUMMARY and
    indexes the page so it is searchable.
    """
    import asyncio
    import io

    from starlette.datastructures import UploadFile

    from saw.drivers.web.routes.import_md import import_markdown

    wiki = WikiRepository(tmp_path)
    conn = sqlite3.connect(str(tmp_path / "route.db"))
    wq = SQLiteWriteQueue(conn)

    body = b"---\ntitle: Foo Design\n---\nreuse the token cache for arch\n"
    upload = UploadFile(filename="foo.md", file=io.BytesIO(body))

    result = asyncio.run(
        import_markdown(files=[upload], wiki_repo=wiki, write_queue=wq)
    )

    assert result["imported"] == 1, f"route reported errors: {result}"
    assert result["errors"] == 0
    hits = FTS5Search(conn).search("token cache").claim_uuids
    assert "imported/foo.md" in hits

"""TC-COMP-13/14/16: index entry / header / render tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from saw.domain.wiki_compile import (
    WikiCompilePage,
    WikiConfidence,
    WikiIndex,
    WikiIndexEntry,
    WikiPageMetadata,
    WikiPageType,
    WikiSource,
)
from saw.engines.compile.compiler import WikiCompileEngine


# ── TC-COMP-13: _update_index_entry ──────────────────────────────────

@pytest.mark.asyncio
async def test_update_index_entry(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    engine.wiki_root.mkdir(parents=True, exist_ok=True)
    (engine.wiki_root / "index.md").write_text(
        engine._render_empty_index(), encoding="utf-8"
    )

    page = WikiCompilePage(
        filename="concepts/ml.md",
        title="Machine Learning",
        content="# Machine Learning\n",
        metadata=WikiPageMetadata(
            type=WikiPageType.CONCEPT,
            confidence=WikiConfidence.HIGH,
            sources=[WikiSource(page_id="src.md", title="Source")],
            topic="concepts",
        ),
    )
    engine._update_index_entry(page)

    index_content = (engine.wiki_root / "index.md").read_text(encoding="utf-8")
    assert "ml" in index_content.lower()


# ── TC-COMP-14: _update_index_header ────────────────────────────────

@pytest.mark.asyncio
async def test_update_index_header_total_count(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    await engine.compile_full()

    index_content = (engine.wiki_root / "index.md").read_text(encoding="utf-8")
    assert "Total pages: 3" in index_content


# ── TC-COMP-16: _render_index ────────────────────────────────────────

def test_render_index_with_entries():
    """_render_index produces markdown with topic headings + table headers."""
    from saw.domain.utils import utcnow

    engine = WikiCompileEngine.__new__(WikiCompileEngine)
    engine._wiki_root = Path("/tmp/fake")

    index = WikiIndex()
    index.add_entry(
        "concepts",
        WikiIndexEntry(
            filename="concepts/ml.md",
            title="ML",
            summary="concept (1 source)",
            updated=utcnow(),
        ),
    )
    rendered = engine._render_index(index)
    assert "## Concepts" in rendered
    assert "| Page | Summary | Updated |" in rendered


def test_render_index_empty():
    engine = WikiCompileEngine.__new__(WikiCompileEngine)
    engine._wiki_root = Path("/tmp/fake")

    index = WikiIndex()
    rendered = engine._render_index(index)
    assert "Total pages: 0" in rendered


# ── get_index / get_log / read_page / list_pages ────────────────────

@pytest.mark.asyncio
async def test_get_index_after_compile(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    await engine.compile_full()
    index = await engine.get_index()
    assert index.total_pages > 0


@pytest.mark.asyncio
async def test_get_log_after_compile(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    await engine.compile_full()
    entries = engine.get_log()
    assert len(entries) > 0
    # Should have a compile entry
    actions = [e.action for e in entries]
    assert "compile" in actions


@pytest.mark.asyncio
async def test_read_page_after_compile(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    await engine.compile_full()
    pages = engine.list_pages()
    assert len(pages) == 3
    # Read one
    page = engine.read_page(pages[0])
    assert page is not None
    assert page.metadata is not None


@pytest.mark.asyncio
async def test_read_page_nonexistent(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    result = engine.read_page("nonexistent.md")
    assert result is None


# ── _render_empty_index / _render_log_header ────────────────────────

def test_render_empty_index():
    engine = WikiCompileEngine.__new__(WikiCompileEngine)
    engine._wiki_root = Path("/tmp/fake")
    rendered = engine._render_empty_index()
    assert "Knowledge Wiki Index" in rendered
    assert "Total pages: 0" in rendered


def test_render_log_header():
    engine = WikiCompileEngine.__new__(WikiCompileEngine)
    engine._wiki_root = Path("/tmp/fake")
    rendered = engine._render_log_header()
    assert "Compile Log" in rendered


# ── parser delegation ────────────────────────────────────────────────

def test_parse_index_delegates():
    engine = WikiCompileEngine.__new__(WikiCompileEngine)
    engine._wiki_root = Path("/tmp/fake")
    index = engine._parse_index("## topic\n| [[page]] | summary | date |")
    assert "topic" in index.topics


def test_parse_page_delegates():
    engine = WikiCompileEngine.__new__(WikiCompileEngine)
    engine._wiki_root = Path("/tmp/fake")
    page = engine._parse_page("test.md", "# Title\n\nBody")
    assert page.title == "Title"


def test_parse_log_delegates():
    engine = WikiCompileEngine.__new__(WikiCompileEngine)
    engine._wiki_root = Path("/tmp/fake")
    entries = engine._parse_log("## 2026-01-01T12:00:00+08:00 — COMPILE\n\n- Summary: test", 10)
    assert len(entries) >= 1

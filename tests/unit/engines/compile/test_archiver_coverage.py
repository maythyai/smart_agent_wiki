"""T-F-R-4: archiver.py coverage tests (coverage ratchet 65→67).

Tests the QueryArchiver archive(), suggest_archive(), list_archives(),
and helper methods.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from saw.engines.compile.archiver import QueryArchiver


def _make_wiki(tmp_path: Path) -> Path:
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "index.md").write_text("# Index\n\n## Pages\n\n| Title | Type |\n|-------|------|\n", encoding="utf-8")
    (wiki / "log.md").write_text("# Compile Log\n\n", encoding="utf-8")
    return wiki


@pytest.mark.asyncio
async def test_archive_creates_page(tmp_path):
    wiki = _make_wiki(tmp_path)
    archiver = QueryArchiver(wiki)
    page = await archiver.archive(
        query="What is machine learning?",
        answer="ML is a subset of AI.",
        referenced_pages=["concepts/ml.md", "concepts/ai.md"],
    )
    assert page.filename.startswith("archive/")
    page_path = wiki / page.filename
    assert page_path.exists()
    content = page_path.read_text()
    assert "machine learning" in content.lower()
    assert "ML is a subset" in content


@pytest.mark.asyncio
async def test_archive_creates_dir(tmp_path):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "index.md").write_text("# Index\n\n", encoding="utf-8")
    (wiki / "log.md").write_text("# Log\n\n", encoding="utf-8")
    archiver = QueryArchiver(wiki)
    await archiver.archive("q?", "a.", [])
    assert (wiki / "archive").exists()


@pytest.mark.asyncio
async def test_archive_invalid_confidence_defaults_medium(tmp_path):
    wiki = _make_wiki(tmp_path)
    archiver = QueryArchiver(wiki)
    page = await archiver.archive("q?", "a.", [], confidence="invalid")
    assert page.metadata.confidence.value == "medium"


@pytest.mark.asyncio
async def test_archive_updates_index(tmp_path):
    wiki = _make_wiki(tmp_path)
    archiver = QueryArchiver(wiki)
    await archiver.archive("What is ML?", "answer", ["concepts/ml.md"])
    index = (wiki / "index.md").read_text()
    assert "## Archive" in index


@pytest.mark.asyncio
async def test_archive_appends_log(tmp_path):
    wiki = _make_wiki(tmp_path)
    original_log = (wiki / "log.md").read_text()
    archiver = QueryArchiver(wiki)
    await archiver.archive("What is ML?", "answer", [])
    updated_log = (wiki / "log.md").read_text()
    assert len(updated_log) > len(original_log)


@pytest.mark.asyncio
async def test_archive_with_no_referenced_pages(tmp_path):
    wiki = _make_wiki(tmp_path)
    archiver = QueryArchiver(wiki)
    page = await archiver.archive("question?", "answer", [])
    assert len(page.metadata.sources) == 0


@pytest.mark.asyncio
async def test_suggest_archive_true(tmp_path):
    wiki = _make_wiki(tmp_path)
    archiver = QueryArchiver(wiki)
    result = await archiver.suggest_archive(
        "How does ML compare to traditional programming?",
        "x" * 600,
        ["a.md", "b.md", "c.md"],
    )
    assert result is True


@pytest.mark.asyncio
async def test_suggest_archive_false(tmp_path):
    wiki = _make_wiki(tmp_path)
    archiver = QueryArchiver(wiki)
    result = await archiver.suggest_archive("what time is it?", "noon", ["a.md"])
    assert result is False


def test_list_archives_empty(tmp_path):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    archiver = QueryArchiver(wiki)
    assert archiver.list_archives() == []


def test_list_archives_after_archive(tmp_path):
    wiki = _make_wiki(tmp_path)
    archiver = QueryArchiver(wiki)
    import asyncio
    asyncio.run(archiver.archive("What is ML?", "answer", []))
    archives = archiver.list_archives()
    assert len(archives) >= 1


def test_slugify(tmp_path):
    wiki = _make_wiki(tmp_path)
    archiver = QueryArchiver(wiki)
    assert archiver._slugify("What is ML?") == "what-is-ml"
    assert len(archiver._slugify("x" * 100)) <= 50


def test_make_title(tmp_path):
    wiki = _make_wiki(tmp_path)
    archiver = QueryArchiver(wiki)
    assert archiver._make_title("What?") == "What"
    assert len(archiver._make_title("x" * 100)) <= 80

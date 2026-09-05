"""TC-COMP-02/03/04: compile_full / compile_incremental / dedup tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from saw.engines.compile.compiler import WikiCompileEngine


# ── TC-COMP-02: compile_full ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_compile_full_creates_pages(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    result = await engine.compile_full()

    # 3 source files → 3 pages created
    assert len(result.pages_created) == 3
    # index.md should have entries
    index_content = (engine.wiki_root / "index.md").read_text(encoding="utf-8")
    assert "ml" in index_content.lower()
    # log should have a compile entry
    log_content = (engine.wiki_root / "log.md").read_text(encoding="utf-8")
    assert "compile" in log_content.lower()


@pytest.mark.asyncio
async def test_compile_full_idempotent_pages_unchanged(tmp_vault: Path):
    """Second compile_full with same content → pages_updated (files exist,
    content re-compiled and overwritten)."""
    engine = WikiCompileEngine(vault_root=tmp_vault)
    first = await engine.compile_full()
    assert len(first.pages_created) == 3

    second = await engine.compile_full()
    # All content identical → pages_updated (files already exist)
    assert len(second.pages_updated) == 3
    assert len(second.pages_created) == 0


# ── TC-COMP-03: compile_incremental ──────────────────────────────────

@pytest.mark.asyncio
async def test_compile_incremental_updates_existing(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    await engine.compile_full()

    # Modify one source file
    (tmp_vault / "concepts" / "ml.md").write_text(
        "# Machine Learning Updated\n\nNew content here. " + "word " * 200,
        encoding="utf-8",
    )

    result = await engine.compile_incremental(["concepts/ml.md"])
    assert len(result.pages_updated) == 1
    assert "concepts/ml.md" in result.pages_updated[0]


@pytest.mark.asyncio
async def test_compile_incremental_skips_nonexistent(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    await engine.compile_full()

    result = await engine.compile_incremental(["nonexistent/file.md"])
    assert len(result.pages_created) == 0
    assert len(result.pages_updated) == 0


# ── TC-COMP-04: _content_hash dedup ─────────────────────────────────

def test_content_hash_same_content(tmp_vault: Path):
    """Two files with identical content produce the same hash → dedup."""
    # Create two files with identical content
    (tmp_vault / "dup1.md").write_text("# Duplicate\n\nSame content.", encoding="utf-8")
    (tmp_vault / "subdir").mkdir(exist_ok=True)
    (tmp_vault / "subdir" / "dup2.md").write_text("# Duplicate\n\nSame content.", encoding="utf-8")

    engine = WikiCompileEngine(vault_root=tmp_vault)
    h1 = engine._content_hash(tmp_vault / "dup1.md")
    h2 = engine._content_hash(tmp_vault / "subdir" / "dup2.md")
    assert h1 is not None
    assert h2 is not None
    assert h1 == h2


def test_content_hash_different_content(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    (tmp_vault / "a.md").write_text("Content A", encoding="utf-8")
    (tmp_vault / "b.md").write_text("Content B", encoding="utf-8")

    h1 = engine._content_hash(tmp_vault / "a.md")
    h2 = engine._content_hash(tmp_vault / "b.md")
    assert h1 != h2


def test_content_hash_none_on_empty(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    (tmp_vault / "empty.md").write_text("   \n\n  ", encoding="utf-8")
    h = engine._content_hash(tmp_vault / "empty.md")
    assert h is None


def test_content_hash_none_on_unreadable(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    h = engine._content_hash(tmp_vault / "nonexistent.md")
    assert h is None

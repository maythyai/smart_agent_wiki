"""TC-COMP-15: _cascade_update tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from saw.engines.compile.compiler import WikiCompileEngine


@pytest.mark.asyncio
async def test_cascade_update_logs_referencing_pages(tmp_vault: Path):
    """When page A is updated and page B references A via [[a]], the log
    should contain a Cascade entry listing B."""
    # Create two source files: A and B (B references A via wikilink)
    (tmp_vault / "concepts").mkdir(exist_ok=True)
    (tmp_vault / "concepts" / "alpha.md").write_text(
        "# Alpha\n\nAlpha is a concept. " + "word " * 100,
        encoding="utf-8",
    )
    (tmp_vault / "concepts" / "beta.md").write_text(
        "# Beta\n\nBeta references [[alpha]] here. " + "word " * 100,
        encoding="utf-8",
    )
    engine = WikiCompileEngine(vault_root=tmp_vault)
    await engine.compile_full()

    # Trigger cascade update for alpha
    engine._cascade_update("concepts/alpha.md")

    log_content = (engine.wiki_root / "log.md").read_text(encoding="utf-8")
    assert "Cascade" in log_content or "cascade" in log_content.lower()
    assert "beta" in log_content.lower()


@pytest.mark.asyncio
async def test_cascade_update_no_references(tmp_vault: Path):
    """When no page references the changed page, no cascade log is added."""
    (tmp_vault / "concepts").mkdir(exist_ok=True)
    (tmp_vault / "concepts" / "solo.md").write_text(
        "# Solo\n\n" + "content " * 50, encoding="utf-8"
    )
    engine = WikiCompileEngine(vault_root=tmp_vault)
    await engine.compile_full()

    log_before = (engine.wiki_root / "log.md").read_text(encoding="utf-8")
    engine._cascade_update("concepts/solo.md")
    log_after = (engine.wiki_root / "log.md").read_text(encoding="utf-8")
    # No new cascade entry should be appended
    assert log_after == log_before


@pytest.mark.asyncio
async def test_cascade_update_in_incremental(tmp_vault: Path):
    """compile_incremental should trigger cascade for changed pages."""
    (tmp_vault / "concepts").mkdir(exist_ok=True)
    (tmp_vault / "concepts" / "alpha.md").write_text(
        "# Alpha\n\nAlpha content. " + "word " * 100,
        encoding="utf-8",
    )
    (tmp_vault / "concepts" / "beta.md").write_text(
        "# Beta\n\nSee [[alpha]]. " + "word " * 100,
        encoding="utf-8",
    )
    engine = WikiCompileEngine(vault_root=tmp_vault)
    await engine.compile_full()

    # Modify alpha
    (tmp_vault / "concepts" / "alpha.md").write_text(
        "# Alpha Updated\n\nNew alpha content. " + "word " * 100,
        encoding="utf-8",
    )
    await engine.compile_incremental(["concepts/alpha.md"])

    log_content = (engine.wiki_root / "log.md").read_text(encoding="utf-8")
    assert "cascade" in log_content.lower()

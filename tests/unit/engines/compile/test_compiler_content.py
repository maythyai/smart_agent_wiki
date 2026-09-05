"""TC-COMP-08/09/10/12: _compile_content (LLM/rule/degraded) + _write_page."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from saw.engines.compile.compiler import WikiCompileEngine


# ── TC-COMP-09: _compile_content rule-based path (no LLM) ───────────

def test_compile_content_rule_based(tmp_vault: Path):
    """With no LLM, _compile_content produces rule-based output with title."""
    engine = WikiCompileEngine(vault_root=tmp_vault)
    raw = "# My Page\n\nSome body content here."
    result = engine._compile_content(raw, "My Page")
    assert "# My Page" in result
    # No degraded banner when no LLM is configured
    assert "Rule-based compile" not in result


def test_compile_content_rule_based_adds_title(tmp_vault: Path):
    """When raw has no H1, rule-based compile prepends the title."""
    engine = WikiCompileEngine(vault_root=tmp_vault)
    raw = "Just body content without heading."
    result = engine._compile_content(raw, "Generated Title")
    assert result.startswith("# Generated Title")


# ── TC-COMP-08: _compile_content LLM path ────────────────────────────

def test_compile_content_llm_path(tmp_vault: Path):
    """With a mock LLM that returns >100 chars, LLM output is used."""
    mock_llm = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = (
        "# LLM Title\n\n" + "Overview paragraph. " * 15 + "\n\n## Section\n\nBody."
    )
    mock_llm.complete.return_value = response
    engine = WikiCompileEngine(vault_root=tmp_vault, llm_router=mock_llm)

    result = engine._compile_content("raw content", "LLM Title")
    assert "LLM Title" in result
    mock_llm.complete.assert_called_once()


# ── TC-COMP-10: _compile_content LLM failure → degraded ──────────────

def test_compile_content_llm_failure_degraded(tmp_vault: Path):
    """When LLM raises, _compile_content falls back to rule-based with
    a visible degradation banner."""
    mock_llm = MagicMock()
    mock_llm.complete.side_effect = RuntimeError("LLM timeout")
    engine = WikiCompileEngine(vault_root=tmp_vault, llm_router=mock_llm)

    raw = "# Source Title\n\nBody content here."
    result = engine._compile_content(raw, "Source Title")
    # Should contain the degradation banner
    assert "Rule-based compile" in result or "⚠️" in result


def test_compile_content_llm_short_output_falls_back(tmp_vault: Path):
    """When LLM returns <100 chars, falls back to rule-based."""
    mock_llm = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = "too short"
    mock_llm.complete.return_value = response
    engine = WikiCompileEngine(vault_root=tmp_vault, llm_router=mock_llm)

    raw = "# Title\n\nBody."
    result = engine._compile_content(raw, "Title")
    # LLM output was too short → rule-based fallback (should have the H1)
    assert "# Title" in result


# ── TC-COMP-12: _write_page ──────────────────────────────────────────

def test_write_page_metadata_comment(tmp_vault: Path):
    """_write_page writes the page with a metadata HTML comment."""
    from saw.domain.wiki_compile import (
        WikiCompilePage,
        WikiConfidence,
        WikiPageMetadata,
        WikiPageType,
        WikiSource,
    )

    engine = WikiCompileEngine(vault_root=tmp_vault)
    engine.wiki_root.mkdir(parents=True, exist_ok=True)

    page = WikiCompilePage(
        filename="concepts/test.md",
        title="Test Page",
        content="# Test Page\n\nBody.",
        metadata=WikiPageMetadata(
            type=WikiPageType.CONCEPT,
            confidence=WikiConfidence.HIGH,
            sources=[WikiSource(page_id="src.md", title="Source")],
            topic="concepts",
        ),
    )
    engine._write_page(page)

    written = (engine.wiki_root / "concepts" / "test.md").read_text(encoding="utf-8")
    assert "<!-- metadata:" in written
    assert "type: concept" in written
    assert "confidence: high" in written
    assert "topic: concepts" in written


# ── _compile_source ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_compile_source_short_content_skipped(tmp_vault: Path):
    """Source with <50 chars of content is skipped."""
    (tmp_vault / "short.md").write_text("# x\n\nhi", encoding="utf-8")
    engine = WikiCompileEngine(vault_root=tmp_vault)
    result = await engine._compile_source(tmp_vault / "short.md", "general")
    assert result is None


@pytest.mark.asyncio
async def test_compile_source_produces_page(tmp_vault: Path):
    (tmp_vault / "concepts").mkdir(exist_ok=True)
    (tmp_vault / "concepts" / "test.md").write_text(
        "# Test\n\n" + "content " * 50, encoding="utf-8"
    )
    engine = WikiCompileEngine(vault_root=tmp_vault)
    page = await engine._compile_source(tmp_vault / "concepts" / "test.md", "concepts")
    assert page is not None
    assert page.title == "Test"
    assert page.filename == "concepts/test.md"

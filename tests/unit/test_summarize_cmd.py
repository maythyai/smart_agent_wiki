"""Summarize CLI tests — T-F-L-3 (AC-SUM-1)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner


def _make_wiki(root: Path) -> Path:
    wiki = root / "wiki" / "concepts"
    wiki.mkdir(parents=True)
    (root / ".saw").mkdir(parents=True)
    (root / ".saw" / "config.yaml").write_text("llm:\n  model: test\n")
    (wiki / "alpha.md").write_text(
        "---\ntitle: Alpha\ntags: [ml]\n---\n# Alpha\nAlpha is about machine learning.\n"
    )
    return root


def test_summarize_no_llm_exits_1(tmp_path):
    """AC-SUM-1: no LLM configured → exit 1 (no silent fallback)."""
    from saw.drivers.cli.main import app

    _make_wiki(tmp_path)
    with patch("saw.config.settings.detect_tier", return_value=0):
        res = CliRunner().invoke(app, ["summarize", "alpha", "--path", str(tmp_path)])
    assert res.exit_code == 1
    assert "LLM unavailable" in res.output


def test_summarize_online_produces_nonempty(tmp_path):
    """AC-SUM-1: with an LLM, summarize returns a non-empty summary."""
    from saw.drivers.cli.main import app

    _make_wiki(tmp_path)
    fake_llm = MagicMock()
    fake_llm.answer_query.return_value = "- Alpha is about ML\n- Key concepts follow."

    import saw.domain.value_objects as vv

    with (
        patch("saw.config.settings.detect_tier", return_value=vv.CapabilityTier.LIGHTWEIGHT),
        patch("saw.adapters.llm.router.LLMRouter", return_value=fake_llm),
    ):
        res = CliRunner().invoke(app, ["summarize", "alpha", "--path", str(tmp_path)])
    assert res.exit_code == 0, res.output
    assert "Alpha is about ML" in res.output
    fake_llm.answer_query.assert_called_once()


def test_summarize_unknown_page_exits_1(tmp_path):
    from saw.drivers.cli.main import app

    _make_wiki(tmp_path)
    res = CliRunner().invoke(app, ["summarize", "nope", "--path", str(tmp_path)])
    assert res.exit_code == 1

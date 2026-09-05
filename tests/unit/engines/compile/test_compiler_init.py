"""TC-COMP-01/19/20: initialize / property / concept_graph tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from saw.engines.compile.compiler import WikiCompileEngine


# ── TC-COMP-01: initialize creates _wiki/ + index.md + log.md ────────

@pytest.mark.asyncio
async def test_initialize_creates_wiki_dir(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    assert not engine.is_initialized

    await engine.initialize()

    assert engine.is_initialized
    assert (engine.wiki_root).exists()
    assert (engine.wiki_root / "index.md").exists()
    assert (engine.wiki_root / "log.md").exists()

    # log.md should contain an "initialize" entry
    log_content = (engine.wiki_root / "log.md").read_text(encoding="utf-8")
    assert "initialize" in log_content.lower()


# ── TC-COMP-19: is_initialized / wiki_root property ──────────────────

def test_is_initialized_false_before_init(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    assert engine.is_initialized is False


def test_is_initialized_true_after_init(tmp_vault: Path, engine):
    import asyncio

    asyncio.run(engine.initialize())
    assert engine.is_initialized is True


def test_wiki_root_property(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    assert engine.wiki_root == tmp_vault / "_wiki"


# ── TC-COMP-20: attach_concept_graph + _rebuild_concept_graph ────────

def test_attach_concept_graph(engine):
    from unittest.mock import MagicMock

    mock_graph = MagicMock()
    mock_graph.rebuild_from_wiki.return_value = 5
    engine.attach_concept_graph(mock_graph)

    assert engine._concept_graph is mock_graph

    # _rebuild_concept_graph should call rebuild_from_wiki
    result = engine._rebuild_concept_graph()
    assert result == 5
    mock_graph.rebuild_from_wiki.assert_called_once()


def test_rebuild_concept_graph_noop_without_graph(engine):
    """When no concept graph is attached, _rebuild_concept_graph is a no-op."""
    assert engine._concept_graph is None
    result = engine._rebuild_concept_graph()
    assert result == 0


def test_rebuild_concept_graph_handles_exception(engine):
    """Exception during rebuild is caught and returns 0."""
    from unittest.mock import MagicMock

    mock_graph = MagicMock()
    mock_graph.rebuild_from_wiki.side_effect = RuntimeError("boom")
    engine.attach_concept_graph(mock_graph)

    result = engine._rebuild_concept_graph()
    assert result == 0

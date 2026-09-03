"""Query engine mode-dispatch + helpers coverage — T-F-J-3 (AC-COV-2).

Covers the non-keyword query paths (graph / compare / tree modes), the
layered-answer parser, citation extraction, and citation resolution that
were previously uncovered (engine.py 14%).
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from saw.engines.query.engine import QueryEngine, QueryResult


def _engine(**subs) -> QueryEngine:
    """Build a QueryEngine with mock sub-services + a real workspace_id."""
    return QueryEngine(
        search=subs.get("search", MagicMock()),
        compiler=subs.get("compiler", MagicMock()),
        graph=subs.get("graph", MagicMock()),
        compare_engine=subs.get("compare", MagicMock()),
        tree_mode=subs.get("tree_mode", MagicMock()),
        llm=subs.get("llm"),
        claims_repo=subs.get("claims_repo", MagicMock()),
        wiki_repo=subs.get("wiki_repo", MagicMock()),
        conn=subs.get("conn", MagicMock()),
        workspace_id=subs.get("workspace_id", "default"),
    )


# ── mode dispatch ────────────────────────────────────────────────────

def test_query_empty_returns_no_question():
    e = _engine()
    r = e.query("")
    assert "No question" in r.answer


def test_query_unknown_mode():
    e = _engine()
    r = e.query("x", mode="bogus")
    assert "Unknown mode" in r.answer


def test_query_auto_no_llm_falls_back_to_keyword():
    """auto mode + no LLM → keyword search path."""
    fts = MagicMock()
    fts_result = MagicMock(claim_uuids=[], contents=[], scores=[], total=0)
    fts.search.return_value = fts_result
    e = _engine(search=fts, wiki_repo=MagicMock(read=lambda s: None))
    r = e.query("hello", mode="auto")
    assert r.mode == "search"


def test_query_auto_with_llm_calls_nl_path():
    """auto mode + LLM → nl_query path; LLM failure falls back to keyword."""
    fts = MagicMock()
    fts_result = MagicMock(claim_uuids=[], contents=[], scores=[], total=0)
    fts.search.return_value = fts_result
    llm = MagicMock()
    llm.answer_query.side_effect = RuntimeError("boom")
    e = _engine(search=fts, llm=llm, wiki_repo=MagicMock(read=lambda s: None))
    r = e.query("hello", mode="auto")
    assert r.mode == "nl_query_fallback"
    assert r.meta.get("nl_fallback") is True


# ── graph mode ──────────────────────────────────────────────────────

def test_graph_query_finds_entities():
    graph = MagicMock()
    node = MagicMock()
    node.name = "Python"
    edge = MagicMock()
    edge.source_uuid = "a"
    edge.relation_type = "related"
    edge.target_uuid = "b"
    empty = MagicMock(nodes=[], edges=[])
    found = MagicMock(nodes=[node], edges=[edge])
    # 1st traverse = word lookup (must have nodes to set entity_name);
    # 2nd traverse = the real max_depth=3 traversal.
    graph.traverse.side_effect = [found, found]
    e = _engine(graph=graph)
    r = e.query("Python", mode="graph")
    assert r.mode == "graph"
    assert any(s.get("entity_name") == "Python" for s in r.sources)


def test_graph_query_no_entities():
    graph = MagicMock()
    graph.traverse.return_value = MagicMock(nodes=[], edges=[])
    e = _engine(graph=graph)
    r = e.query("nothing", mode="graph")
    assert "No entities" in r.answer


# ── compare mode ────────────────────────────────────────────────────

def test_compare_query_needs_two_pages():
    e = _engine()
    r = e.query("solo", mode="compare")
    assert "Need at least 2" in r.answer


def test_compare_query_runs():
    comp = MagicMock()
    from saw.engines.query.compare import ComparisonResult
    claim = MagicMock(uuid="c1", content="shared")
    comp.compare.return_value = ComparisonResult(
        pages=["a", "b"], shared_claims=[claim], unique_claims={"a": [], "b": []},
        similarity=0.5,
    )
    e = _engine(compare=comp)
    r = e.query('a, b', mode="compare")
    assert r.mode == "compare"
    assert "Similarity" in r.answer


# ── tree mode ───────────────────────────────────────────────────────

def test_tree_query_no_sections():
    tm = MagicMock()
    tm.search.return_value = []
    e = _engine(tree_mode=tm)
    r = e.query("x", mode="tree")
    assert "No hierarchical structure" in r.answer


def test_tree_query_with_sections():
    tm = MagicMock()
    path = MagicMock()
    path.path = ["root", "child"]
    claim = MagicMock(uuid="c1", content="hello")
    path.claims = [claim]
    tm.search.return_value = [path]
    e = _engine(tree_mode=tm)
    r = e.query("x", mode="tree")
    assert r.mode == "tree"
    assert any(s.get("section_path") == "root > child" for s in r.sources)


# ── layered answer + citations helpers ──────────────────────────────

def test_parse_layered_answer():
    e = _engine()
    raw = "# Title\n\nSummary line.\n\n- bullet one\n- bullet two\n\nbody"
    layers = e._parse_layered_answer(raw, depth=4)
    assert layers["L1"] == "Title"
    assert "Summary" in layers["L2"]
    assert "bullet one" in layers["L3"]
    assert layers["L4"] == raw


def test_extract_citations():
    e = _engine()
    txt = "see [^claim:abc-123] and [^claim:xyz] and [^claim:abc-123]"
    cites = e._extract_citations(txt)
    assert set(cites) == {"abc-123", "xyz"}


def test_resolve_citations_from_compiled_and_repo():
    claims_repo = MagicMock()
    claim = MagicMock(uuid="c1", content="hi", confidence=MagicMock(name="HIGH"))
    claim.confidence.name.lower.return_value = "high"
    claim.source_uuid = "s1"
    claim.page_number = 1
    claim.line_number = 2
    claims_repo.get_by_id.return_value = claim
    e = _engine(claims_repo=claims_repo)
    compiled = [{"claim_uuid": "c1", "content": "x"}]
    out = e._resolve_citations(["c1", "c2"], compiled)
    # c1 from compiled, c2 from repo
    assert any(s.get("claim_uuid") == "c1" for s in out)

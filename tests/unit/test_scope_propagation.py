"""Scope-propagation cleanup tests — T-F-K-2 (AC-ARCH-1).

Verifies QueryEngine propagates workspace_id via the public ``set_workspace_id``
setter (not private-attribute setattr), and that the sub-services receive it.
"""
from __future__ import annotations

from unittest.mock import MagicMock


def test_sub_services_have_public_set_workspace_id():
    """AC-ARCH-1: tree_mode / compiler / graph expose set_workspace_id."""
    from saw.engines.query.tree_mode import TreeModeSearch
    from saw.engines.query.compiler import ContextCompiler
    from saw.engines.query.graph_traverse import GraphTraverse

    import sqlite3

    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    tree = TreeModeSearch(MagicMock(), MagicMock(), conn)
    compiler = ContextCompiler(MagicMock(), MagicMock(), MagicMock(), conn)
    graph = GraphTraverse(conn)
    for sub in (tree, compiler, graph):
        assert callable(getattr(sub, "set_workspace_id", None))
    conn.close()


def test_query_engine_propagates_scope_via_setter():
    """AC-ARCH-1: QueryEngine calls set_workspace_id on sub-services."""
    from saw.engines.query.engine import QueryEngine

    calls = []

    class _Sub:
        def set_workspace_id(self, ws):
            calls.append(ws)

    engine = QueryEngine(
        search=_Sub(), compiler=_Sub(), graph=_Sub(),
        compare_engine=_Sub(), tree_mode=_Sub(),
        llm=None, claims_repo=MagicMock(), wiki_repo=MagicMock(),
        conn=MagicMock(), workspace_id="alpha",
    )
    assert engine._workspace_id == "alpha"
    # 3 scoped sub-services (tree_mode / compiler / graph) each called once.
    assert calls.count("alpha") == 3


def test_no_setattr_private_attribute_in_engine():
    """AC-ARCH-1: engine.py no longer uses setattr to poke sub-service privates."""
    from pathlib import Path

    src = Path("src/saw/engines/query/engine.py").read_text()
    assert "setattr(_sub" not in src, "engine still uses setattr on sub-services"

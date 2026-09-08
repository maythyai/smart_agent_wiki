"""AUDIT-F-08 / W1: Sub-service effective_workspace_id contextvar test.

Verifies that TreeModeSearch, ContextCompiler, and GraphTraverse read the
per-request ``workspace_id_var`` contextvar (not just their instance-level
``_workspace_id`` set at construction time). This is the regression test
for the cross-workspace data leakage bug (W1 from v1.18.0 retro).

**Before the fix**: sub-services used ``self._workspace_id`` (construction-
time ``"default"``), so a web request with ``X-Workspace-Id: ws-A`` would
get ws-A's claims from QueryEngine (which has ``effective_workspace_id``)
but ``"default"``'s claims from tree_mode/compiler/graph_traverse (which
did not).  Same request → inconsistent data sources → cross-ws leakage.

**After the fix**: all three sub-services have ``effective_workspace_id``
that reads the contextvar first, falling back to ``_workspace_id`` for
CLI/scripts/tests without middleware.
"""
from __future__ import annotations

import pytest

from saw.drivers.cli.commands.smoke_harness import build_smoke_context
from saw.drivers.web.middleware.workspace import workspace_id_var


@pytest.fixture
def ctx():
    """Fresh smoke context with real (non-mock) sub-services."""
    c = build_smoke_context()
    yield c
    c.close()


def _ingest_and_split_workspaces(ctx) -> list[str]:
    """Ingest fixture content and split claims across ws-A / ws-B."""
    from saw.drivers.cli.commands.smoke_harness import _ingest_fixture

    _ingest_fixture(ctx)
    rows = ctx.conn.execute(
        "SELECT uuid FROM claim WHERE deleted_at IS NULL"
    ).fetchall()
    uuids = [r[0] for r in rows]
    assert len(uuids) >= 2, "fixture produced too few claims for split test"
    midpoint = len(uuids) // 2
    for uuid in uuids[:midpoint]:
        ctx.claims_repo.set_workspace(uuid, "ws-A")
    for uuid in uuids[midpoint:]:
        ctx.claims_repo.set_workspace(uuid, "ws-B")
    return uuids


# ── Unit: effective_workspace_id reads contextvar ─────────────────────


def test_tree_mode_effective_workspace_reads_contextvar(ctx):
    """TreeModeSearch.effective_workspace_id reads contextvar."""
    tree = ctx.query_engine._tree_mode
    token = workspace_id_var.set("ws-A")
    try:
        assert tree.effective_workspace_id == "ws-A"
    finally:
        workspace_id_var.reset(token)
    # Without contextvar, falls back to instance-level "default"
    assert tree.effective_workspace_id == "default"


def test_compiler_effective_workspace_reads_contextvar(ctx):
    """ContextCompiler.effective_workspace_id reads contextvar."""
    compiler = ctx.query_engine._compiler
    token = workspace_id_var.set("ws-B")
    try:
        assert compiler.effective_workspace_id == "ws-B"
    finally:
        workspace_id_var.reset(token)
    assert compiler.effective_workspace_id == "default"


def test_graph_effective_workspace_reads_contextvar(ctx):
    """GraphTraverse.effective_workspace_id reads contextvar."""
    graph = ctx.query_engine._graph
    token = workspace_id_var.set("ws-A")
    try:
        assert graph.effective_workspace_id == "ws-A"
    finally:
        workspace_id_var.reset(token)
    assert graph.effective_workspace_id == "default"


# ── Integration: sub-services scope claims by contextvar ──────────────


def test_tree_mode_claims_scoped_by_contextvar(ctx):
    """TreeModeSearch claim lookups respect per-request workspace.

    With contextvar=ws-A, ws-A claims are visible and ws-B claims are not
    (and vice versa).  Before the fix, the sub-service always used the
    construction-time "default" workspace, leaking data across workspaces.
    """
    uuids = _ingest_and_split_workspaces(ctx)
    midpoint = len(uuids) // 2
    ws_a_uuid = uuids[0]
    ws_b_uuid = uuids[midpoint]
    tree = ctx.query_engine._tree_mode

    # contextvar = ws-A
    token = workspace_id_var.set("ws-A")
    try:
        ws = tree.effective_workspace_id
        claim_a = tree._claims_repo.get_by_id(ws_a_uuid, workspace_id=ws)
        claim_b = tree._claims_repo.get_by_id(ws_b_uuid, workspace_id=ws)
        assert claim_a is not None, "ws-A claim not found with ws-A contextvar"
        assert claim_b is None, "ws-B claim leaked into ws-A (W1 regression!)"
    finally:
        workspace_id_var.reset(token)

    # contextvar = ws-B
    token = workspace_id_var.set("ws-B")
    try:
        ws = tree.effective_workspace_id
        claim_b = tree._claims_repo.get_by_id(ws_b_uuid, workspace_id=ws)
        claim_a = tree._claims_repo.get_by_id(ws_a_uuid, workspace_id=ws)
        assert claim_b is not None, "ws-B claim not found with ws-B contextvar"
        assert claim_a is None, "ws-A claim leaked into ws-B (W1 regression!)"
    finally:
        workspace_id_var.reset(token)


def test_compiler_claims_scoped_by_contextvar(ctx):
    """ContextCompiler claim lookups respect per-request workspace."""
    uuids = _ingest_and_split_workspaces(ctx)
    midpoint = len(uuids) // 2
    ws_a_uuid = uuids[0]
    ws_b_uuid = uuids[midpoint]
    compiler = ctx.query_engine._compiler

    token = workspace_id_var.set("ws-A")
    try:
        ws = compiler.effective_workspace_id
        claim_a = compiler._claims_repo.get_by_id(ws_a_uuid, workspace_id=ws)
        claim_b = compiler._claims_repo.get_by_id(ws_b_uuid, workspace_id=ws)
        assert claim_a is not None
        assert claim_b is None, "ws-B claim leaked into ws-A via compiler"
    finally:
        workspace_id_var.reset(token)


# ── Integration: GraphTraverse reloads graph for correct workspace ────


def _insert_entities(ctx, workspace: str, names: list[str]) -> None:
    """Insert entities directly into the DB for a given workspace."""
    import json
    import uuid as uuid_mod

    for name in names:
        ctx.conn.execute(
            "INSERT INTO entity (uuid, name, aliases, entity_type, "
            "description, workspace_id) VALUES (?, ?, '[]', 'concept', ?, ?)",
            (str(uuid_mod.uuid4()), name, f"test entity {name}", workspace),
        )
    ctx.conn.commit()


def test_graph_traverse_scoped_by_contextvar(ctx):
    """GraphTraverse loads only the contextvar workspace's entities.

    With contextvar=ws-A, traverse returns ws-A entities; switching to
    ws-B reloads and returns ws-B entities.  Before the fix, the graph was
    loaded once at construction time for "default" and never reloaded for
    per-request workspaces.
    """
    _insert_entities(ctx, "ws-A", ["AlphaEntity", "AlphaNode"])
    _insert_entities(ctx, "ws-B", ["BetaEntity", "BetaNode"])
    graph = ctx.query_engine._graph

    # contextvar = ws-A → only ws-A entities visible
    token = workspace_id_var.set("ws-A")
    try:
        result = graph.traverse("AlphaEntity", mode="bfs", max_depth=1)
        node_names = {n.name for n in result.nodes}
        assert "AlphaEntity" in node_names, "ws-A entity not found with ws-A contextvar"
        assert "BetaEntity" not in node_names, "ws-B entity leaked into ws-A graph (W1 regression!)"
    finally:
        workspace_id_var.reset(token)

    # contextvar = ws-B → only ws-B entities visible
    token = workspace_id_var.set("ws-B")
    try:
        result = graph.traverse("BetaEntity", mode="bfs", max_depth=1)
        node_names = {n.name for n in result.nodes}
        assert "BetaEntity" in node_names, "ws-B entity not found with ws-B contextvar"
        assert "AlphaEntity" not in node_names, "ws-A entity leaked into ws-B graph (W1 regression!)"
    finally:
        workspace_id_var.reset(token)


# ── Integration: QueryEngine delegates consistently ──────────────────


def test_engine_and_subservices_consistent_workspace(ctx):
    """QueryEngine and all sub-services agree on the effective workspace.

    This is the core of the W1 fix: after setting contextvar, the engine
    AND all three sub-services must return the same effective_workspace_id.
    Before the fix, the engine read contextvar but sub-services did not.
    """
    engine = ctx.query_engine
    token = workspace_id_var.set("ws-consistency")
    try:
        ws = engine.effective_workspace_id
        assert ws == "ws-consistency"
        assert engine._tree_mode.effective_workspace_id == ws, (
            "tree_mode workspace diverges from engine (W1 bug!)"
        )
        assert engine._compiler.effective_workspace_id == ws, (
            "compiler workspace diverges from engine (W1 bug!)"
        )
        assert engine._graph.effective_workspace_id == ws, (
            "graph workspace diverges from engine (W1 bug!)"
        )
    finally:
        workspace_id_var.reset(token)

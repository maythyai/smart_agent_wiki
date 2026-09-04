"""Graph workspace isolation tests — T-F-K-1 (AC-WS-6).

Verifies that GraphTraverse only loads entities + relations belonging to
its workspace (relations require both endpoints in the same workspace).
"""
from __future__ import annotations

import sqlite3

from saw.db.migrations import apply_migrations
from saw.engines.query.graph_traverse import GraphTraverse


def _conn():
    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    return conn


def _seed(conn):
    """Seed: alpha has e1→e2; beta has e3; cross edge e1→e3 (must drop)."""
    conn.executemany(
        "INSERT OR IGNORE INTO entity (uuid, name, entity_type, workspace_id) "
        "VALUES (?, ?, ?, ?)",
        [
            ("e1", "Alpha1", "concept", "alpha"),
            ("e2", "Alpha2", "concept", "alpha"),
            ("e3", "Beta1", "concept", "beta"),
        ],
    )
    conn.executemany(
        "INSERT INTO entity_relation (source_uuid, target_uuid, relation_type, weight) "
        "VALUES (?, ?, ?, ?)",
        [
            ("e1", "e2", "related_to", 1.0),  # both alpha → visible in alpha
            ("e1", "e3", "cross_to_beta", 1.0),  # cross-ws → dropped everywhere
        ],
    )
    conn.commit()


def test_graph_traverse_isolates_workspace():
    """AC-WS-6: alpha graph has e1/e2 + e1→e2; NOT e3 nor the cross edge."""
    conn = _conn()
    _seed(conn)

    g_alpha = GraphTraverse(conn, workspace_id="alpha")
    res = g_alpha.traverse("Alpha1", mode="bfs", max_depth=2)
    names = {n.name for n in res.nodes}
    assert {"Alpha1", "Alpha2"} <= names
    assert "Beta1" not in names  # beta entity not loaded
    # The cross-ws edge (e1→e3) must not appear.
    assert all(e.target_uuid != "e3" for e in res.edges)
    # e1→e2 (both alpha) is present.
    assert any(e.source_uuid == "e1" and e.target_uuid == "e2" for e in res.edges)
    conn.close()


def test_graph_traverse_beta_excludes_alpha():
    """AC-WS-6: beta graph has only e3; no alpha entities/edges."""
    conn = _conn()
    _seed(conn)
    g_beta = GraphTraverse(conn, workspace_id="beta")
    res = g_beta.traverse("Beta1", mode="bfs", max_depth=2)
    assert {n.name for n in res.nodes} == {"Beta1"}
    assert res.edges == []  # cross edge dropped (e1 not in beta)
    conn.close()


def test_graph_traverse_default_workspace_compat():
    """Entities default to 'default' (backward compat)."""
    conn = _conn()
    conn.execute(
        "INSERT INTO entity (uuid, name, entity_type) VALUES (?, ?, ?)",
        ("d1", "DefaultEntity", "concept"),
    )
    conn.commit()
    g = GraphTraverse(conn, workspace_id="default")
    res = g.traverse("DefaultEntity", mode="bfs", max_depth=2)
    assert any(n.name == "DefaultEntity" for n in res.nodes)
    conn.close()


def test_graph_traverse_empty_workspace():
    """An empty workspace yields no nodes."""
    conn = _conn()
    _seed(conn)
    g = GraphTraverse(conn, workspace_id="gamma")
    res = g.traverse("Alpha1", mode="bfs", max_depth=2)
    assert res.nodes == []
    conn.close()

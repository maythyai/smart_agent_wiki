"""Tests for A2 community detection (v1.24.0) + D1 langfuse span (no-op)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


def _entity_graph_conn() -> sqlite3.Connection:
    """A claims DB with two distinct entity clusters (a-b-c | d-e)."""
    c = sqlite3.connect(":memory:")
    c.executescript(
        """CREATE TABLE entity (
    uuid TEXT PRIMARY KEY, name TEXT, aliases TEXT, entity_type TEXT,
    description TEXT, created_at TEXT, workspace_id TEXT DEFAULT 'default'
);
CREATE TABLE entity_relation (
    id INTEGER PRIMARY KEY AUTOINCREMENT, source_uuid TEXT, target_uuid TEXT,
    relation_type TEXT, weight REAL DEFAULT 1.0, created_at TEXT
);
"""
    )
    for u, n in [("a1","Alpha"),("a2","Bravo"),("a3","Charlie"),("b1","Delta"),("b2","Echo")]:
        c.execute(
            "INSERT INTO entity(uuid,name,aliases,entity_type,description,workspace_id) "
            "VALUES (?,?,?,?,?,?)",
            (u, n, "[]", "concept", n, "default"),
        )
    # cluster 1: a1-a2-a3 (triangle)
    for s, t in [("a1","a2"),("a2","a3"),("a1","a3")]:
        c.execute("INSERT INTO entity_relation(source_uuid,target_uuid,relation_type,weight) VALUES (?,?,?,?)", (s, t, "related", 1.0))
    # cluster 2: b1-b2 (edge, disconnected from cluster 1)
    c.execute("INSERT INTO entity_relation(source_uuid,target_uuid,relation_type,weight) VALUES (?,?,?,?)", ("b1","b2","related",1.0))
    return c


# ── A2 communities ──────────────────────────────────────────────────

def test_communities_finds_two_clusters():
    """GraphTraverse.communities() detects the two disconnected clusters."""
    from saw.engines.query.graph_traverse import GraphTraverse
    gt = GraphTraverse(_entity_graph_conn())
    comms = gt.communities(min_size=2)
    assert len(comms) == 2
    # cluster of 3 + cluster of 2
    sizes = sorted(c["size"] for c in comms)
    assert sizes == [2, 3]
    # all members are entity names
    all_names = {n for c in comms for n in c["members"]}
    assert {"Alpha","Bravo","Charlie","Delta","Echo"} <= all_names


def test_communities_min_size_filters_singletons():
    """A singleton cluster (if any) is dropped below min_size."""
    from saw.engines.query.graph_traverse import GraphTraverse
    c = _entity_graph_conn()
    c.execute("INSERT INTO entity(uuid,name,aliases,entity_type,description,workspace_id) VALUES ('x1','Xray','[]','concept','xray','default')")
    gt = GraphTraverse(c)
    comms = gt.communities(min_size=2)
    assert all(comm["size"] >= 2 for comm in comms)
    assert not any("Xray" in comm["members"] for comm in comms)


def test_community_of_locates_entity_cluster():
    """community_of() returns the cluster containing the named entity."""
    from saw.engines.query.graph_traverse import GraphTraverse
    gt = GraphTraverse(_entity_graph_conn())
    res = gt.community_of("Alpha")
    assert res is not None
    assert res["entity"] == "Alpha"
    assert res["size"] == 3
    assert "Bravo" in res["members"] and "Charlie" in res["members"]


def test_community_of_unknown_entity():
    from saw.engines.query.graph_traverse import GraphTraverse
    gt = GraphTraverse(_entity_graph_conn())
    assert gt.community_of("Nonexistent") is None


def test_communities_empty_graph():
    from saw.engines.query.graph_traverse import GraphTraverse
    c = sqlite3.connect(":memory:")
    c.executescript("CREATE TABLE entity (uuid TEXT PRIMARY KEY, name TEXT, aliases TEXT, entity_type TEXT, description TEXT, created_at TEXT, workspace_id TEXT DEFAULT 'default'); CREATE TABLE entity_relation (id INTEGER PRIMARY KEY, source_uuid TEXT, target_uuid TEXT, relation_type TEXT, weight REAL, created_at TEXT);")
    gt = GraphTraverse(c)
    assert gt.communities() == []


# ── D1 langfuse_span (no-op path) ───────────────────────────────────

def test_langfuse_span_noop_without_client():
    """D1: langfuse_span is a transparent no-op when Langfuse isn't configured."""
    from saw.drivers.web.middleware.observability import langfuse_span, _langfuse_client
    _langfuse_client.init(None)  # ensure no client
    with langfuse_span("test-span") as span:
        assert span is None  # no-op yields None
    # must not raise even with metadata
    with langfuse_span("x", metadata={"k": "v"}) as s:
        assert s is None

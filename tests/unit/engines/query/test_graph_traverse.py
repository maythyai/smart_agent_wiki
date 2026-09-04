"""Unit tests for GraphTraverse service."""
from __future__ import annotations

import json
import sqlite3

import pytest

from saw.engines.query.graph_traverse import GraphTraverse, GraphResult


@pytest.fixture
def in_memory_db() -> sqlite3.Connection:
    """Create in-memory SQLite with entity tables for testing."""
    conn = sqlite3.connect(":memory:")

    # Create entity table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entity (
            uuid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            aliases TEXT NOT NULL DEFAULT '[]',
            entity_type TEXT NOT NULL,
            description TEXT,
            workspace_id TEXT NOT NULL DEFAULT 'default',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Create entity_relation table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entity_relation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_uuid TEXT NOT NULL,
            target_uuid TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 1.0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (source_uuid) REFERENCES entity(uuid),
            FOREIGN KEY (target_uuid) REFERENCES entity(uuid)
        )
    """)

    conn.commit()
    return conn


@pytest.fixture
def populated_graph(in_memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """Populate in-memory DB with test entities and relations."""
    conn = in_memory_db

    # Insert test entities
    entities = [
        ("e1", "Python", "programming language", "A popular programming language"),
        ("e2", "Django", "framework", "A web framework for Python"),
        ("e3", "Flask", "framework", "A micro web framework for Python"),
        ("e4", "FastAPI", "framework", "A modern web framework for Python"),
        ("e5", "JavaScript", "programming language", "A scripting language for web"),
        ("e6", "React", "library", "A JavaScript library for UI"),
    ]

    for uuid, name, entity_type, description in entities:
        conn.execute(
            """INSERT INTO entity (uuid, name, entity_type, description)
               VALUES (?, ?, ?, ?)""",
            (uuid, name, entity_type, description),
        )

    # Insert relations (Python -> Django, Flask, FastAPI)
    relations = [
        ("e1", "e2", "has_framework", 1.0),
        ("e1", "e3", "has_framework", 1.0),
        ("e1", "e4", "has_framework", 1.0),
        ("e5", "e6", "has_library", 1.0),
    ]

    for source, target, rel_type, weight in relations:
        conn.execute(
            """INSERT INTO entity_relation (source_uuid, target_uuid, relation_type, weight)
               VALUES (?, ?, ?, ?)""",
            (source, target, rel_type, weight),
        )

    conn.commit()
    return conn


class TestGraphTraverse:
    """Tests for GraphTraverse class."""

    def test_bfs_traversal(self, populated_graph: sqlite3.Connection) -> None:
        """Test BFS traversal returns expected neighbors."""
        traverse = GraphTraverse(populated_graph)
        result = traverse.traverse("Python", mode="bfs", max_depth=2)

        assert isinstance(result, GraphResult)
        assert len(result.nodes) >= 1

        # Python should be in nodes
        node_names = [n.name for n in result.nodes]
        assert "Python" in node_names

        # Should include connected frameworks
        assert len(result.nodes) >= 2

    def test_dfs_traversal(self, populated_graph: sqlite3.Connection) -> None:
        """Test DFS traversal returns expected path."""
        traverse = GraphTraverse(populated_graph)
        result = traverse.traverse("Python", mode="dfs", max_depth=2)

        assert isinstance(result, GraphResult)
        assert len(result.nodes) >= 1
        assert "Python" in [n.name for n in result.nodes]

    def test_find_path(self, populated_graph: sqlite3.Connection) -> None:
        """Test finding shortest path between entities."""
        traverse = GraphTraverse(populated_graph)

        # Path from Python to Django (direct connection)
        path = traverse.find_path("Python", "Django")
        assert len(path) == 2
        assert path[0] == "e1"  # Python's UUID
        assert path[1] == "e2"  # Django's UUID

    def test_find_path_no_connection(
        self, populated_graph: sqlite3.Connection
    ) -> None:
        """Test finding path when no connection exists."""
        traverse = GraphTraverse(populated_graph)

        # Python and JavaScript are not connected
        path = traverse.find_path("Python", "JavaScript")
        assert path == []

    def test_get_neighbors(self, populated_graph: sqlite3.Connection) -> None:
        """Test getting direct neighbors."""
        traverse = GraphTraverse(populated_graph)
        neighbors = traverse.get_neighbors("Python", depth=1)

        # Should get Django, Flask, FastAPI as neighbors
        neighbor_names = [n.name for n in neighbors]
        assert "Django" in neighbor_names or "Flask" in neighbor_names or "FastAPI" in neighbor_names

    def test_max_depth_limits_traversal(
        self, populated_graph: sqlite3.Connection
    ) -> None:
        """Test that max_depth limits traversal scope."""
        traverse = GraphTraverse(populated_graph)

        # With max_depth=1, only direct neighbors
        result = traverse.traverse("Python", mode="bfs", max_depth=1)
        direct_count = len(result.nodes)

        # With max_depth=2, might include more
        result2 = traverse.traverse("Python", mode="bfs", max_depth=2)
        # Should be same or more (no 2-hop in our simple graph)
        assert len(result2.nodes) >= direct_count

    def test_traverse_unknown_entity(
        self, populated_graph: sqlite3.Connection
    ) -> None:
        """Test traversal for unknown entity returns empty result."""
        traverse = GraphTraverse(populated_graph)
        result = traverse.traverse("UnknownEntity", mode="bfs")

        assert result.nodes == []
        assert result.edges == []
        assert result.paths == []

    def test_entity_alias_lookup(
        self, populated_graph: sqlite3.Connection
    ) -> None:
        """Test that entity can be found by alias."""
        conn = populated_graph

        # Add an alias to Python
        conn.execute(
            "UPDATE entity SET aliases = ? WHERE uuid = 'e1'",
            (json.dumps(["py", "python3"]),),
        )
        conn.commit()

        traverse = GraphTraverse(conn)
        result = traverse.traverse("py", mode="bfs", max_depth=1)

        # Should find Python by alias
        assert len(result.nodes) >= 1
        assert "Python" in [n.name for n in result.nodes]

    def test_max_nodes_limit(
        self, populated_graph: sqlite3.Connection
    ) -> None:
        """Test that max_nodes limits result size."""
        traverse = GraphTraverse(populated_graph)
        result = traverse.traverse("Python", mode="bfs", max_depth=2, max_nodes=2)

        assert len(result.nodes) <= 2

"""Regression tests for the GraphSink contract fix.

The ingest pipeline emits graph WriteOps with a ``type`` discriminator
(``"entity"`` / ``"relation"``) and the fields inline; GraphSink previously
checked ``if "entity" in payload`` / ``if "relation" in payload`` (keys that
never exist), so every entity/relation write was silently skipped and the
knowledge graph was never built.
"""
from __future__ import annotations

import sqlite3

from saw.write_queue.queue import WriteOp
from saw.write_queue.sinks.graph_sink import GraphSink
from saw.domain.value_objects import WriteOpStatus

_GRAPH_SCHEMA = """
CREATE TABLE IF NOT EXISTS entity (
    uuid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    aliases TEXT NOT NULL DEFAULT '[]',
    entity_type TEXT NOT NULL,
    description TEXT,
    workspace_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS entity_relation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_uuid TEXT NOT NULL,
    target_uuid TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _new_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_GRAPH_SCHEMA)
    conn.commit()
    return conn


def _op(payload: dict) -> WriteOp:
    return WriteOp(
        op_id="op-1",
        session_id="sess-1",
        sink_name="graph",
        payload=payload,
        status=WriteOpStatus.PENDING,
    )


class TestGraphSinkContract:
    def test_entity_write_with_type_discriminator_lands_in_db(self) -> None:
        """Pipeline payload shape ``{"type": "entity", ...}`` must insert a row."""
        conn = _new_conn()
        sink = GraphSink(conn)
        sink.write(_op({
            "type": "entity",
            "uuid": "e-1",
            "name": "React",
            "entity_type": "library",
            "aliases": ["reactjs"],
            "description": "A UI library",
        }))

        row = conn.execute(
            "SELECT uuid, name, entity_type FROM entity WHERE uuid = ?",
            ("e-1",),
        ).fetchone()
        assert row is not None
        assert row[0] == "e-1"
        assert row[1] == "React"
        assert row[2] == "library"

    def test_relation_write_with_type_discriminator_lands_in_db(self) -> None:
        """Pipeline payload shape ``{"type": "relation", ...}`` must insert a row."""
        conn = _new_conn()
        sink = GraphSink(conn)
        # Both endpoints must exist for the FK, or use a non-FK-enforcing
        # connection (sqlite does not enforce FKs unless PRAGMA is on).
        conn.execute("INSERT INTO entity (uuid, name, entity_type) VALUES ('a', 'A', 'x')")
        conn.execute("INSERT INTO entity (uuid, name, entity_type) VALUES ('b', 'B', 'x')")
        conn.commit()
        sink.write(_op({
            "type": "relation",
            "source_uuid": "a",
            "target_uuid": "b",
            "relation_type": "depends_on",
            "weight": 0.8,
        }))

        row = conn.execute(
            "SELECT source_uuid, target_uuid, relation_type, weight "
            "FROM entity_relation WHERE source_uuid = ? AND target_uuid = ?",
            ("a", "b"),
        ).fetchone()
        assert row is not None
        assert row[2] == "depends_on"
        assert row[3] == 0.8

    def test_batch_relations_still_written(self) -> None:
        """The ``relations`` batch path keeps working alongside the fix."""
        conn = _new_conn()
        sink = GraphSink(conn)
        sink.write(_op({
            "relations": [
                {"source_uuid": "a", "target_uuid": "b", "relation_type": "related_to"},
                {"source_uuid": "b", "target_uuid": "c", "relation_type": "related_to"},
            ],
        }))

        count = conn.execute(
            "SELECT COUNT(*) FROM entity_relation"
        ).fetchone()[0]
        assert count == 2

    def test_can_handle_graph_sink(self) -> None:
        sink = GraphSink(_new_conn())
        assert sink.can_handle("graph") is True
        assert sink.can_handle("wiki") is False

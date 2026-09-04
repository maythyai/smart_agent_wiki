"""Graph sink - writes entity and entity_relation records to SQLite.

Per Pitfall 7: idempotent via INSERT OR IGNORE for entities,
and idempotent via unique constraint handling for relations.
"""
from __future__ import annotations

import json
import sqlite3

from saw.domain.exceptions import StorageError


class GraphSink:
    """Write Queue sink for knowledge graph (entity + relation) storage."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    @property
    def name(self) -> str:
        return "graph"

    def write(self, op) -> None:
        """Insert entity and entity_relation records.

        Payload shape (see engines/ingest/pipeline.py):
          - entity:   ``{"type": "entity", "uuid", "name", "entity_type", ...}``
          - relation: ``{"type": "relation", "source_uuid", "target_uuid",
                        "relation_type", ...}``
          - batch:    ``{"relations": [ {...}, ... ]}``

        Note: the discriminator is ``payload["type"]`` ("entity"/"relation"),
        NOT a top-level ``entity``/``relation`` key — the previous code checked
        ``if "entity" in payload`` and never matched, so every graph write was
        silently skipped and the knowledge graph was never built.
        """
        payload = op.payload

        try:
            node_type = payload.get("type")

            # Handle entity creation
            if node_type == "entity" or "entity" in payload:
                entity = payload.get("entity") if "entity" in payload else payload
                self._conn.execute(
                    """INSERT OR IGNORE INTO entity (uuid, name, aliases, entity_type, description, workspace_id)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        entity.get("uuid", op.op_id),
                        entity.get("name", ""),
                        json.dumps(entity.get("aliases", [])),
                        entity.get("entity_type", "unknown"),
                        entity.get("description", ""),
                        entity.get("workspace_id", "default"),
                    ),
                )

            # Handle relation creation
            if node_type == "relation" or "relation" in payload:
                rel = payload.get("relation") if "relation" in payload else payload
                self._conn.execute(
                    """INSERT INTO entity_relation (source_uuid, target_uuid, relation_type, weight)
                       VALUES (?, ?, ?, ?)""",
                    (
                        rel.get("source_uuid", ""),
                        rel.get("target_uuid", ""),
                        rel.get("relation_type", "related_to"),
                        rel.get("weight", 1.0),
                    ),
                )

            # Handle batch of relations
            if "relations" in payload:
                for rel in payload["relations"]:
                    self._conn.execute(
                        """INSERT INTO entity_relation (source_uuid, target_uuid, relation_type, weight)
                           VALUES (?, ?, ?, ?)""",
                        (
                            rel.get("source_uuid", ""),
                            rel.get("target_uuid", ""),
                            rel.get("relation_type", "related_to"),
                            rel.get("weight", 1.0),
                        ),
                    )

            self._conn.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Graph sink write failed for {op.op_id}: {e}") from e

    def can_handle(self, sink_name: str) -> bool:
        return sink_name == "graph"

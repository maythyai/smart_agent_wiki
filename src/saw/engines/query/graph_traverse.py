"""Graph traversal for entity relationships.

Per D-16: NetworkX BFS/DFS on SQLite-stored entity relationships.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

import networkx as nx

from saw.domain.entities import Entity, EntityRelation


@dataclass
class GraphResult:
    """Result of graph traversal."""
    nodes: list[Entity]
    edges: list[EntityRelation]
    paths: list[list[str]]


class GraphTraverse:
    """NetworkX-based graph traversal for entity relationships.

    Per D-16: Lightweight graph storage as JSONL edges in SQLite,
    loaded into NetworkX for traversal operations.
    """

    def __init__(self, conn: sqlite3.Connection, workspace_id: str = "default") -> None:
        """Initialize and load graph from database.

        Args:
            conn: SQLite connection with entity tables.
            workspace_id: Workspace scope (T-F-K-1, ADR-009). Only entities
                in this workspace (and relations whose both endpoints are
                in it) are loaded. Defaults to 'default' for single-wiki.
        """
        self._conn = conn
        self._workspace_id = workspace_id
        self._graph: nx.DiGraph = nx.DiGraph()
        self._entity_cache: dict[str, Entity] = {}
        self._relation_count: int = 0
        self._load_graph()

    def set_workspace_id(self, workspace_id: str) -> None:
        """Re-scope the graph and reload entities/relations (T-F-K-2)."""
        self._workspace_id = workspace_id
        self._graph = nx.DiGraph()
        self._entity_cache = {}
        self._relation_count = 0
        self._load_graph()

    def _load_graph(self) -> None:
        """Load entity_relation table into NetworkX graph.

        T-F-K-1 (ADR-009): scoped to ``self._workspace_id`` — only entities in
        that workspace are loaded, and only relations whose both endpoints
        belong to it (so cross-workspace edges never appear).
        """
        ws = self._workspace_id
        # Load entities in this workspace
        entity_rows = self._conn.execute(
            "SELECT uuid, name, aliases, entity_type, description "
            "FROM entity WHERE workspace_id = ?",
            (ws,),
        ).fetchall()

        for row in entity_rows:
            entity = Entity(
                uuid=row[0],
                name=row[1],
                aliases=self._parse_json_list(row[2]),
                entity_type=row[3],
                description=row[4] or "",
            )
            self._entity_cache[entity.uuid] = entity
            self._graph.add_node(entity.uuid, entity=entity)

        # Load relations whose both endpoints are in this workspace
        edge_rows = self._conn.execute(
            """SELECT er.source_uuid, er.target_uuid, er.relation_type, er.weight
               FROM entity_relation er
               JOIN entity s ON s.uuid = er.source_uuid
               JOIN entity t ON t.uuid = er.target_uuid
               WHERE s.workspace_id = ? AND t.workspace_id = ?""",
            (ws, ws),
        ).fetchall()

        for row in edge_rows:
            source_uuid = row[0]
            target_uuid = row[1]
            relation_type = row[2]
            weight = row[3] if row[3] else 1.0

            self._graph.add_edge(
                source_uuid, target_uuid,
                relation_type=relation_type,
                weight=weight,
            )

        self._relation_count = len(edge_rows)

    def _parse_json_list(self, json_str: str | None) -> list[str]:
        """Parse JSON list from string."""
        if not json_str:
            return []
        import json
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return []

    def traverse(
        self,
        entity_name: str,
        mode: str = "bfs",
        max_depth: int = 3,
        max_nodes: int = 50,
    ) -> GraphResult:
        """Traverse graph from a named entity.

        Args:
            entity_name: Name or alias of entity to start from.
            mode: "bfs" for breadth-first, "dfs" for depth-first.
            max_depth: Maximum traversal depth.
            max_nodes: Maximum nodes to include.

        Returns:
            GraphResult with nodes, edges, and paths.
        """
        # Find entity by name or alias
        entity = self._find_entity(entity_name)
        if entity is None:
            return GraphResult(nodes=[], edges=[], paths=[])

        entity_uuid = entity.uuid

        # Check if graph needs reload
        self._reload_if_stale()

        # Perform traversal
        try:
            if mode == "bfs":
                edges_gen = nx.bfs_edges(
                    self._graph, entity_uuid, depth_limit=max_depth
                )
            else:
                edges_gen = nx.dfs_edges(
                    self._graph, entity_uuid, depth_limit=max_depth
                )

            # Collect nodes and edges
            visited_nodes: set[str] = {entity_uuid}
            edges: list[EntityRelation] = []

            for source_uuid, target_uuid in edges_gen:
                if len(visited_nodes) >= max_nodes:
                    break

                visited_nodes.add(target_uuid)

                # Get edge data
                edge_data = self._graph.get_edge_data(source_uuid, target_uuid)
                if edge_data:
                    edge = EntityRelation(
                        source_uuid=source_uuid,
                        target_uuid=target_uuid,
                        relation_type=edge_data.get("relation_type", "related"),
                        weight=edge_data.get("weight", 1.0),
                    )
                    edges.append(edge)

            # Build node list
            nodes: list[Entity] = []
            for uuid in visited_nodes:
                if uuid in self._entity_cache:
                    nodes.append(self._entity_cache[uuid])

            # Build paths from root
            paths = self._find_paths_to_root(entity_uuid, visited_nodes)

            return GraphResult(nodes=nodes, edges=edges, paths=paths)

        except (nx.NetworkXError, nx.NodeNotFound):
            return GraphResult(nodes=[entity], edges=[], paths=[])

    def find_path(self, from_entity: str, to_entity: str) -> list[str]:
        """Find shortest path between two entities.

        Args:
            from_entity: Starting entity name.
            to_entity: Target entity name.

        Returns:
            List of entity UUIDs along the path, or empty if none.
        """
        from_e = self._find_entity(from_entity)
        to_e = self._find_entity(to_entity)

        if from_e is None or to_e is None:
            return []

        try:
            path = nx.shortest_path(
                self._graph, from_e.uuid, to_e.uuid
            )
            return path
        except (nx.NetworkXError, nx.NodeNotFound, nx.NetworkXNoPath):
            return []

    def get_neighbors(self, entity_name: str, depth: int = 1) -> list[Entity]:
        """Get directly connected entities.

        Args:
            entity_name: Entity name to find neighbors for.
            depth: How many hops (1 = direct neighbors only).

        Returns:
            List of neighboring Entity objects.
        """
        entity = self._find_entity(entity_name)
        if entity is None:
            return []

        self._reload_if_stale()

        neighbors: set[str] = set()

        if depth >= 1:
            # Direct successors and predecessors
            for succ in self._graph.successors(entity.uuid):
                neighbors.add(succ)
            for pred in self._graph.predecessors(entity.uuid):
                neighbors.add(pred)

        if depth >= 2:
            # Two-hop neighbors
            current_neighbors = set(neighbors)
            for neighbor_uuid in current_neighbors:
                for succ in self._graph.successors(neighbor_uuid):
                    if succ != entity.uuid:
                        neighbors.add(succ)
                for pred in self._graph.predecessors(neighbor_uuid):
                    if pred != entity.uuid:
                        neighbors.add(pred)

        # Convert to Entity objects
        result: list[Entity] = []
        for uuid in neighbors:
            if uuid in self._entity_cache:
                result.append(self._entity_cache[uuid])

        return result

    def _find_entity(self, name: str) -> Entity | None:
        """Find entity by name or alias.

        Args:
            name: Entity name or alias to search.

        Returns:
            Entity if found, None otherwise.
        """
        # Check cache first
        for entity in self._entity_cache.values():
            if entity.name.lower() == name.lower():
                return entity
            if name.lower() in [a.lower() for a in entity.aliases]:
                return entity

        # If not in cache, query database directly (T-F-K-1: scoped to ws)
        row = self._conn.execute(
            """SELECT uuid, name, aliases, entity_type, description
               FROM entity
               WHERE (LOWER(name) = ?
                  OR (aliases IS NOT NULL AND aliases LIKE ?))
                  AND workspace_id = ?
               LIMIT 1""",
            (name.lower(), f'%"{name.lower()}"%', self._workspace_id),
        ).fetchone()

        if row:
            entity = Entity(
                uuid=row[0],
                name=row[1],
                aliases=self._parse_json_list(row[2]),
                entity_type=row[3],
                description=row[4] or "",
            )
            self._entity_cache[entity.uuid] = entity
            return entity

        return None

    def _find_paths_to_root(
        self, root_uuid: str, visited: set[str]
    ) -> list[list[str]]:
        """Find paths from root to all visited nodes.

        Args:
            root_uuid: Starting entity UUID.
            visited: Set of visited node UUIDs.

        Returns:
            List of paths from root to each node.
        """
        paths: list[list[str]] = []

        for target_uuid in visited:
            if target_uuid == root_uuid:
                paths.append([root_uuid])
                continue

            try:
                path = nx.shortest_path(
                    self._graph, root_uuid, target_uuid
                )
                paths.append(path)
            except nx.NetworkXNoPath:
                pass

        return paths

    def _reload_if_stale(self) -> None:
        """Reload graph from DB if relation count has changed."""
        row = self._conn.execute(
            "SELECT COUNT(*) FROM entity_relation"
        ).fetchone()
        current_count = row[0] if row else 0

        if current_count != self._relation_count:
            self._graph = nx.DiGraph()
            self._entity_cache.clear()
            self._load_graph()

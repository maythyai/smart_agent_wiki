"""Graph API route for knowledge graph visualization.

Per D-10: GET /api/graph endpoint.
Per D-11: GET /api/graph/{entity} for entity subgraph.
Per D-12: Support BFS/DFS traversal with depth parameter.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

from saw.drivers.web.schemas.graph import (
    GraphEdge,
    GraphNode,
    GraphResponse,
    TraversalMode,
)

if TYPE_CHECKING:
    from saw.engines.query.engine import QueryEngine

router = APIRouter()


def get_query_engine(request: Request) -> QueryEngine:
    """Dependency: get QueryEngine from app.state."""
    return request.app.state.query


@router.get("/graph", response_model=GraphResponse)
async def get_graph(
    depth: int = Query(2, ge=1, le=5, description="Traversal depth"),
    mode: TraversalMode = Query(TraversalMode.bfs, description="BFS or DFS"),
    type: str | None = Query(None, description="Filter by entity type"),
    max_nodes: int = Query(50, ge=1, le=200, description="Max nodes"),
    engine: QueryEngine = Depends(get_query_engine),
) -> GraphResponse:
    """Get knowledge graph nodes and edges (per D-10).

    Builds graph from wiki pages and [[wiki-links]] for real connections.
    Falls back to entity graph if wiki is empty.

    Args:
        depth: Traversal depth (default 2, max 5).
        mode: Traversal mode - BFS or DFS (default BFS).
        type: Optional filter by entity type.
        max_nodes: Maximum nodes to return (default 50, max 200).
        engine: QueryEngine dependency.

    Returns:
        GraphResponse with nodes and edges for Cytoscape.js.
    """
    # Try wiki graph first (real [[wiki-links]])
    wiki = getattr(engine, "_wiki_repo", None) or getattr(engine, "wiki", None)
    if wiki is not None:
        from saw.engines.query.wiki_graph import WikiGraphBuilder

        builder = WikiGraphBuilder(wiki)
        wiki_nodes, wiki_edges = builder.build(max_nodes=max_nodes)

        # Apply type filter if specified
        if type is not None:
            wiki_nodes = [n for n in wiki_nodes if n.type == type]
            wiki_node_ids = {n.id for n in wiki_nodes}
            wiki_edges = [e for e in wiki_edges if e.source in wiki_node_ids and e.target in wiki_node_ids]

        if wiki_nodes:
            # Convert to GraphNode/GraphEdge
            nodes = [
                GraphNode(
                    id=n.id,
                    label=n.label,
                    type=n.type,
                    confidence=n.confidence,
                    description=n.description,
                )
                for n in wiki_nodes
            ]
            edges = [
                GraphEdge(
                    id=e.id,
                    source=e.source,
                    target=e.target,
                    type=e.type,
                    weight=e.weight,
                )
                for e in wiki_edges
            ]
            return GraphResponse(
                nodes=nodes,
                edges=edges,
                total_nodes=len(nodes),
                total_edges=len(edges),
            )

    # Fallback to entity graph if wiki is empty
    graph = engine._graph

    # Get all entities from cache
    all_entities = list(graph._entity_cache.values())

    # Apply type filter if specified
    if type is not None:
        all_entities = [e for e in all_entities if e.entity_type == type]

    # Limit nodes
    entities = all_entities[:max_nodes]

    # Build nodes
    nodes: list[GraphNode] = []
    for entity in entities:
        nodes.append(
            GraphNode(
                id=entity.uuid,
                label=entity.name,
                type=entity.entity_type,
                confidence=1,  # Default confidence for entities
                description=entity.description[:100] if entity.description else None,
            )
        )

    # Build edges from NetworkX graph
    edges: list[GraphEdge] = []
    entity_ids = {e.uuid for e in entities}
    edge_id = 0

    for source_uuid, target_uuid, data in graph._graph.edges(data=True):
        if source_uuid in entity_ids and target_uuid in entity_ids:
            edges.append(
                GraphEdge(
                    id=f"edge-{edge_id}",
                    source=source_uuid,
                    target=target_uuid,
                    type=data.get("relation_type", "related_to"),
                    weight=data.get("weight", 1.0),
                )
            )
            edge_id += 1

    return GraphResponse(
        nodes=nodes,
        edges=edges,
        total_nodes=len(nodes),
        total_edges=len(edges),
    )


@router.get("/graph/{entity}", response_model=GraphResponse)
async def get_entity_subgraph(
    entity: str = Path(..., description="Entity ID or name"),
    depth: int = Query(2, ge=1, le=5, description="Traversal depth"),
    mode: TraversalMode = Query(TraversalMode.bfs, description="BFS or DFS"),
    max_nodes: int = Query(50, ge=1, le=200, description="Max nodes"),
    engine: QueryEngine = Depends(get_query_engine),
) -> GraphResponse:
    """Get entity details and relationships (per D-11~12).

    Per D-12: Support BFS/DFS traversal with depth parameter.

    Args:
        entity: Entity ID or name to traverse from.
        depth: Traversal depth (default 2, max 5).
        mode: Traversal mode - BFS or DFS (default BFS).
        max_nodes: Maximum nodes to return (default 50, max 200).
        engine: QueryEngine dependency.

    Returns:
        GraphResponse with entity subgraph.

    Raises:
        HTTPException: 404 if entity not found.
    """
    graph = engine._graph

    # Traverse from entity
    result = graph.traverse(
        entity_name=entity,
        mode=mode.value,
        max_depth=depth,
        max_nodes=max_nodes,
    )

    if not result.nodes:
        raise HTTPException(status_code=404, detail=f"Entity '{entity}' not found")

    # Build nodes
    nodes: list[GraphNode] = []
    for node in result.nodes:
        nodes.append(
            GraphNode(
                id=node.uuid,
                label=node.name,
                type=node.entity_type,
                confidence=1,
                description=node.description[:100] if node.description else None,
            )
        )

    # Build edges
    edges: list[GraphEdge] = []
    for i, edge in enumerate(result.edges):
        edges.append(
            GraphEdge(
                id=f"edge-{i}",
                source=edge.source_uuid,
                target=edge.target_uuid,
                type=edge.relation_type,
                weight=edge.weight,
            )
        )

    return GraphResponse(
        nodes=nodes,
        edges=edges,
        total_nodes=len(nodes),
        total_edges=len(edges),
    )

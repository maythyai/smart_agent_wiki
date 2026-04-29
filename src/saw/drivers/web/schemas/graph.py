"""Graph API schemas for request/response validation.

Per D-10: GET /api/graph endpoint for knowledge graph.
Per D-11: GET /api/graph/{entity} for entity subgraph.
Per D-12: Support BFS/DFS traversal parameters.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TraversalMode(str, Enum):
    """Graph traversal mode (per D-12)."""

    bfs = "bfs"
    dfs = "dfs"


class GraphQuery(BaseModel):
    """Graph query parameters (per D-10~12)."""

    depth: int = Field(2, ge=1, le=5, description="Traversal depth")
    mode: TraversalMode = Field(TraversalMode.bfs, description="BFS or DFS")
    type: str | None = Field(None, description="Filter by entity type")
    max_nodes: int = Field(50, ge=1, le=200, description="Max nodes to return")


class GraphNode(BaseModel):
    """Node in knowledge graph for Cytoscape.js."""

    id: str
    label: str
    type: str
    confidence: int = Field(1, ge=1, le=4)
    description: str | None = None


class GraphEdge(BaseModel):
    """Edge in knowledge graph for Cytoscape.js."""

    id: str
    source: str
    target: str
    type: str
    weight: float = Field(1.0, ge=0.0)


class GraphResponse(BaseModel):
    """Graph data for Cytoscape.js visualization."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    total_nodes: int
    total_edges: int

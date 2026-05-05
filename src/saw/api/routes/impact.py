"""API routes for impact analysis."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

from saw.analysis.impact import analyze_impact, NodeNotFoundError
from saw.graph import get_graph


router = APIRouter(prefix="/api/impact", tags=["impact"])


class DirectionEnum(str, Enum):
    upstream = "upstream"
    downstream = "downstream"


class ImpactRequest(BaseModel):
    """Request body for impact analysis."""
    target: str = Field(..., description="Symbol name or UID to analyze")
    direction: DirectionEnum = Field(DirectionEnum.upstream, description="Analysis direction")
    max_depth: int = Field(3, ge=1, le=5, description="Maximum traversal depth")
    min_confidence: float = Field(0.8, ge=0.0, le=1.0, description="Minimum confidence")
    relation_types: Optional[List[str]] = Field(None, description="Filter by relation types")
    include_tests: bool = Field(False, description="Include test files")


class GraphNode(BaseModel):
    """Node for graph visualization."""
    id: str
    name: str
    type: str
    risk: str
    depth: Optional[int] = None
    confidence: Optional[float] = None


class GraphEdge(BaseModel):
    """Edge for graph visualization."""
    source: str
    target: str
    type: str
    confidence: float


class GraphData(BaseModel):
    """Graph data for D3.js visualization."""
    nodes: List[GraphNode]
    links: List[GraphEdge]
    summary: dict


@router.post("/")
async def analyze_impact_endpoint(request: ImpactRequest):
    """
    Analyze code modification impact.

    Returns nodes that will be affected by modifying the target.
    """
    graph = get_graph()

    try:
        result = analyze_impact(
            graph,
            request.target,
            request.direction.value,
            request.max_depth,
            request.min_confidence,
            request.relation_types,
            request.include_tests
        )
        return result

    except NodeNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Node '{request.target}' not found in knowledge graph"
        )


@router.get("/{target}")
async def get_impact(
    target: str,
    direction: DirectionEnum = DirectionEnum.upstream,
    max_depth: int = 3,
    min_confidence: float = 0.8
):
    """
    Get impact analysis for a target symbol.

    - **target**: Symbol name or UID
    - **direction**: 'upstream' (dependents) or 'downstream' (dependencies)
    - **max_depth**: Traversal depth limit (1-5)
    - **min_confidence**: Minimum confidence (0.0-1.0)
    """
    graph = get_graph()

    try:
        return analyze_impact(
            graph, target, direction.value if hasattr(direction, 'value') else direction,
            max_depth, min_confidence
        )
    except NodeNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Node '{target}' not found"
        )


@router.get("/{target}/graph", response_model=GraphData)
async def get_impact_graph(
    target: str,
    direction: DirectionEnum = DirectionEnum.upstream,
    max_depth: int = 3,
    min_confidence: float = 0.8
):
    """
    Get impact analysis as graph data for visualization.

    Returns nodes and edges in a format suitable for D3.js.
    """
    graph = get_graph()

    try:
        result = analyze_impact(
            graph, target, direction.value if hasattr(direction, 'value') else direction,
            max_depth, min_confidence
        )

        # Convert to D3.js format
        nodes = []
        edges = []

        # Add target node
        nodes.append(GraphNode(
            id=result["target_node"]["uid"],
            name=result["target"],
            type="target",
            risk="TARGET"
        ))

        # Add impact nodes
        for impact in result["impacts"]:
            nodes.append(GraphNode(
                id=impact["uid"],
                name=impact["name"],
                type=impact["kind"],
                risk=impact["risk_level"],
                depth=impact["depth"],
                confidence=impact["confidence"]
            ))

            # Add edge
            if direction == DirectionEnum.upstream:
                edges.append(GraphEdge(
                    source=impact["uid"],
                    target=result["target_node"]["uid"],
                    type=impact["relation_type"],
                    confidence=impact["confidence"]
                ))
            else:
                edges.append(GraphEdge(
                    source=result["target_node"]["uid"],
                    target=impact["uid"],
                    type=impact["relation_type"],
                    confidence=impact["confidence"]
                ))

        return GraphData(nodes=nodes, links=edges, summary=result["summary"])

    except NodeNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Node '{target}' not found"
        )


__all__ = ['router']
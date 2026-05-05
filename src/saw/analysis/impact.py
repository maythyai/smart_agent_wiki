"""Impact analysis core algorithm."""
from __future__ import annotations
import time
from collections import deque
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from .types import ImpactNode, ImpactResult, RiskLevel, Direction

if TYPE_CHECKING:
    from saw.graph import KnowledgeGraph


class NodeNotFoundError(Exception):
    """Node not found in knowledge graph."""
    pass


def analyze_impact(
    graph: 'KnowledgeGraph',
    target: str,
    direction: Direction = 'upstream',
    max_depth: int = 3,
    min_confidence: float = 0.5,
    relation_types: list[str] = None,
    include_tests: bool = False
) -> ImpactResult:
    """
    GitNexus-style impact analysis.

    Algorithm:
    1. Find target node by name or UID
    2. BFS traverse along specified edges
    3. Group by depth with risk labels
    4. Filter by confidence threshold
    5. Return structured result

    Args:
        graph: Knowledge graph instance
        target: Symbol name or UID to analyze
        direction: 'upstream' (dependents) or 'downstream' (dependencies)
        max_depth: Maximum traversal depth (1-5)
        min_confidence: Minimum edge confidence (0.0-1.0)
        relation_types: Filter by relation types
        include_tests: Include test files

    Returns:
        ImpactResult with affected nodes grouped by depth and risk level
    """
    relation_types = relation_types or ['CALLS', 'IMPORTS', 'EXTENDS', 'IMPLEMENTS']

    start = time.time()

    # Find target
    target_node = _find_node(graph, target)
    if not target_node:
        raise NodeNotFoundError(f"Node '{target}' not found in knowledge graph")

    # BFS traversal
    visited = {target_node['uid']}  # Mark target as visited from start
    impacts = []
    queue = deque([(target_node['uid'], 0)])

    while queue:
        node_id, depth = queue.popleft()

        # Get edges based on direction
        edges = _get_edges(graph, node_id, direction, relation_types)

        for edge in edges:
            if edge.get('confidence', 1.0) < min_confidence:
                continue

            # Get the dependent node
            dep_id = edge['source'] if direction == 'upstream' else edge['target']

            # Skip if already visited
            if dep_id in visited:
                continue

            visited.add(dep_id)

            dep_node = _get_node(graph, dep_id)
            if dep_node is None:
                continue

            # Filter tests if needed
            if not include_tests and _is_test_node(dep_node):
                continue

            # Check depth limit
            if depth + 1 > max_depth:
                continue

            # Add to results
            impacts.append(ImpactNode(
                uid=dep_id,
                name=dep_node.get('name', 'unknown'),
                kind=dep_node.get('kind', 'unknown'),
                file_path=dep_node.get('filePath', ''),
                start_line=dep_node.get('startLine', 0),
                depth=depth + 1,
                risk_level=_get_risk_level(depth + 1),
                relation_type=edge.get('type', 'unknown'),
                confidence=edge.get('confidence', 1.0)
            ))

            queue.append((dep_id, depth + 1))

    # Sort by depth, then confidence
    impacts.sort(key=lambda x: (x['depth'], -x['confidence']))

    execution_time_ms = (time.time() - start) * 1000

    return ImpactResult(
        target=target,
        target_node=target_node,
        direction=direction,
        impacts=impacts,
        summary=_get_summary(impacts),
        execution_time_ms=execution_time_ms,
        analyzed_at=datetime.utcnow().isoformat()
    )


def _find_node(graph, target: str) -> Optional[dict]:
    """Find node by name or UID."""
    # Try exact UID match first
    node = _get_node(graph, target)
    if node:
        return node

    # Try name lookup
    nodes = _find_nodes_by_name(graph, target)
    if nodes:
        return nodes[0]  # Return first match

    return None


def _get_node(graph, uid: str) -> Optional[dict]:
    """Get node by UID."""
    # Placeholder - actual implementation depends on graph
    if hasattr(graph, 'get_node'):
        return graph.get_node(uid)
    return None


def _find_nodes_by_name(graph, name: str) -> list[dict]:
    """Find nodes by name."""
    # Placeholder - actual implementation depends on graph
    if hasattr(graph, 'find_nodes_by_name'):
        return graph.find_nodes_by_name(name)
    return []


def _get_edges(graph, node_id: str, direction: Direction, relation_types: list[str]) -> list[dict]:
    """Get edges for a node based on direction."""
    # Placeholder - actual implementation depends on graph
    if direction == 'upstream':
        if hasattr(graph, 'get_incoming_edges'):
            return graph.get_incoming_edges(node_id, relation_types)
    else:
        if hasattr(graph, 'get_outgoing_edges'):
            return graph.get_outgoing_edges(node_id, relation_types)
    return []


def _get_risk_level(depth: int) -> RiskLevel:
    """Map depth to risk level."""
    if depth == 1:
        return 'WILL_BREAK'
    elif depth == 2:
        return 'LIKELY_AFFECTED'
    else:
        return 'MAY_NEED_TESTING'


def _get_summary(impacts: list[ImpactNode]) -> dict:
    """Generate summary statistics."""
    return {
        'depth_1_count': sum(1 for i in impacts if i['depth'] == 1),
        'depth_2_count': sum(1 for i in impacts if i['depth'] == 2),
        'depth_3_count': sum(1 for i in impacts if i['depth'] == 3),
        'high_risk_count': sum(1 for i in impacts if i['risk_level'] == 'WILL_BREAK'),
        'total_affected': len(impacts)
    }


def _is_test_node(node: dict) -> bool:
    """Check if node is a test."""
    name = node.get('name', '').lower()
    file_path = node.get('filePath', '').lower()

    test_indicators = ['test', 'spec', '_test', '_spec', 'tests/', 'test_']
    return any(ind in name or ind in file_path for ind in test_indicators)
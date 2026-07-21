"""Process detection module."""
from __future__ import annotations
import time
from datetime import datetime
from typing import Optional, Literal, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from saw.graph import KnowledgeGraph


class EntryNotFoundError(Exception):
    """Entry node not found in knowledge graph."""
    pass


@dataclass
class ProcessNode:
    """Node in execution flow tree."""
    uid: str
    name: str
    kind: str
    file_path: str
    depth: int
    children: list['ProcessNode'] = field(default_factory=list)
    relation_type: str = 'CALLS'


@dataclass
class ProcessResult:
    """Process detection result."""
    entry: str
    entry_node: dict
    tree: ProcessNode
    summary: dict
    execution_time_ms: float
    analyzed_at: str


def detect_process(
    graph: 'KnowledgeGraph',
    entry: str,
    max_depth: int = 5,
    relation_types: list[str] = None,
    include_loops: bool = False
) -> ProcessResult:
    """
    Detect execution flow from an entry point.

    Algorithm:
    1. Find entry node
    2. DFS traverse CALLS edges
    3. Build call tree with depth
    4. Detect branches and loops
    5. Return structured flow

    Args:
        graph: Knowledge graph instance
        entry: Entry point name or UID
        max_depth: Maximum traversal depth (1-10)
        relation_types: Filter by relation types (default: CALLS)
        include_loops: Include recursive/loop calls

    Returns:
        ProcessResult with call tree and summary
    """
    relation_types = relation_types or ['CALLS']
    max_depth = max(1, min(max_depth, 10))  # 防止 RecursionError

    start = time.time()

    # Find entry node
    entry_node = _find_node(graph, entry)
    if not entry_node:
        raise EntryNotFoundError(f"Entry point '{entry}' not found in knowledge graph")

    # Build call tree
    tree = ProcessNode(
        uid=entry_node['uid'],
        name=entry_node['name'],
        kind=entry_node.get('kind', 'unknown'),
        file_path=entry_node.get('filePath', ''),
        depth=0,
        children=[]
    )

    visited = set()
    _build_call_tree(graph, tree, visited, max_depth, relation_types, include_loops)

    execution_time_ms = (time.time() - start) * 1000

    return ProcessResult(
        entry=entry,
        entry_node=entry_node,
        tree=tree,
        summary=_get_process_summary(tree),
        execution_time_ms=execution_time_ms,
        analyzed_at=datetime.utcnow().isoformat()
    )


def _find_node(graph, target: str) -> Optional[dict]:
    """Find node by name or UID."""
    node = _get_node(graph, target)
    if node:
        return node

    nodes = _find_nodes_by_name(graph, target)
    if nodes:
        return nodes[0]

    return None


def _get_node(graph, uid: str) -> Optional[dict]:
    """Get node by UID."""
    if hasattr(graph, 'get_node'):
        return graph.get_node(uid)
    return None


def _find_nodes_by_name(graph, name: str) -> list[dict]:
    """Find nodes by name."""
    if hasattr(graph, 'find_nodes_by_name'):
        return graph.find_nodes_by_name(name)
    return []


def _build_call_tree(
    graph: 'KnowledgeGraph',
    node: ProcessNode,
    visited: set,
    max_depth: int,
    relation_types: list[str],
    include_loops: bool
) -> None:
    """Recursively build call tree using DFS."""
    if node.depth >= max_depth:
        return

    # Check for loops
    if node.uid in visited:
        if include_loops:
            # Mark as loop
            node.children.append(ProcessNode(
                uid=node.uid,
                name=f"{node.name} (loop)",
                kind='loop',
                file_path='',
                depth=node.depth + 1,
                relation_type='RECURSIVE'
            ))
        return

    visited.add(node.uid)

    # Get outgoing calls
    edges = _get_outgoing_edges(graph, node.uid, relation_types)

    for edge in edges:
        target_id = edge.get('target')
        target_node = _get_node(graph, target_id)

        if target_node is None:
            continue

        child = ProcessNode(
            uid=target_id,
            name=target_node.get('name', 'unknown'),
            kind=target_node.get('kind', 'unknown'),
            file_path=target_node.get('filePath', ''),
            depth=node.depth + 1,
            relation_type=edge.get('type', 'CALLS'),
            children=[]
        )

        node.children.append(child)

        # Recurse
        _build_call_tree(
            graph, child, visited.copy(), max_depth, relation_types, include_loops
        )


def _get_outgoing_edges(graph, uid: str, types: list[str]) -> list[dict]:
    """Get outgoing edges."""
    if hasattr(graph, 'get_outgoing_edges'):
        return graph.get_outgoing_edges(uid, types)
    return []


def _get_process_summary(tree: ProcessNode) -> dict:
    """Generate summary statistics."""
    total_nodes = 0
    max_depth = 0
    branches = []

    def count_nodes(node: ProcessNode):
        nonlocal total_nodes, max_depth

        total_nodes += 1
        max_depth = max(max_depth, node.depth)

        if len(node.children) > 1:
            branches.append({
                'name': node.name,
                'depth': node.depth,
                'branch_count': len(node.children)
            })

        for child in node.children:
            count_nodes(child)

    count_nodes(tree)

    return {
        'total_nodes': total_nodes,
        'max_depth': max_depth,
        'branch_points': len(branches),
        'branches': branches
    }


def flatten_tree(tree: ProcessNode) -> list[dict]:
    """Flatten tree to list for display."""
    result = []

    def flatten(node: ProcessNode, indent: int = 0):
        prefix = '  ' * indent
        arrow = '→ ' if indent > 0 else ''

        result.append({
            'display': f"{prefix}{arrow}{node.name}",
            'depth': node.depth,
            'name': node.name,
            'kind': node.kind,
            'relation': node.relation_type
        })

        for child in node.children:
            flatten(child, indent + 1)

    flatten(tree)
    return result


__all__ = [
    'detect_process',
    'EntryNotFoundError',
    'ProcessNode',
    'ProcessResult',
    'flatten_tree'
]
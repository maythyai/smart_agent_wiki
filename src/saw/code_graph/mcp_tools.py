"""MCP tools for code graph — saw_code_query / saw_code_search / saw_architecture

升级 saw_impact + 新增图查询和搜索工具。
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Tool Definitions ─────────────────────────────────────────────


def get_code_query_tool_definition() -> dict:
    """saw_code_query: 图模式查询"""
    return {
        "name": "saw_code_query",
        "description": """Query the code graph for structural relationships.

Supported patterns:
- callers_of: Who calls this symbol?
- callees_of: What does this symbol call?
- imports_of: What does this file import?
- importers_of: Who imports this file?
- tests_for: What tests cover this symbol?
- children_of: What does this class/module contain?
- inheritors_of: Who inherits from this class?

Use this BEFORE Grep/Glob for understanding code structure.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Symbol name or UID (e.g., 'AuthService', 'src/auth.py::login')",
                },
                "pattern": {
                    "type": "string",
                    "enum": [
                        "callers_of", "callees_of", "imports_of",
                        "importers_of", "tests_for", "children_of",
                        "inheritors_of",
                    ],
                    "description": "Query pattern",
                },
                "limit": {
                    "type": "integer",
                    "default": 20,
                    "description": "Max results",
                },
            },
            "required": ["target", "pattern"],
        },
    }


def get_code_search_tool_definition() -> dict:
    """saw_code_search: 混合搜索"""
    return {
        "name": "saw_code_search",
        "description": """Search code symbols by name, signature, or file path.

Uses FTS5 full-text search with porter stemming.
Returns matching functions, classes, methods with their signatures and locations.

Use this to find symbols before querying their relationships.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'authenticate', 'UserService', 'handle*')",
                },
                "kind": {
                    "type": "string",
                    "enum": ["function", "class", "method", "type", "test", "endpoint"],
                    "description": "Filter by symbol kind (optional)",
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Max results",
                },
            },
            "required": ["query"],
        },
    }


def get_architecture_tool_definition() -> dict:
    """saw_architecture: 架构概览"""
    return {
        "name": "saw_architecture",
        "description": """Get a high-level architecture overview of the codebase.

Returns:
- Communities (module clusters) with names and members
- Hub nodes (most depended-upon symbols)
- Bridge nodes (cross-module connectors)
- Graph statistics

Use this to understand the overall structure before diving into specifics.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "include_members": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include full member lists for communities",
                },
            },
        },
    }


def get_flows_tool_definition() -> dict:
    """saw_flows: 执行流追踪"""
    return {
        "name": "saw_flows",
        "description": """Trace execution flows through the codebase.

Detects entry points (endpoints, main functions, handlers) and traces
call chains forward. Scores each flow by criticality (security sensitivity,
test coverage, path length).

Use this to understand critical execution paths and identify untested flows.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "max_depth": {
                    "type": "integer",
                    "default": 8,
                    "description": "Maximum trace depth",
                },
                "min_criticality": {
                    "type": "number",
                    "default": 0.0,
                    "description": "Minimum criticality score (0-1)",
                },
                "affected_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Only show flows affected by these symbol UIDs",
                },
            },
        },
    }


# ─── Tool Handlers ────────────────────────────────────────────────


async def handle_code_query(
    target: str,
    pattern: str,
    limit: int = 20,
    engine=None,
) -> dict:
    """Handle saw_code_query tool call."""
    if engine is None:
        return {"error": "engine_not_available", "message": "Code graph engine not initialized"}

    # 输入验证
    if not target or not target.strip():
        return {"error": "invalid_input", "message": "target must not be empty"}
    target = target.strip()[:512]
    limit = max(1, min(int(limit), 200))

    try:
        # Resolve target
        node = engine._resolve_target(target)
        if not node:
            suggestions = [n.name for n in engine.search(target, limit=5)]
            return {
                "error": "node_not_found",
                "message": f"Symbol '{target}' not found",
                "suggestions": suggestions,
            }

        uid = node.uid

        if pattern == "callers_of":
            results = engine.callers_of(uid)
        elif pattern == "callees_of":
            results = engine.callees_of(uid)
        elif pattern == "imports_of":
            results = engine.imports_of(uid)
        elif pattern == "importers_of":
            edges = engine.store.get_incoming_edges(uid, ["IMPORTS"])
            results = [engine.store.get_node(e.source) for e in edges]
            results = [n for n in results if n]
        elif pattern == "tests_for":
            results = engine.tests_for(uid)
        elif pattern == "children_of":
            edges = engine.store.get_outgoing_edges(uid, ["CONTAINS"])
            results = [engine.store.get_node(e.target) for e in edges]
            results = [n for n in results if n]
        elif pattern == "inheritors_of":
            edges = engine.store.get_incoming_edges(uid, ["INHERITS"])
            results = [engine.store.get_node(e.source) for e in edges]
            results = [n for n in results if n]
        else:
            return {"error": "invalid_pattern", "message": f"Unknown pattern: {pattern}"}

        return {
            "target": {"uid": node.uid, "name": node.name, "kind": node.kind.value},
            "pattern": pattern,
            "count": len(results[:limit]),
            "results": [
                {
                    "uid": n.uid,
                    "name": n.name,
                    "kind": n.kind.value,
                    "file_path": n.file_path,
                    "signature": n.signature,
                }
                for n in results[:limit]
            ],
        }

    except Exception as e:
        logger.exception(f"Error in code_query: {e}")
        return {"error": "query_error", "message": str(e)}


async def handle_code_search(
    query: str,
    kind: Optional[str] = None,
    limit: int = 10,
    engine=None,
) -> dict:
    """Handle saw_code_search tool call."""
    if engine is None:
        return {"error": "engine_not_available", "message": "Code graph engine not initialized"}

    # 输入验证
    if not query or not query.strip():
        return {"error": "invalid_input", "message": "query must not be empty"}
    query = query.strip()[:512]
    limit = max(1, min(int(limit), 100))

    try:
        results = engine.search(query, limit=limit * 2)  # over-fetch for filtering

        if kind:
            results = [n for n in results if n.kind.value == kind]

        results = results[:limit]

        return {
            "query": query,
            "kind_filter": kind,
            "count": len(results),
            "results": [
                {
                    "uid": n.uid,
                    "name": n.name,
                    "kind": n.kind.value,
                    "file_path": n.file_path,
                    "start_line": n.start_line,
                    "signature": n.signature,
                    "docstring": (n.docstring or "")[:200],
                }
                for n in results
            ],
        }

    except Exception as e:
        logger.exception(f"Error in code_search: {e}")
        return {"error": "search_error", "message": str(e)}


async def handle_architecture(
    include_members: bool = False,
    engine=None,
) -> dict:
    """Handle saw_architecture tool call."""
    if engine is None:
        return {"error": "engine_not_available", "message": "Code graph engine not initialized"}

    try:
        overview = engine.architecture_overview()

        communities_data = []
        for c in overview.communities:
            entry = {
                "id": c.community_id,
                "name": c.name,
                "size": c.size,
                "files": c.files[:10],
                "hub_nodes": c.hub_nodes[:3],
            }
            if include_members:
                entry["members"] = c.members
            communities_data.append(entry)

        return {
            "total_nodes": overview.total_nodes,
            "total_edges": overview.total_edges,
            "community_count": len(overview.communities),
            "communities": communities_data,
            "hub_nodes": overview.hub_nodes[:10],
            "bridge_nodes": overview.bridge_nodes[:10],
        }

    except Exception as e:
        logger.exception(f"Error in architecture: {e}")
        return {"error": "architecture_error", "message": str(e)}


async def handle_flows(
    max_depth: int = 8,
    min_criticality: float = 0.0,
    affected_by: Optional[list[str]] = None,
    engine=None,
) -> dict:
    """Handle saw_flows tool call."""
    if engine is None:
        return {"error": "engine_not_available", "message": "Code graph engine not initialized"}

    # 输入验证: 防止 max_depth 过大导致 CPU/内存 DoS
    max_depth = max(1, min(int(max_depth), 32))
    min_criticality = max(0.0, min(float(min_criticality), 1.0))

    try:
        if affected_by:
            flows = engine.get_affected_flows(affected_by)
        else:
            flows = engine.trace_flows(max_depth=max_depth)

        # Filter by criticality
        flows = [f for f in flows if f.criticality >= min_criticality]

        return {
            "count": len(flows),
            "flows": [
                {
                    "flow_id": f.flow_id,
                    "entry_point": f.entry_name,
                    "length": f.length,
                    "criticality": round(f.criticality, 3),
                    "security_sensitive": f.security_sensitive,
                    "has_tests": f.has_tests,
                    "files_touched": f.files_touched[:10],
                    "path": [n.name for n in f.nodes[:15]],
                }
                for f in flows[:20]
            ],
        }

    except Exception as e:
        logger.exception(f"Error in flows: {e}")
        return {"error": "flows_error", "message": str(e)}


__all__ = [
    "get_code_query_tool_definition",
    "get_code_search_tool_definition",
    "get_architecture_tool_definition",
    "get_flows_tool_definition",
    "handle_code_query",
    "handle_code_search",
    "handle_architecture",
    "handle_flows",
]

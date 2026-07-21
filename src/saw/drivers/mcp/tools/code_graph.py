"""MCP tools for code graph operations.

Registers code graph tools with FastMCP: saw_code_query, saw_code_search,
saw_architecture, saw_flows, saw_code_context, saw_impact.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from saw.drivers.mcp.server import mcp

logger = logging.getLogger(__name__)

# Global engine reference (set during initialization)
_code_graph_engine = None


def init_code_graph_tools(engine) -> None:
    """Initialize code graph tools with engine reference.

    Args:
        engine: CodeGraphEngine instance.
    """
    global _code_graph_engine
    _code_graph_engine = engine


@mcp.tool
async def saw_code_query(
    target: str,
    pattern: str = "callers_of",
    limit: int = 20,
) -> dict[str, Any]:
    """Query the code graph for structural relationships.

    Supported patterns: callers_of, callees_of, imports_of, importers_of,
    tests_for, children_of, inheritors_of.

    Args:
        target: Symbol name or UID (e.g., 'AuthService', 'src/auth.py::login').
        pattern: Query pattern (callers_of, callees_of, imports_of, etc.).
        limit: Max results (1-200).

    Returns:
        Matching symbols with their locations and signatures.
    """
    if _code_graph_engine is None:
        return {"error": "code_graph_not_initialized", "message": "Code graph engine not available. Run 'saw code-graph build' first."}

    from saw.code_graph.mcp_tools import handle_code_query
    return await handle_code_query(target=target, pattern=pattern, limit=limit, engine=_code_graph_engine)


@mcp.tool
async def saw_code_search(
    query: str,
    kind: Optional[str] = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search code symbols by name, signature, or file path.

    Uses FTS5 full-text search with porter stemming.

    Args:
        query: Search query (e.g., 'authenticate', 'UserService').
        kind: Filter by symbol kind (function, class, method, type, test, endpoint).
        limit: Max results (1-100).

    Returns:
        Matching symbols with signatures, locations, and docstrings.
    """
    if _code_graph_engine is None:
        return {"error": "code_graph_not_initialized", "message": "Code graph engine not available. Run 'saw code-graph build' first."}

    from saw.code_graph.mcp_tools import handle_code_search
    return await handle_code_search(query=query, kind=kind, limit=limit, engine=_code_graph_engine)


@mcp.tool
async def saw_architecture(
    include_members: bool = False,
) -> dict[str, Any]:
    """Get a high-level architecture overview of the codebase.

    Returns communities (module clusters), hub nodes (most depended-upon),
    and bridge nodes (cross-module connectors).

    Args:
        include_members: Include full member lists for communities.

    Returns:
        Architecture overview with communities, hubs, and bridges.
    """
    if _code_graph_engine is None:
        return {"error": "code_graph_not_initialized", "message": "Code graph engine not available. Run 'saw code-graph build' first."}

    from saw.code_graph.mcp_tools import handle_architecture
    return await handle_architecture(include_members=include_members, engine=_code_graph_engine)


@mcp.tool
async def saw_flows(
    max_depth: int = 8,
    min_criticality: float = 0.0,
    affected_by: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Trace execution flows through the codebase.

    Detects entry points and traces call chains forward, scoring each
    flow by criticality (security sensitivity, test coverage, path length).

    Args:
        max_depth: Maximum trace depth (1-32).
        min_criticality: Minimum criticality score (0-1).
        affected_by: Only show flows affected by these symbol UIDs.

    Returns:
        Criticality-scored execution flows with paths and metadata.
    """
    if _code_graph_engine is None:
        return {"error": "code_graph_not_initialized", "message": "Code graph engine not available. Run 'saw code-graph build' first."}

    from saw.code_graph.mcp_tools import handle_flows
    return await handle_flows(
        max_depth=max_depth, min_criticality=min_criticality,
        affected_by=affected_by, engine=_code_graph_engine,
    )


@mcp.tool
async def saw_code_context(
    target: str,
    detail_level: str = "standard",
    token_budget: int = 2000,
) -> dict[str, Any]:
    """Get token-efficient code context for a symbol.

    Assembles a compact context package around a target symbol, respecting
    a token budget. Three detail levels: minimal, standard, verbose.

    Args:
        target: Symbol name or UID.
        detail_level: How much context (minimal, standard, verbose).
        token_budget: Maximum tokens to use (default 2000).

    Returns:
        Context package with savings metadata.
    """
    if _code_graph_engine is None:
        return {"error": "code_graph_not_initialized", "message": "Code graph engine not available. Run 'saw code-graph build' first."}

    from saw.code_graph.context_tool import handle_code_context
    return await handle_code_context(
        target=target, detail_level=detail_level,
        token_budget=token_budget, engine=_code_graph_engine,
    )


@mcp.tool
async def saw_impact(
    target: str,
    direction: str = "upstream",
    max_depth: int = 3,
) -> dict[str, Any]:
    """Analyze code modification impact (blast radius).

    Identifies what will be affected if you modify the target symbol.
    Returns nodes grouped by depth with risk levels:
    - WILL_BREAK: Direct dependents (depth 1)
    - LIKELY_AFFECTED: Indirect dependents (depth 2)
    - MAY_NEED_TESTING: Transitive dependents (depth 3+)

    Args:
        target: Symbol name or UID to analyze.
        direction: 'upstream' (what depends on this) or 'downstream' (what this depends on).
        max_depth: Maximum traversal depth (1-5).

    Returns:
        Impact analysis with affected symbols, risk levels, and scores.
    """
    if _code_graph_engine is None:
        return {"error": "code_graph_not_initialized", "message": "Code graph engine not available. Run 'saw code-graph build' first."}

    max_depth = max(1, min(int(max_depth), 5))
    impacts = _code_graph_engine.impact_analysis(target, direction=direction, max_depth=max_depth)

    if not impacts:
        return {"target": target, "direction": direction, "impacts": [], "summary": "No impact found (symbol may not exist)"}

    return {
        "target": target,
        "direction": direction,
        "total_affected": len(impacts),
        "impacts": [
            {
                "uid": imp.uid,
                "name": imp.name,
                "kind": imp.kind,
                "file_path": imp.file_path,
                "depth": imp.depth,
                "score": round(imp.score, 3),
                "risk_level": imp.risk_level,
                "edge_type": imp.edge_type,
            }
            for imp in impacts
        ],
        "summary": {
            "will_break": sum(1 for i in impacts if i.risk_level == "WILL_BREAK"),
            "likely_affected": sum(1 for i in impacts if i.risk_level == "LIKELY_AFFECTED"),
            "may_need_testing": sum(1 for i in impacts if i.risk_level == "MAY_NEED_TESTING"),
        },
    }

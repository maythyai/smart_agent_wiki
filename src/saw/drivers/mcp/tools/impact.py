"""MCP tool for impact analysis."""
from __future__ import annotations
import logging
from typing import Optional

from saw.analysis.impact import analyze_impact, NodeNotFoundError

logger = logging.getLogger(__name__)


def get_impact_tool_definition() -> dict:
    """Get MCP tool definition for saw_impact."""
    return {
        "name": "saw_impact",
        "description": """Analyze code modification impact.

Identifies what will be affected if you modify the target symbol.
Use this BEFORE making changes to understand blast radius.

Returns nodes grouped by depth with risk levels:
- WILL_BREAK: Direct dependents (depth 1) that will definitely break
- LIKELY_AFFECTED: Indirect dependents (depth 2) that might be affected
- MAY_NEED_TESTING: Transitive dependents (depth 3+) that should be tested

High-risk modifications trigger warnings.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Symbol name or UID to analyze (e.g., 'UserService', 'handleLogin')"
                },
                "direction": {
                    "type": "string",
                    "enum": ["upstream", "downstream"],
                    "default": "upstream",
                    "description": "'upstream' (what depends on this) or 'downstream' (what this depends on)"
                },
                "max_depth": {
                    "type": "integer",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 5,
                    "description": "Maximum traversal depth"
                },
                "min_confidence": {
                    "type": "number",
                    "default": 0.8,
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Minimum edge confidence threshold"
                },
                "relation_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["CALLS", "IMPORTS", "INHERITS", "IMPLEMENTS"]
                    },
                    "description": "Filter by relation types (default: all)"
                },
                "include_tests": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include test files in results"
                }
            },
            "required": ["target"]
        }
    }


async def handle_impact_tool(
    target: str,
    direction: str = 'upstream',
    max_depth: int = 3,
    min_confidence: float = 0.8,
    relation_types: Optional[list[str]] = None,
    include_tests: bool = False,
    graph=None
) -> dict:
    """
    Handle saw_impact MCP tool call.

    Args:
        target: Symbol name or UID
        direction: 'upstream' or 'downstream'
        max_depth: Maximum traversal depth
        min_confidence: Minimum confidence threshold
        relation_types: Filter by relation types
        include_tests: Include test files
        graph: Knowledge graph instance

    Returns:
        ImpactResult dict or error response
    """
    if graph is None:
        # Try to get graph from context
        try:
            from saw.graph import get_graph
            graph = get_graph()
        except ImportError:
            return {
                "error": "graph_not_available",
                "message": "Knowledge graph not initialized"
            }

    try:
        result = analyze_impact(
            graph, target, direction, max_depth,
            min_confidence, relation_types, include_tests
        )

        # Warning for high-risk modifications
        if result['summary']['high_risk_count'] > 0:
            logger.warning(
                f"HIGH RISK: Modifying {target} will break "
                f"{result['summary']['high_risk_count']} direct dependents"
            )

        return result

    except NodeNotFoundError as e:
        suggestions = _find_similar_nodes(graph, target)
        return {
            "error": "node_not_found",
            "message": str(e),
            "suggestions": suggestions[:5] if suggestions else []
        }
    except Exception as e:
        logger.exception(f"Error analyzing impact for {target}")
        return {
            "error": "analysis_error",
            "message": str(e)
        }


def _find_similar_nodes(graph, target: str) -> list[str]:
    """Find similar node names for suggestions."""
    try:
        # Try to find nodes with similar names
        all_nodes = []
        if hasattr(graph, 'get_all_nodes'):
            all_nodes = graph.get_all_nodes()
        elif hasattr(graph, 'nodes'):
            all_nodes = list(graph.nodes.values())

        # Simple fuzzy matching - first 3 characters
        prefix = target[:3].lower() if len(target) >= 3 else target.lower()
        return [n['name'] for n in all_nodes
                if n.get('name', '').lower().startswith(prefix)][:5]
    except Exception:
        return []


__all__ = ['get_impact_tool_definition', 'handle_impact_tool']
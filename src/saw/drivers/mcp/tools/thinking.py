"""
Thinking Tools MCP - 批判性思维工具集

基于 Obsidian Second Brain 的 Thinking Tools 设计模式.

F-MCP-01: these tools were defined but never registered with FastMCP, so
half the MCP tool surface was unreachable. The wrappers below expose only
the user-facing parameters (idea / topics / level / days) and return a
formatted string; the underlying *_tool functions keep their wiki_path
default (the server's CWD == wiki root under `saw mcp`).
"""

from saw.drivers.mcp.server import mcp
from .challenge import challenge_tool, format_challenge_result
from .connect import connect_tool, format_connect_result
from .context import context_tool, format_context_bundle
from .emerge import emerge_tool, format_emerge_result
from .graduate import graduate_tool, format_graduate_result

__all__ = [
    "challenge_tool",
    "emerge_tool",
    "connect_tool",
    "graduate_tool",
    "context_tool",
]


@mcp.tool
def saw_challenge(idea: str) -> str:
    """Challenge an idea: surface historical failures and counter-arguments
    so it can be pressure-tested before committing."""
    return format_challenge_result(challenge_tool(idea=idea))


@mcp.tool
def saw_connect(topic_a: str, topic_b: str) -> str:
    """Bridge two topics: find shared concepts, cross-insights, and
    actionable ideas linking them."""
    return format_connect_result(connect_tool(topic_a=topic_a, topic_b=topic_b))


@mcp.tool
def saw_context(level: str = "l1") -> str:
    """Progressively load context by level (l0 / l1 / l2 / l3) to control
    token consumption."""
    return format_context_bundle(context_tool(level=level))


@mcp.tool
def saw_emerge(days: int = 30, min_occurrences: int = 3) -> str:
    """Discover unnamed patterns across recent notes and propose names +
    definitions for repeating concepts."""
    return format_emerge_result(emerge_tool(days=days, min_occurrences=min_occurrences))


@mcp.tool
def saw_graduate(idea: str) -> str:
    """Promote an idea to a project: assess maturity, generate a spec and
    task breakdown, and draft a kanban."""
    return format_graduate_result(graduate_tool(idea=idea))

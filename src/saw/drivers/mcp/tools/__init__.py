"""MCP tools package.

Provides tool registration for MCP server.
"""
from saw.drivers.mcp.tools import register_all_tools

__all__ = ["register_all_tools"]


def register_all_tools(mcp) -> None:
    """Register all MCP tools with the server.

    Args:
        mcp: FastMCP instance to register tools with.
    """
    # Tools will be registered when implemented
    pass

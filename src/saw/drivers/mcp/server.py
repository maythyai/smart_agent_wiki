"""MCP server using FastMCP.

Per STACK.md: FastMCP==3.2.4
Per PITFALLS.md: Use async LiteLLM calls with timeouts.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fastmcp import FastMCP

from saw.drivers.mcp.config import MCPConfig

if TYPE_CHECKING:
    from saw.engines.govern.governor import Governor
    from saw.engines.learn.engine import LearnEngine
    from saw.engines.query.engine import QueryEngine
    from saw.engines.ingest.pipeline import IngestPipeline


# Global MCP instance
mcp = FastMCP(
    name="smart-agent-wiki",
    version="1.0.0",
)


def create_server(wiki_path: Path) -> FastMCP:
    """Create and configure MCP server with all tools.

    Args:
        wiki_path: Path to the wiki directory.

    Returns:
        Configured FastMCP instance.
    """
    # The mcp instance is already created globally
    # In production, this would initialize engines and register tools
    # For now, return the global instance
    return mcp


def run_server(config: MCPConfig) -> None:
    """Run the MCP server.

    Args:
        config: MCP server configuration.
    """
    mcp.run(transport=config.transport)
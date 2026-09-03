"""CLI command for MCP server.

Per D-17: Typer CLI with Rich-formatted output.
"""
from __future__ import annotations

import typer
from rich.console import Console

from saw.drivers.mcp.config import MCPConfig
from saw.drivers.mcp.server import create_server, run_server

console = Console()


def mcp(
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to run MCP server on (for SSE transport)",
    ),
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        "-h",
        help="Host to bind MCP server to",
    ),
    transport: str = typer.Option(
        "stdio",
        "--transport",
        "-t",
        help="Transport protocol: 'stdio' or 'sse'",
    ),
) -> None:
    """Start the MCP server for agent integration.

    Usage:
        saw mcp                   # Start with stdio transport (default)
        saw mcp --transport sse   # Start with HTTP SSE transport
        saw mcp --port 9000       # Use custom port for SSE
    """
    from pathlib import Path

    # Determine wiki path from current directory
    wiki_path = Path.cwd() / ".saw"

    if not wiki_path.exists():
        console.print("[yellow]Warning: No .saw directory found in current path[/yellow]")
        console.print("[yellow]Run 'saw init' first to create a wiki[/yellow]")

    config = MCPConfig(
        port=port,
        host=host,
        transport=transport,
    )

    console.print("[blue]Starting MCP server...[/blue]")
    console.print(f"[green]Server: {config.server_name} v{config.server_version}[/green]")
    console.print(f"[green]Transport: {config.transport}[/green]")

    if transport == "sse":
        console.print(f"[green]Listening on {config.host}:{config.port}[/green]")

    # Create and run server
    create_server(wiki_path)
    run_server(config)
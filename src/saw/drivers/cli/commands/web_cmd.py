"""CLI `web` command - start the Smart Agent Wiki web server.

Per D-02: Default port 8000.
Per D-03: CORS configuration for frontend development.
"""
from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def web(
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        "-h",
        help="Host to bind the server",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to bind the server (per D-02)",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        "-r",
        help="Enable auto-reload for development",
    ),
    cors_origins: str = typer.Option(
        "http://localhost:3000,http://127.0.0.1:3000",
        "--cors",
        "-c",
        help="Comma-separated CORS origins",
    ),
) -> None:
    """Start the Smart Agent Wiki web server.

    Per D-02: Default port 8000.

    Examples:
        saw web                      # Start on http://127.0.0.1:8000
        saw web --port 9000          # Start on port 9000
        saw web --host 0.0.0.0       # Bind to all interfaces
        saw web --reload             # Development mode with auto-reload
    """
    import uvicorn

    # Parse CORS origins
    cors_list = [o.strip() for o in cors_origins.split(",") if o.strip()]

    # Development mode with reload
    if reload:
        console.print(f"[blue]Starting development server on http://{host}:{port}[/blue]")
        console.print("[yellow]Auto-reload enabled[/yellow]")
        uvicorn.run(
            "saw.drivers.web.app:create_app_from_config",
            host=host,
            port=port,
            reload=True,
            factory=True,
        )
    else:
        # Production mode: create app instance
        from saw.drivers.web.app import create_app_from_config

        app = create_app_from_config(cors_origins=cors_list, host=host, port=port)

        console.print("[green]Starting Smart Agent Wiki server[/green]")
        console.print(f"[blue]Server running at http://{host}:{port}[/blue]")
        console.print(f"[blue]API docs at http://{host}:{port}/docs[/blue]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")

        uvicorn.run(
            app,
            host=host,
            port=port,
        )

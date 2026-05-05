"""CLI entry point for Smart Agent Wiki.

Per D-17: Typer CLI with Rich-formatted output.
"""
from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer(
    name="saw",
    help="Smart Agent Wiki - 智能多代理知识平台",
    no_args_is_help=True,
)
console = Console()

# Import and register commands
from saw.drivers.cli.commands.init_cmd import init  # noqa: E402
from saw.drivers.cli.commands.status_cmd import status  # noqa: E402
from saw.drivers.cli.commands.ingest_cmd import ingest  # noqa: E402
from saw.drivers.cli.commands.query_cmd import query  # noqa: E402
from saw.drivers.cli.commands.search_cmd import search  # noqa: E402
from saw.drivers.cli.commands.lint_cmd import lint  # noqa: E402
from saw.drivers.cli.commands.verify_cmd import verify  # noqa: E402
from saw.drivers.cli.commands.freshness_cmd import freshness  # noqa: E402
from saw.drivers.cli.commands.review_cmd import review  # noqa: E402
from saw.drivers.cli.commands.conflicts_cmd import conflicts  # noqa: E402
from saw.drivers.cli.commands.audit_cmd import audit  # noqa: E402
from saw.drivers.cli.commands.mcp_cmd import mcp  # noqa: E402
from saw.drivers.cli.commands.web_cmd import web  # noqa: E402
from saw.drivers.cli.commands.ingest_media_cmd import ingest_media, preview_app  # noqa: E402
from saw.drivers.cli.commands.feed_cmd import app as feed_app  # noqa: E402
from saw.cli.commands.tutorial_cmd import tutorial  # noqa: E402

# Phase 33: CLI Usability - Import new modules
from saw.cli.config_tui import config  # noqa: E402
from saw.cli.completion import completion  # noqa: E402

# Register main commands
app.command(name="init")(init)
app.command(name="status")(status)
app.command(name="ingest")(ingest)
app.command(name="ingest-media")(ingest_media)
app.add_typer(preview_app, name="preview")
app.command(name="query")(query)
app.command(name="search")(search)
app.command(name="lint")(lint)
app.command(name="verify")(verify)
app.command(name="freshness")(freshness)
app.command(name="review")(review)
app.command(name="conflicts")(conflicts)
app.command(name="audit")(audit)
app.command(name="mcp")(mcp)
app.command(name="web")(web)

# Phase 9: RSS Feed commands
app.add_typer(feed_app, name="feed")

# Phase 31: Tutorial command
app.command(name="tutorial")(tutorial)

# Phase 33: CLI Usability commands
app.command(name="config")(config)
app.command(name="completion")(completion)

# Phase 33: Short command aliases (CLI-01)
app.command(name="i", help="Short alias for 'ingest'")(ingest)
app.command(name="q", help="Short alias for 'query'")(query)
app.command(name="s", help="Short alias for 'status'")(status)
app.command(name="w", help="Short alias for 'web'")(web)
app.command(name="v", help="Short alias for 'verify'")(verify)
app.command(name="l", help="Short alias for 'lint'")(lint)


def main() -> None:
    """Main entry point."""
    # Setup friendly error handler
    from saw.cli.error_handler import setup_error_handler
    setup_error_handler()

    app()


if __name__ == "__main__":
    main()
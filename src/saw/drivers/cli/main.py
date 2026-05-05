"""CLI entry point for Smart Agent Wiki.

Per D-17: Typer CLI with Rich-formatted output.
"""
from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer(
    name="saw",
    help="Smart Agent Wiki - \u667a\u80fd\u591a\u4ee3\u7406\u77e5\u8bc6\u5e73\u53f0",
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

app.command(name="init")(init)
app.command(name="status")(status)
app.command(name="ingest")(ingest)
app.command(name="ingest-media")(ingest_media)
app.add_typer(preview_app, name="preview")
app.command(name="query")(query)
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
# Phase 32: Tutorial command
app.command(name="tutorial")(tutorial)

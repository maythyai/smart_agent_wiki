"""CLI entry point for Smart Agent Wiki.

Per D-17: Typer CLI with Rich-formatted output.
"""
from __future__ import annotations

import typer
from rich.console import Console
from importlib.metadata import version as _pkg_version, PackageNotFoundError

app = typer.Typer(
    name="saw",
    help="Smart Agent Wiki - 智能多代理知识平台",
    no_args_is_help=True,
)
console = Console()

try:
    __version__ = _pkg_version("smart-agent-wiki")
except PackageNotFoundError:  # editable/dev checkout without metadata
    __version__ = "0.0.0"


@app.callback(invoke_without_command=True)
def _main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        is_eager=True,
    ),
) -> None:
    """Smart Agent Wiki — local-first multi-agent knowledge platform."""
    if version:
        typer.echo(f"saw {__version__}")
        raise typer.Exit()

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
from saw.drivers.cli.commands.tutorial_cmd import tutorial  # noqa: E402

# Phase 33: CLI Usability - Import new modules
from saw.drivers.cli.config_tui import config  # noqa: E402
from saw.drivers.cli.completion import completion  # noqa: E402
from saw.drivers.cli.commands.docs_cmd import docs  # noqa: E402
from saw.drivers.cli.commands.smoke_cmd import smoke  # noqa: E402
from saw.drivers.cli.commands.health_cmd import health  # noqa: E402

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
app.command(name="health")(health)
app.command(name="mcp")(mcp)
app.command(name="web")(web)

# Phase 9: RSS Feed commands
app.add_typer(feed_app, name="feed")

# Phase 31: Tutorial command
app.command(name="tutorial")(tutorial)

# Phase 33: CLI Usability commands
app.command(name="config")(config)
app.command(name="completion")(completion)

# Phase 34: Documentation command
app.command(name="docs")(docs)

# Smoke baseline command (T-F-A-1-1)
app.command(name="smoke")(smoke)

# v1.5.0 intelligence-adaptation CLI surface (F-I-1..4, F-Z-8)
from saw.drivers.cli.commands.workflow_cmd import app as workflow_app  # noqa: E402
from saw.drivers.cli.commands.learn_cmd import app as learn_app  # noqa: E402
from saw.drivers.cli.commands.token_cmd import app as token_app  # noqa: E402
from saw.drivers.cli.commands.policy_cmd import app as policy_app  # noqa: E402
from saw.drivers.cli.commands.links_cmd import app as links_app  # noqa: E402
from saw.drivers.cli.commands.summarize_cmd import summarize  # noqa: E402
from saw.drivers.cli.commands.agents_cmd import agents  # noqa: E402
app.add_typer(workflow_app, name="workflow")
app.add_typer(learn_app, name="learn")
app.add_typer(token_app, name="token")
app.add_typer(policy_app, name="policy")
app.add_typer(links_app, name="links")
app.command(name="summarize")(summarize)
app.command(name="agents")(agents)

# Code Graph lifecycle commands
from saw.code_graph.cli import register_code_graph_commands  # noqa: E402
register_code_graph_commands(app)

# Wiki compile layer, concept graph, feedback, and code wiki commands
from saw.drivers.cli.commands.compile_cmd import register_compile_commands  # noqa: E402
register_compile_commands(app)

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
    from saw.drivers.cli.error_handler import setup_error_handler
    setup_error_handler()

    app()


if __name__ == "__main__":
    main()
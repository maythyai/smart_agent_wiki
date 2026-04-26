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

app.command(name="init")(init)
app.command(name="status")(status)

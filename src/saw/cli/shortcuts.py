"""Short command aliases for Smart Agent Wiki CLI.

This module provides abbreviated commands for faster typing:
- saw i → saw ingest
- saw q → saw query
- saw s → saw status
- saw w → saw web

Usage:
    saw i document.pdf
    saw q "topic"
    saw s
"""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()

# Shortcuts app
shortcuts_app = typer.Typer(
    name="shortcuts",
    help="Short command aliases",
    no_args_is_help=False,
)


@shortcuts_app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Handle shortcut commands when no subcommand is provided."""
    # If invoked without command, try to interpret as shortcut
    if ctx.invoked_subcommand is None:
        console.print("[yellow]Tip: Use full commands for more options[/yellow]")
        console.print("  saw ingest  → saw i")
        console.print("  saw query   → saw q")
        console.print("  saw status  → saw s")
        console.print("  saw web     → saw w")


def create_shortcut_wrapper(original_command, short_name: str):
    """Create a wrapper that delegates to the original command."""

    def wrapper(*args, **kwargs):
        # Simply call the original command
        return original_command(*args, **kwargs)

    # Preserve the original command's signature
    wrapper.__name__ = short_name
    wrapper.__doc__ = original_command.__doc__

    return wrapper


# Command aliases (will be registered in main.py)
ALIASES = {
    "i": "ingest",      # ingest
    "q": "query",       # query
    "s": "status",      # status
    "w": "web",         # web
    "v": "verify",      # verify
    "l": "lint",        # lint
    "r": "review",      # review
    "a": "audit",       # audit
    "c": "conflicts",   # conflicts
    "f": "freshness",   # freshness
}


def get_alias_help(alias: str) -> str:
    """Get help text for an alias."""
    full_cmd = ALIASES.get(alias, alias)
    return f"Short alias for '{full_cmd}' command"


__all__ = ["shortcuts_app", "ALIASES", "create_shortcut_wrapper", "get_alias_help"]
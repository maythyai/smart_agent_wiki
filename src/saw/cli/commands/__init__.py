"""CLI commands package."""

from saw.cli.commands.tutorial_cmd import app as tutorial_app

__all__ = ["tutorial_app"]


# CLI command registration helper
def get_cli_commands():
    """Get all CLI command modules."""
    return {
        "tutorial": tutorial_app,
    }

"""Friendly error handling for Smart Agent Wiki CLI.

This module provides user-friendly error messages with suggestions
instead of raw stack traces.

Usage:
    from saw.drivers.cli.error_handler import handle_error

    try:
        risky_operation()
    except Exception as e:
        handle_error(e)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


# Error message templates with suggestions
ERROR_SUGGESTIONS = {
    FileNotFoundError: {
        "message": "File '{path}' not found",
        "suggestions": [
            "Check if the file exists: ls {path}",
            "Use absolute path: saw ingest /full/path/to/{path}",
            "Ingest entire directory: saw ingest ./documents/",
        ],
    },
    PermissionError: {
        "message": "Permission denied for '{path}'",
        "suggestions": [
            "Check file permissions: ls -la {path}",
            "Run with appropriate permissions",
            "Ensure the directory is writable",
        ],
    },
    ValueError: {
        "message": "Invalid value provided",
        "suggestions": [
            "Check the command syntax: saw --help",
            "Verify the input format",
        ],
    },
    KeyError: {
        "message": "Required key '{key}' not found",
        "suggestions": [
            "Check configuration file",
            "Run 'saw init' to create default config",
        ],
    },
    ConnectionError: {
        "message": "Could not connect to '{endpoint}'",
        "suggestions": [
            "Check if the server is running",
            "Verify network connectivity",
            "Check firewall settings",
        ],
    },
}


def format_path(path: Optional[str]) -> str:
    """Format a path for display."""
    if path:
        return str(Path(path).resolve())
    return "<unknown>"


def handle_error(
    error: Exception,
    context: Optional[dict] = None,
    show_traceback: bool = False,
) -> None:
    """
    Handle an exception with a friendly error message.

    Args:
        error: The exception to handle
        context: Additional context (e.g., {'path': 'file.pdf'})
        show_traceback: Whether to show full traceback (debug mode)
    """
    context = context or {}
    error_type = type(error)

    # Get error template
    template = ERROR_SUGGESTIONS.get(error_type, {
        "message": f"{type(error).__name__}: {error}",
        "suggestions": [
            "Check the error message above for clues.",
            "If this persists, re-run with --debug for a full traceback.",
        ],
    })

    # Format message with context
    message = template["message"]
    for key, value in context.items():
        message = message.replace(f"{{{key}}}", format_path(str(value)))

    # Display error
    console.print()
    console.print(Panel(
        f"[red bold]Error: {message}[/red bold]",
        title="❌",
        border_style="red",
    ))

    # Show suggestions
    if template.get("suggestions"):
        console.print("\n[yellow bold]💡 Suggestions:[/yellow bold]")
        for suggestion in template["suggestions"]:
            # Format suggestion with context
            formatted = suggestion
            for key, value in context.items():
                formatted = formatted.replace(f"{{{key}}}", format_path(str(value)))
            console.print(f"  • {formatted}")

    # Show traceback in debug mode
    if show_traceback or os.environ.get("SAW_DEBUG"):
        console.print("\n[dim]Debug traceback:[/dim]")
        import traceback
        console.print(traceback.format_exc())

    console.print()


def setup_error_handler():
    """Set up global error handler for the CLI."""
    def excepthook(exc_type, exc_value, exc_tb):
        # Skip KeyboardInterrupt (Ctrl+C)
        if exc_type is KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled by user.[/yellow]")
            return

        # Handle other exceptions
        handle_error(exc_value)

    sys.excepthook = excepthook


def wrap_command(command_func):
    """Wrap a command function with error handling."""
    def wrapper(*args, **kwargs):
        try:
            return command_func(*args, **kwargs)
        except Exception as e:
            # Extract context from args if possible
            context = {}
            if args and isinstance(args[0], str):
                context["path"] = args[0]
            handle_error(e, context)
            raise typer.Exit(1)

    wrapper.__name__ = command_func.__name__
    wrapper.__doc__ = command_func.__doc__
    return wrapper


__all__ = ["handle_error", "setup_error_handler", "wrap_command", "ERROR_SUGGESTIONS"]
"""Interactive TUI configuration for Smart Agent Wiki.

This module provides a terminal-based configuration interface
using questionary for interactive prompts.

Usage:
    saw config
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

console = Console()

# Default configuration schema
DEFAULT_CONFIG = {
    "wiki": {
        "name": "My Wiki",
        "description": "Personal knowledge base",
    },
    "storage": {
        "database": "wiki.db",
        "vault": "vault/",
        "claims": "claims/",
        "wiki": "wiki/",
    },
    "llm": {
        "provider": "auto",
        "model": "auto",
        "api_key": "",
    },
    "ingest": {
        "auto_validate_threshold": 0.7,
        "formats": ["md", "pdf", "url", "py", "js", "ts"],
    },
    "query": {
        "default_mode": "direct",
        "max_results": 20,
    },
}


def load_config(config_path: Path) -> dict:
    """Load configuration from file."""
    if not config_path.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config: dict, config_path: Path) -> None:
    """Save configuration to file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def display_current_config(config: dict) -> None:
    """Display current configuration in a table."""
    table = Table(title="Current Configuration", show_header=True)
    table.add_column("Section", style="cyan")
    table.add_column("Key", style="green")
    table.add_column("Value", style="yellow")

    for section, values in config.items():
        if isinstance(values, dict):
            for key, value in values.items():
                # Mask sensitive values
                if "key" in key.lower() or "password" in key.lower():
                    value = "***" if value else "(not set)"
                table.add_row(section, key, str(value))
        else:
            table.add_row(section, "-", str(values))

    console.print(table)


def interactive_config(config_path: Optional[Path] = None) -> None:
    """
    Interactive configuration wizard.

    Usage:
        saw config
        saw config --path ./my-wiki/saw.yaml
    """
    if config_path is None:
        config_path = Path.cwd() / "saw.json"

    console.print(Panel.fit(
        "[bold blue]Smart Agent Wiki Configuration[/bold blue]\n"
        "[dim]Interactive setup wizard[/dim]",
        border_style="blue",
    ))

    # Load existing config
    config = load_config(config_path)
    console.print(f"\nConfig file: [cyan]{config_path}[/cyan]\n")

    # Display current config
    display_current_config(config)

    console.print("\n[bold]Configure Settings:[/bold]\n")

    # Wiki settings
    console.print("[bold cyan]Wiki Settings[/bold cyan]")
    config["wiki"]["name"] = Prompt.ask(
        "  Wiki name",
        default=config["wiki"]["name"],
    )
    config["wiki"]["description"] = Prompt.ask(
        "  Description",
        default=config["wiki"]["description"],
    )

    # LLM settings
    console.print("\n[bold cyan]LLM Settings[/bold cyan]")
    console.print("  Provider options: local, openai, anthropic, auto")

    provider = Prompt.ask(
        "  LLM provider",
        default=config["llm"]["provider"],
        choices=["local", "openai", "anthropic", "auto"],
    )
    config["llm"]["provider"] = provider

    if provider in ["openai", "anthropic"]:
        api_key = Prompt.ask(
            f"  {provider.capitalize()} API key",
            default="",
            password=True,
        )
        config["llm"]["api_key"] = api_key if api_key else ""

    # Query settings
    console.print("\n[bold cyan]Query Settings[/bold cyan]")
    config["query"]["max_results"] = int(Prompt.ask(
        "  Max results per query",
        default=str(config["query"]["max_results"]),
    ))

    # Show updated config
    console.print()
    display_current_config(config)

    # Confirm save
    if Confirm.ask("\nSave configuration?", default=True):
        save_config(config, config_path)
        console.print(f"\n[green]✓ Configuration saved to {config_path}[/green]")
    else:
        console.print("\n[yellow]Configuration not saved.[/yellow]")


def config(
    path: Optional[Path] = typer.Option(
        None,
        "--path", "-p",
        help="Path to configuration file",
    ),
    show: bool = typer.Option(
        False,
        "--show", "-s",
        help="Show current configuration without editing",
    ),
) -> None:
    """
    Configure Smart Agent Wiki settings.

    This command opens an interactive configuration wizard
    to set up your wiki preferences.

    Examples:
        saw config
        saw config --show
        saw config --path ./my-wiki/saw.json
    """
    config_path = path or Path.cwd() / "saw.json"

    if show:
        config = load_config(config_path)
        display_current_config(config)
        return

    interactive_config(config_path)


app = typer.Typer(help="Configuration management")
app.command(name="config")(config)


__all__ = ["config", "interactive_config", "load_config", "save_config", "DEFAULT_CONFIG"]
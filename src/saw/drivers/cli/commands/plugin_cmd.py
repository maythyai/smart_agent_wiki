"""Plugin CLI commands.

saw plugin list/install/enable/disable/uninstall
"""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
import shutil

from saw.plugins.registry import PluginRegistry
from saw.plugins.base import PluginContext

app = typer.Typer(help="Manage plugins")
console = Console()


@app.command("list")
def list_plugins():
    """List all installed plugins."""
    registry = PluginRegistry()
    registry.discover()
    plugins = registry.list_plugins()

    if not plugins:
        console.print("[yellow]No plugins installed.[/yellow]")
        return

    table = Table(title="Installed Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Status", style="magenta")
    table.add_column("Description")

    for p in plugins:
        status = "[green]Enabled[/green]" if p["enabled"] else "[dim]Disabled[/dim]"
        table.add_row(p["name"], p["version"], status, p["description"])

    console.print(table)


@app.command("install")
def install_plugin(
    source: str = typer.Argument(..., help="Plugin source path or URL"),
):
    """Install a plugin from local path."""
    source_path = Path(source).expanduser()
    if not source_path.exists():
        console.print(f"[red]Source not found: {source}[/red]")
        raise typer.Exit(1)

    plugins_dir = Path.home() / ".saw" / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    dest = plugins_dir / source_path.name
    if dest.exists():
        console.print(f"[yellow]Plugin already installed: {dest.name}[/yellow]")
        return

    try:
        shutil.copytree(source_path, dest)
        console.print(f"[green]Installed: {dest.name}[/green]")
    except Exception as e:
        console.print(f"[red]Install failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("enable")
def enable_plugin(
    name: str = typer.Argument(..., help="Plugin name"),
):
    """Enable a plugin."""
    registry = PluginRegistry()
    registry.discover()

    # Create minimal context
    data_dir = Path.home() / ".saw" / "plugins" / name / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    context = PluginContext(
        data_dir=data_dir,
        wiki_read=lambda x: None,
        wiki_write=lambda x, y: False,
        claims_read=lambda x: [],
        graph_query=lambda x: [],
        subscribe_event=lambda x, y: None,
        publish_event=lambda x, y: None,
    )

    if registry.enable(name, context):
        console.print(f"[green]Enabled: {name}[/green]")
    else:
        console.print(f"[red]Failed to enable: {name}[/red]")
        raise typer.Exit(1)


@app.command("disable")
def disable_plugin(
    name: str = typer.Argument(..., help="Plugin name"),
):
    """Disable a plugin."""
    registry = PluginRegistry()
    registry.discover()

    if registry.disable(name):
        console.print(f"[yellow]Disabled: {name}[/yellow]")
    else:
        console.print(f"[red]Failed to disable: {name}[/red]")
        raise typer.Exit(1)


@app.command("uninstall")
def uninstall_plugin(
    name: str = typer.Argument(..., help="Plugin name"),
):
    """Uninstall a plugin."""
    plugins_dir = Path.home() / ".saw" / "plugins"
    plugin_path = plugins_dir / name

    if not plugin_path.exists():
        console.print(f"[yellow]Plugin not found: {name}[/yellow]")
        return

    try:
        shutil.rmtree(plugin_path)
        console.print(f"[green]Uninstalled: {name}[/green]")
    except Exception as e:
        console.print(f"[red]Uninstall failed: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

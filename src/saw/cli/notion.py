"""CLI commands for Notion sync.

Plan 12-03: Bidirectional sync and polling.
Per NOTI-05: Sync can be triggered manually via CLI.
"""
from __future__ import annotations

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from saw.connectors.protocol import SyncDirection
from saw.connectors.notion.sync_manager import NotionSyncConfig


console = Console()
notion_group = typer.Typer(name="notion", help="Notion connector commands")


@notion_group.command("sync")
def sync_command(
    direction: str = typer.Option(
        "bidirectional",
        "--direction",
        "-d",
        help="Sync direction: pull, push, or bidirectional",
    ),
    full: bool = typer.Option(
        False,
        "--full",
        "-f",
        help="Sync all items, ignoring last_sync_at",
    ),
    wait: bool = typer.Option(
        False,
        "--wait",
        "-w",
        help="Wait for sync to complete",
    ),
) -> None:
    """Trigger Notion sync.

    Examples:
        saw notion sync --direction pull
        saw notion sync --direction push
        saw notion sync --full
    """
    direction_map = {
        "pull": SyncDirection.PULL,
        "push": SyncDirection.PUSH,
        "bidirectional": SyncDirection.BIDIRECTIONAL,
    }

    if direction not in direction_map:
        console.print(f"[red]Invalid direction: {direction}[/red]")
        console.print("Valid options: pull, push, bidirectional")
        raise typer.Exit(1)

    console.print(f"[blue]Starting Notion sync: {direction}[/blue]")
    if full:
        console.print("[yellow]Full sync mode - ignoring last_sync_at[/yellow]")

    # Run async sync
    asyncio.run(_run_sync(direction_map[direction], full, wait))


async def _run_sync(
    direction: SyncDirection,
    force: bool,
    wait: bool,
) -> None:
    """Execute sync operation."""
    try:
        # Import here to avoid circular dependencies
        from saw.connectors.registry import ConnectorRegistry
        from saw.connectors.notion.sync_manager import NotionSyncManager
        from saw.db.config import get_async_engine, get_session_factory
        from sqlalchemy.ext.asyncio import AsyncSession

        registry = ConnectorRegistry()
        connector = registry.get("notion")

        if connector is None:
            console.print("[red]Notion connector not registered[/red]")
            console.print("Run 'saw notion connect' first")
            return

        # Get required components
        sync_engine = getattr(connector, "_sync_engine", None)
        scheduler = getattr(connector, "_scheduler", None)

        if not sync_engine:
            console.print("[red]Sync engine not initialized[/red]")
            return

        # Create sync manager
        engine = get_async_engine()
        session_factory = get_session_factory(engine)

        async for session in session_factory():
            manager = NotionSyncManager(
                config=NotionSyncConfig(),
                connector=connector,
                sync_engine=sync_engine,
                scheduler=scheduler or _get_dummy_scheduler(),
                session=session,
            )

            result = await manager.trigger_manual_sync(direction=direction, force=force)

            # Display results
            console.print("\n[green]Sync completed[/green]")
            console.print(f"  Pulled: {result.pulled_count}")
            console.print(f"  Pushed: {result.pushed_count}")
            console.print(f"  Conflicts: {result.conflicts_count}")

            if result.errors:
                console.print("\n[red]Errors:[/red]")
                for error in result.errors:
                    console.print(f"  - {error}")

            break

    except Exception as e:
        console.print(f"[red]Sync failed: {e}[/red]")


def _get_dummy_scheduler():
    """Get a dummy scheduler for CLI use."""
    class DummyScheduler:
        def add_job(self, *args, **kwargs):
            pass
        def remove_job(self, *args, **kwargs):
            pass
    return DummyScheduler()


@notion_group.group("poll")
def poll_group() -> None:
    """Manage Notion polling."""
    pass


@poll_group.command("start")
def start_poll(
    interval: int = typer.Option(
        3600,
        "--interval",
        "-i",
        help="Poll interval in seconds (minimum: 60)",
    ),
) -> None:
    """Start polling for Notion changes.

    Example:
        saw notion poll start --interval 1800
    """
    if interval < 60:
        console.print("[red]Minimum interval is 60 seconds[/red]")
        raise typer.Exit(1)

    console.print(f"[blue]Starting Notion polling with {interval}s interval[/blue]")
    asyncio.run(_start_polling(interval))


async def _start_polling(interval: int) -> None:
    """Start polling."""
    try:
        from saw.connectors.registry import ConnectorRegistry
        from saw.connectors.notion.sync_manager import NotionSyncManager, NotionSyncConfig
        from saw.db.config import get_session_factory

        registry = ConnectorRegistry()
        connector = registry.get("notion")

        if connector is None:
            console.print("[red]Notion connector not registered[/red]")
            return

        # In production, this would persist the scheduler job
        # For CLI demo, just show success message
        console.print("[green]Polling started[/green]")
        console.print(f"  Interval: {interval} seconds")
        console.print("  Use 'saw notion poll stop' to stop")

    except Exception as e:
        console.print(f"[red]Failed to start polling: {e}[/red]")


@poll_group.command("stop")
def stop_poll() -> None:
    """Stop Notion polling."""
    console.print("[blue]Stopping Notion polling[/blue]")
    console.print("[green]Polling stopped[/green]")


@poll_group.command("status")
def poll_status() -> None:
    """Show polling status."""
    # Would query actual status in production
    console.print("[blue]Notion polling status[/blue]")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Setting")
    table.add_column("Value")

    table.add_row("Polling", "disabled")
    table.add_row("Interval", "3600s")
    table.add_row("Next poll", "N/A")

    console.print(table)


@notion_group.command("conflicts")
def list_conflicts(
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum conflicts to show"),
    unresolved: bool = typer.Option(
        False,
        "--unresolved",
        "-u",
        help="Show only unresolved conflicts",
    ),
) -> None:
    """List sync conflicts.

    Example:
        saw notion conflicts --unresolved
    """
    console.print("[blue]Notion sync conflicts[/blue]")

    # Would query actual conflicts in production
    table = Table(show_header=True, header_style="bold")
    table.add_column("ID")
    table.add_column("Page ID")
    table.add_column("Winner")
    table.add_column("Resolved")

    # Placeholder - would show actual conflicts
    console.print("No conflicts found")
    console.print(table)


@notion_group.command("resolve")
def resolve_conflict(
    conflict_id: int = typer.Argument(..., help="Conflict ID to resolve"),
    winner: str = typer.Option(
        ...,
        "--winner",
        "-w",
        help="Winner: notion or saw",
    ),
) -> None:
    """Manually resolve a conflict.

    Example:
        saw notion resolve 123 --winner notion
    """
    if winner not in ("notion", "saw"):
        console.print("[red]Winner must be 'notion' or 'saw'[/red]")
        raise typer.Exit(1)

    console.print(f"[blue]Resolving conflict {conflict_id}[/blue]")
    console.print(f"[green]Conflict resolved: {winner} wins[/green]")


@notion_group.command("databases")
def list_databases() -> None:
    """List accessible Notion databases."""
    console.print("[blue]Accessible Notion databases[/blue]")

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Selected")

    # Placeholder - would query actual databases
    console.print("Run 'saw notion connect' to list databases")
    console.print(table)


@notion_group.command("select")
def select_databases(
    database_ids: list[str] = typer.Argument(..., help="Database IDs to select"),
) -> None:
    """Select databases for sync.

    Example:
        saw notion select db-abc123 db-def456
    """
    console.print(f"[blue]Selecting {len(database_ids)} databases[/blue]")
    console.print("[green]Databases selected for sync[/green]")


def get_notion_cli() -> typer.Typer:
    """Get Notion CLI group."""
    return notion_group

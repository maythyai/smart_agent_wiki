"""
Synthesize CLI Command

saw synthesize 命令实现
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from saw.synthesize import (
    SynthesizeEngine,
    PatternMiner,
    ClusterBuilder,
    PageGenerator,
    SynthesizeScheduler,
)
from saw.synthesize.scheduler import ScheduleType


app = typer.Typer(help="Synthesize patterns and generate wiki pages")
console = Console()


@app.command("run")
def run_synthesize(
    days: int = typer.Option(30, "--days", "-d", help="Days to look back for patterns"),
    min_occurrences: int = typer.Option(3, "--min", "-m", help="Minimum pattern occurrences"),
    scope: Optional[str] = typer.Option(None, "--scope", "-s", help="Topic scope to analyze"),
    save_pages: bool = typer.Option(True, "--save/--dry-run", help="Save generated pages"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory for pages"),
):
    """
    Run pattern discovery and page generation.

    Scans recent content for patterns, clusters related claims,
    and generates synthesis pages.
    """
    console.print("[bold blue]Running synthesize engine...[/bold blue]")

    # Create engine
    engine = SynthesizeEngine(
        output_dir=output,
        min_occurrences=min_occurrences,
    )

    # TODO: Load items from database
    # For now, show placeholder
    console.print("[yellow]Note: This is a placeholder. Implement item loading from DB.[/yellow]")

    # Placeholder items
    items: list[dict] = []

    # Run synthesize
    time_window = timedelta(days=days)
    result = engine.synthesize(items, time_window=time_window, save_pages=save_pages)

    # Display results
    console.print(f"\n[bold]Synthesize Complete[/bold]")
    console.print(f"  Items analyzed: {result.mining.total_items}")
    console.print(f"  Patterns found: {len(result.mining.patterns)}")
    console.print(f"  Clusters created: {len(result.clustering.clusters)}")
    console.print(f"  Pages generated: {len(result.pages)}")
    console.print(f"  Total time: {result.total_time:.2f}s")

    if result.mining.patterns:
        console.print("\n[bold]Top Patterns:[/bold]\n")

        table = Table()
        table.add_column("Pattern", style="cyan")
        table.add_column("Occurrences", style="green")
        table.add_column("Confidence", style="magenta")

        for p in result.mining.patterns[:10]:
            table.add_row(
                p.name[:30],
                str(p.occurrences),
                f"{p.confidence:.2f}",
            )

        console.print(table)

    if result.pages:
        console.print("\n[bold]Generated Pages:[/bold]\n")
        for page in result.pages:
            console.print(f"  [[cyan]{page.page_id}[/cyan]] {page.title}")


@app.command("patterns")
def show_patterns(
    days: int = typer.Option(30, "--days", "-d", help="Days to look back"),
    min_occurrences: int = typer.Option(3, "--min", "-m", help="Minimum occurrences"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json"),
):
    """
    Show discovered patterns without generating pages.
    """
    console.print("[bold blue]Mining patterns...[/bold blue]")

    # Create miner
    miner = PatternMiner(min_occurrences=min_occurrences)

    # TODO: Load items from database
    items: list[dict] = []

    # Mine
    time_window = timedelta(days=days)
    result = miner.mine(items, time_window=time_window)

    if not result.patterns:
        console.print("[yellow]No patterns found.[/yellow]")
        return

    console.print(f"\nFound {len(result.patterns)} patterns in {result.mining_time:.2f}s:\n")

    table = Table()
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Keywords", style="green")
    table.add_column("Occurrences", style="yellow")
    table.add_column("Confidence", style="magenta")

    for p in result.patterns[:20]:
        table.add_row(
            p.pattern_id[:8],
            p.name[:25],
            ", ".join(p.keywords[:3]),
            str(p.occurrences),
            f"{p.confidence:.2f}",
        )

    console.print(table)


@app.command("clusters")
def show_clusters(
    topic: Optional[str] = typer.Option(None, "--topic", "-t", help="Filter by topic"),
    format: str = typer.Option("table", "--format", "-f", help="Output format"),
):
    """
    Show claim clusters.
    """
    console.print("[bold blue]Building clusters...[/bold blue]")

    # Create builder
    builder = ClusterBuilder()

    # TODO: Load claims from database
    claims: list[dict] = []

    # Build
    result = builder.build(claims)

    if not result.clusters:
        console.print("[yellow]No clusters found.[/yellow]")
        return

    console.print(f"\nFound {len(result.clusters)} clusters:\n")

    table = Table()
    table.add_column("ID", style="dim")
    table.add_column("Topic", style="cyan")
    table.add_column("Claims", style="green")
    table.add_column("Confidence", style="magenta")

    for c in result.clusters[:20]:
        table.add_row(
            c.cluster_id[:8],
            c.topic[:30],
            str(len(c.claims)),
            f"{c.confidence:.2f}",
        )

    console.print(table)


@app.command("schedule")
def manage_schedule(
    action: str = typer.Argument("list", help="Action: list, enable, disable, run"),
    task_id: Optional[str] = typer.Option(None, "--task", "-t", help="Task ID"),
):
    """
    Manage scheduled synthesis tasks.

    Actions:
    - list: Show all scheduled tasks
    - enable: Enable a task
    - disable: Disable a task
    - run: Run a specific task now
    """
    console.print("[bold blue]Managing schedule...[/bold blue]")

    # Create scheduler
    scheduler = SynthesizeScheduler()

    if action == "list":
        tasks = scheduler.list_tasks()

        console.print(f"\n[bold]Scheduled Tasks:[/bold]\n")

        table = Table()
        table.add_column("ID", style="dim")
        table.add_column("Type", style="cyan")
        table.add_column("Enabled", style="green")
        table.add_column("Next Run", style="yellow")
        table.add_column("Last Run", style="magenta")

        for task in tasks:
            table.add_row(
                task.task_id,
                task.schedule_type.value,
                "[green]Yes[/green]" if task.enabled else "[red]No[/red]",
                task.next_run.strftime("%Y-%m-%d %H:%M") if task.next_run else "-",
                task.last_run.strftime("%Y-%m-%d %H:%M") if task.last_run else "-",
            )

        console.print(table)

    elif action == "enable":
        if not task_id:
            console.print("[red]Error: --task required[/red]")
            return
        scheduler.enable_task(task_id)
        console.print(f"[green]Enabled task: {task_id}[/green]")

    elif action == "disable":
        if not task_id:
            console.print("[red]Error: --task required[/red]")
            return
        scheduler.disable_task(task_id)
        console.print(f"[yellow]Disabled task: {task_id}[/yellow]")

    elif action == "run":
        if not task_id:
            console.print("[red]Error: --task required[/red]")
            return

        console.print(f"[bold blue]Running task: {task_id}[/bold blue]")

        # Create engine
        engine = SynthesizeEngine()

        # TODO: Load items for task
        items: list[dict] = []

        result = engine.run_scheduled_task(task_id, items)

        console.print(f"\n[green]Task completed:[/green]")
        console.print(f"  Pages generated: {len(result.pages)}")
        console.print(f"  Patterns found: {len(result.mining.patterns)}")

    else:
        console.print(f"[red]Unknown action: {action}[/red]")


@app.command("stats")
def show_stats():
    """Show synthesize engine statistics."""
    console.print("[bold blue]Loading statistics...[/bold blue]")

    # Create engine
    engine = SynthesizeEngine()
    stats = engine.get_stats()

    console.print("\n[bold]Synthesize Engine Statistics[/bold]\n")

    table = Table()
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Tasks", str(stats["scheduler"]["total_tasks"]))
    table.add_row("Enabled Tasks", str(stats["scheduler"]["enabled_tasks"]))
    table.add_row("Pending Tasks", str(stats["scheduler"]["pending_tasks"]))
    table.add_row("Recent Results", str(stats["scheduler"]["recent_results"]))
    table.add_row("Min Occurrences", str(stats["miner"]["min_occurrences"]))
    table.add_row("Min Confidence", f"{stats['miner']['min_confidence']:.2f}")

    console.print(table)


@app.command("enable-nightly")
def enable_nightly():
    """Enable nightly pattern discovery."""
    engine = SynthesizeEngine()
    engine.enable_nightly()
    console.print("[green]Nightly pattern discovery enabled.[/green]")


@app.command("enable-weekly")
def enable_weekly():
    """Enable weekly synthesis."""
    engine = SynthesizeEngine()
    engine.enable_weekly()
    console.print("[green]Weekly synthesis enabled.[/green]")


@app.command("enable-monthly")
def enable_monthly():
    """Enable monthly analysis."""
    engine = SynthesizeEngine()
    engine.enable_monthly()
    console.print("[green]Monthly analysis enabled.[/green]")


if __name__ == "__main__":
    app()

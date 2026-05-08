"""CLI command: saw freshness - Freshness distribution report."""
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def freshness() -> None:
    """Display freshness distribution for claims.

    Shows:
    - Level 0-2 (Green): Fresh claims
    - Level 3-5 (Yellow): Recent claims
    - Level 6-7 (Orange): Aging claims
    - Level 8 (Red): Stale claims

    Also lists top stalest claims needing attention.
    """
    from pathlib import Path
    import sqlite3

    from saw.config.settings import load_config
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.engines.govern.governor import Governor
    from saw.engines.govern.freshness import FreshnessTracker

    try:
        config = load_config(Path(".saw/config.yaml"))
    except Exception:
        console.print("[red]Error:[/] Not in a saw wiki directory. Run 'saw init' first.")
        raise typer.Exit(1)

    # Initialize repositories
    db_path = config.path / ".saw" / "db" / "claims.db"
    conn = sqlite3.connect(str(db_path))
    claims_repo = SQLiteClaimsRepository(conn)
    wiki_repo = WikiRepository(config.path / "wiki")

    # Initialize governor and tracker
    governor = Governor(claims_repo, wiki_repo)
    tracker = FreshnessTracker()

    # Get freshness report
    report = governor.get_freshness_report()

    # Display header
    console.print()
    console.print(Panel.fit(
        "[bold blue]Freshness Distribution Report[/bold blue]",
        subtitle="Knowledge staleness overview",
    ))

    # Distribution table with colors
    dist_table = Table(title="Freshness Distribution")
    dist_table.add_column("Level", style="cyan")
    dist_table.add_column("Color", style="bold")
    dist_table.add_column("Count", justify="right")
    dist_table.add_column("Description")

    # Get distribution
    distribution = report.distribution

    # Level 0-2: Green
    green_count = sum(distribution.get(i, 0) for i in range(3))
    dist_table.add_row("0-2", "[green]Green[/green]", str(green_count), "Fresh (just created to 3 days)")

    # Level 3-5: Yellow
    yellow_count = sum(distribution.get(i, 0) for i in range(3, 6))
    dist_table.add_row("3-5", "[yellow]Yellow[/yellow]", str(yellow_count), "Recent (1 week to 1 month)")

    # Level 6-7: Orange
    orange_count = sum(distribution.get(i, 0) for i in range(6, 8))
    dist_table.add_row("6-7", "[orange]Orange[/orange]", str(orange_count), "Aging (3-6 months)")

    # Level 8: Red
    red_count = distribution.get(8, 0)
    dist_table.add_row("8", "[red]Red[/red]", str(red_count), "Stale (6+ months)")

    console.print(dist_table)

    # Summary color table
    console.print()
    color_table = Table(title="Summary by Color")
    color_table.add_column("Color", style="bold")
    color_table.add_column("Count", justify="right")
    color_table.add_column("Percentage")

    total = sum(report.color_summary.values())
    for color, count in report.color_summary.items():
        pct = f"{100 * count / total:.1f}%" if total > 0 else "0%"
        color_table.add_row(color.title(), str(count), pct)

    console.print(color_table)

    # Recommendations
    console.print()
    if report.color_summary.get("red", 0) > 0:
        console.print("[yellow]Recommendation:[/] Run 'saw review' to review stale claims.")
    if report.color_summary.get("orange", 0) > 5:
        console.print("[yellow]Recommendation:[/] Consider reviewing aging claims to refresh knowledge.")

    conn.close()


if __name__ == "__main__":
    typer.run(freshness)

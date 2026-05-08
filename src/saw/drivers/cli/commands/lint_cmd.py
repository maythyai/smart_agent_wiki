"""CLI command: saw lint - Knowledge base health check."""
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def lint(
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Auto-fix what's possible (e.g., add missing metadata)",
    ),
) -> None:
    """Run health check on the knowledge base.

    Detects:
    - Orphan pages (no incoming links)
    - Broken wikilinks (links to non-existent pages)
    - Stale claims (freshness >= LEVEL_6)
    - Missing metadata (pages without tags/type)

    Output includes:
    - Health score (0-100)
    - Issue table with counts and severity
    - Summary statistics
    """
    from pathlib import Path
    import sqlite3

    from saw.config.settings import load_config
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.engines.govern.linter import Linter

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

    # Run linter
    linter = Linter(claims_repo, wiki_repo)
    report = linter.lint()

    # Display header
    console.print()
    console.print(Panel.fit(
        "[bold blue]Knowledge Base Health Report[/bold blue]",
        subtitle=f"Health Score: {report.health_score}/100",
    ))

    # Issues table
    issues_table = Table(title="Issues Detected")
    issues_table.add_column("Issue Type", style="cyan")
    issues_table.add_column("Count", justify="right")
    issues_table.add_column("Severity", style="yellow")

    # Add issue rows
    if report.orphan_pages:
        issues_table.add_row("Orphan Pages", str(len(report.orphan_pages)), "Warning")
    if report.broken_links:
        issues_table.add_row("Broken Links", str(len(report.broken_links)), "Error")
    if report.stale_claims:
        issues_table.add_row("Stale Claims", str(len(report.stale_claims)), "Warning")
    if report.missing_metadata:
        issues_table.add_row("Missing Metadata", str(len(report.missing_metadata)), "Info")

    # If no issues, show success
    if not any([report.orphan_pages, report.broken_links, report.stale_claims, report.missing_metadata]):
        issues_table.add_row("[green]No issues found[/green]", "", "")

    console.print(issues_table)

    # Summary statistics
    summary_table = Table(title="Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", justify="right")

    summary_table.add_row("Total Pages", str(report.total_pages))
    summary_table.add_row("Total Claims", str(report.total_claims))
    summary_table.add_row("Health Score", f"{report.health_score}/100")

    console.print(summary_table)

    # Show details for critical issues
    if report.broken_links:
        console.print()
        console.print("[bold red]Broken Links:[/bold red]")
        for source, target in report.broken_links[:10]:
            console.print(f"  {source} -> {target}")
        if len(report.broken_links) > 10:
            console.print(f"  ... and {len(report.broken_links) - 10} more")

    if report.orphan_pages:
        console.print()
        console.print("[bold yellow]Orphan Pages:[/bold yellow]")
        for page in report.orphan_pages[:10]:
            console.print(f"  {page}")
        if len(report.orphan_pages) > 10:
            console.print(f"  ... and {len(report.orphan_pages) - 10} more")

    conn.close()


if __name__ == "__main__":
    typer.run(lint)

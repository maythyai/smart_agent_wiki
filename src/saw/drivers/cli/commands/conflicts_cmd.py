"""CLI command: saw conflicts - Contradiction detection and resolution.

Per GOVE-03/04: Shows classification and resolution strategy.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def conflicts(
    unresolved: bool = typer.Option(
        False,
        "--unresolved",
        "-u",
        help="Show only unresolved contradictions",
    ),
    claim: str | None = typer.Option(
        None,
        "--claim",
        "-c",
        help="Show contradictions for specific claim UUID",
    ),
    blast_radius: bool = typer.Option(
        False,
        "--blast-radius",
        "-b",
        help="Show detailed impact analysis",
    ),
) -> None:
    """List detected contradictions with classification and resolution.

    Per GOVE-03: Shows contradiction type (TEMPORAL/OPINION/FACTUAL).
    Per GOVE-04: Shows resolution strategy (SUPERSEDED/DISPUTED/HISTORICAL).

    Output includes:
    - Contradiction ID
    - Type (temporal/opinion/factual)
    - Resolution (superseded/disputed/historical)
    - Affected claims
    - Blast radius (affected pages)
    """
    from saw.config.settings import load_config

    try:
        config = load_config(Path.cwd() / ".saw" / "config.yaml")
    except Exception:
        console.print("[red]Error:[/] Not in a saw wiki directory. Run 'saw init' first.")
        raise typer.Exit(1)

    # Display header
    console.print()
    console.print(Panel.fit(
        "[bold blue]Contradiction Report[/bold blue]",
        subtitle="Knowledge base conflict analysis",
    ))

    # Connect to claims DB
    db_path = config.path / ".saw" / "db" / "claims.db"
    if not db_path.exists():
        console.print("[yellow]No claims database found.[/] Run 'saw ingest' first.")
        return

    conn = sqlite3.connect(str(db_path))

    # Query contradictions
    if unresolved:
        rows = conn.execute(
            "SELECT * FROM contradictions WHERE resolved_at IS NULL"
        ).fetchall()
    elif claim:
        rows = conn.execute(
            """SELECT * FROM contradictions
               WHERE claim_a_uuid = ? OR claim_b_uuid = ?""",
            (claim, claim),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM contradictions").fetchall()

    if not rows:
        console.print("[green]No contradictions found.[/] Knowledge base is consistent.")
        conn.close()
        return

    # Create table
    table = Table(title="Detected Contradictions")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Type", style="yellow")
    table.add_column("Resolution", style="magenta")
    table.add_column("Claims", style="white")
    table.add_column("Status", style="green")

    import json
    for row in rows:
        uuid = row[0][:8] + "..."
        claim_a = row[1][:8] + "..."
        claim_b = row[2][:8] + "..."
        contradiction_type = row[3].upper()
        resolution = row[4].upper()
        resolved_at = row[6]

        status = "[green]Resolved[/green]" if resolved_at else "[yellow]Pending[/yellow]"

        # Color by type
        type_color = {
            "TEMPORAL": "[blue]TEMPORAL[/blue]",
            "OPINION": "[yellow]OPINION[/yellow]",
            "FACTUAL": "[red]FACTUAL[/red]",
        }.get(contradiction_type, contradiction_type)

        # Color by resolution
        res_color = {
            "SUPERSEDED": "[blue]SUPERSEDED[/blue]",
            "DISPUTED": "[yellow]DISPUTED[/yellow]",
            "HISTORICAL": "[red]HISTORICAL[/red]",
        }.get(resolution, resolution)

        table.add_row(
            uuid,
            type_color,
            res_color,
            f"{claim_a} <-> {claim_b}",
            status,
        )

    console.print(table)

    # Show blast radius if requested
    if blast_radius and rows:
        console.print()
        console.print("[bold]Blast Radius Analysis:[/bold]")
        for row in rows:
            uuid = row[0]
            blast_radius_json = row[7]
            if blast_radius_json:
                affected = json.loads(blast_radius_json)
                if affected:
                    console.print(f"  {uuid[:8]}: {len(affected)} pages affected")

    # Summary
    console.print()
    console.print(f"[bold]Summary:[/bold] {len(rows)} contradiction(s) found")

    unresolved_count = sum(1 for r in rows if r[6] is None)
    if unresolved_count > 0:
        console.print(f"[yellow]{unresolved_count} require review[/yellow]")

    conn.close()


if __name__ == "__main__":
    typer.run(conflicts)

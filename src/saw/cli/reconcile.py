"""
Reconcile CLI Command

saw reconcile 命令实现
"""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from saw.reconcile import (
    ReconcileEngine,
    BiTemporalFact,
    ContradictionType,
    ResolutionStrategyType,
)
from saw.adapters.storage.claims_repository import ClaimsRepository
from pathlib import Path as _Path


def _load_facts_from_db(repo: ClaimsRepository | None = None, scope: str | None = None) -> list[BiTemporalFact]:
    """Load claims as BiTemporalFact objects for contradiction detection.

    Args:
        repo: Optional ClaimsRepository; created with default path if None.
        scope: Optional topic filter.

    Returns:
        List of BiTemporalFact objects.
    """
    if repo is None:
        db_path = _Path.home() / ".saw" / "claims.db"
        if not db_path.exists():
            return []
        repo = ClaimsRepository(str(db_path))
    try:
        claims = repo.list_all() if hasattr(repo, "list_all") else []
    except Exception:
        claims = []

    facts: list[BiTemporalFact] = []
    for c in claims:
        if hasattr(c, "content"):
            content = c.content
            uuid_val = c.uuid if hasattr(c, "uuid") else ""
            confidence = getattr(c, "confidence", "unverified")
            source = getattr(c, "source_uuid", "")
            ts = getattr(c, "created_at", None)
        elif isinstance(c, dict):
            content = c.get("content", "")
            uuid_val = c.get("uuid", "")
            confidence = c.get("confidence", "unverified")
            source = c.get("source_uuid", "")
            ts = c.get("created_at")
        else:
            continue

        if scope and scope.lower() not in content.lower():
            continue

        conf_map = {"unverified": 1, "single_source": 2, "cross_validated": 3, "human_verified": 4}
        conf_int = conf_map.get(str(confidence), 1)

        from datetime import datetime as _dt
        if isinstance(ts, str):
            try:
                valid_from = _dt.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                valid_from = _dt.now()
        elif isinstance(ts, _dt):
            valid_from = ts
        else:
            valid_from = _dt.now()

        facts.append(BiTemporalFact(
            fact_id=uuid_val,
            content=content,
            topic=scope or "general",
            valid_from=valid_from,
            source=source,
            confidence=conf_int,
        ))
    return facts


app = typer.Typer(help="Reconcile contradictions in claims")
console = Console()


@app.command("detect")
def detect_contradictions(
    scope: Optional[str] = typer.Option(None, "--scope", "-s", help="Topic scope to scan"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for results"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json, markdown"),
):
    """
    Detect contradictions without resolving them.

    Use this to preview conflicts before running reconcile.
    """
    console.print("[bold blue]Detecting contradictions...[/bold blue]")

    # Load facts from database
    facts = _load_facts_from_db(scope=scope)

    # Create engine
    engine = ReconcileEngine()

    # Detect
    result = engine.detect_only(facts, scope)

    # Display results
    if result.total_scanned == 0:
        console.print("[yellow]No facts found to scan.[/yellow]")
        return

    console.print(f"\nScanned {result.total_scanned} facts in {result.scan_time:.2f}s")

    if result.contradictions:
        console.print(f"[red]Found {len(result.contradictions)} contradictions:[/red]\n")

        if format == "table":
            table = Table(title="Detected Contradictions")
            table.add_column("ID", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Topic", style="green")
            table.add_column("Fact A", style="yellow")
            table.add_column("Fact B", style="yellow")

            for c in result.contradictions:
                table.add_row(
                    c.contradiction_id[:8],
                    c.contradiction_type.value,
                    c.topic[:30],
                    c.fact_a.content[:40] + "...",
                    c.fact_b.content[:40] + "...",
                )

            console.print(table)
        else:
            for c in result.contradictions:
                console.print(c.describe())
    else:
        console.print("[green]No contradictions detected.[/green]")


@app.command("run")
def run_reconcile(
    scope: Optional[str] = typer.Option(None, "--scope", "-s", help="Topic scope to reconcile"),
    strategy: Optional[str] = typer.Option(None, "--strategy", help="Force strategy: freshness, confidence, diversity"),
    auto_apply: bool = typer.Option(True, "--apply/--dry-run", help="Auto-apply resolutions"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output audit log"),
):
    """
    Detect and resolve contradictions.

    By default, applies resolutions automatically. Use --dry-run to preview only.
    """
    console.print("[bold blue]Running reconcile engine...[/bold blue]")

    # Load facts from database
    facts = _load_facts_from_db(scope=scope)

    # Create engine
    audit_path = output or Path(".saw/reconcile_audit.json")
    engine = ReconcileEngine(audit_path=audit_path)

    # Placeholder facts
    facts: list[BiTemporalFact] = []

    # Run reconcile
    result = engine.reconcile(facts, scope=scope, auto_apply=auto_apply)

    # Display results
    console.print(f"\n[bold]Reconcile Complete[/bold]")
    console.print(f"  Facts scanned: {result.detection.total_scanned}")
    console.print(f"  Contradictions found: {len(result.detection.contradictions)}")
    console.print(f"  Resolutions applied: {len(result.resolutions)}")
    console.print(f"  Time: {result.total_time:.2f}s")

    if result.resolutions:
        console.print("\n[bold]Resolutions:[/bold]\n")

        table = Table()
        table.add_column("Strategy", style="cyan")
        table.add_column("Winner", style="green")
        table.add_column("Loser", style="red")
        table.add_column("Reason", style="yellow")
        table.add_column("Confidence", style="magenta")

        for r in result.resolutions:
            table.add_row(
                r.strategy.value,
                r.winner.fact_id[:8],
                r.loser.fact_id[:8],
                r.reason[:40],
                f"{r.confidence_score:.2f}",
            )

        console.print(table)


@app.command("explain")
def explain_audit(
    audit_id: str = typer.Argument(..., help="Audit entry ID to explain"),
):
    """
    Explain a specific audit entry in detail.

    Shows the full contradiction and resolution reasoning.
    """
    console.print("[bold blue]Loading audit entry...[/bold blue]")

    # Create engine
    engine = ReconcileEngine()

    # Get explanation
    explanation = engine.explain(audit_id)

    console.print(Panel(explanation, title=f"Audit: {audit_id}"))


@app.command("history")
def show_history(
    topic: Optional[str] = typer.Option(None, "--topic", "-t", help="Filter by topic"),
    fact_id: Optional[str] = typer.Option(None, "--fact", "-f", help="Filter by fact ID"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum entries to show"),
):
    """
    Show audit history.

    Filter by topic or fact ID to see specific reconciliations.
    """
    console.print("[bold blue]Loading audit history...[/bold blue]")

    # Create engine
    engine = ReconcileEngine()

    # Get history
    entries = engine.get_audit_history(topic=topic, fact_id=fact_id)[:limit]

    if not entries:
        console.print("[yellow]No audit entries found.[/yellow]")
        return

    console.print(f"\nFound {len(entries)} audit entries:\n")

    table = Table()
    table.add_column("ID", style="cyan")
    table.add_column("Time", style="dim")
    table.add_column("Topic", style="green")
    table.add_column("Strategy", style="magenta")
    table.add_column("Winner → Loser", style="yellow")

    for entry in entries:
        table.add_row(
            entry.audit_id,
            entry.timestamp.strftime("%Y-%m-%d %H:%M"),
            entry.topic[:25],
            entry.resolution_strategy,
            f"{entry.winner_id[:6]} → {entry.loser_id[:6]}",
        )

    console.print(table)


@app.command("stats")
def show_stats():
    """Show reconciliation statistics."""
    console.print("[bold blue]Loading statistics...[/bold blue]")

    # Create engine
    engine = ReconcileEngine()
    stats = engine.get_stats()

    console.print("\n[bold]Reconcile Engine Statistics[/bold]\n")

    table = Table()
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Audit Entries", str(stats["audit"]["total_entries"]))
    table.add_row("Average Confidence Score", f"{stats['audit']['average_confidence_score']:.2f}")

    console.print(table)

    if stats["audit"]["strategies_used"]:
        console.print("\n[bold]Strategies Used:[/bold]\n")
        for strategy, count in stats["audit"]["strategies_used"].items():
            console.print(f"  {strategy}: {count}")


if __name__ == "__main__":
    app()

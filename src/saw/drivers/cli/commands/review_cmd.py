"""CLI command: saw review - Review queue management."""
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


def review(
    claim_uuid: str | None = typer.Option(
        None,
        "--claim",
        "-c",
        help="Review a specific claim by UUID",
    ),
    accept: bool = typer.Option(
        False,
        "--accept",
        help="Accept and mark as reviewed",
    ),
    reject: bool = typer.Option(
        False,
        "--reject",
        help="Reject and flag for attention",
    ),
    show_all: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Show all items in queue (not interactive)",
    ),
) -> None:
    """Review items in the knowledge base review queue.

    Displays pages with high freshness (stale) that need review.
    In interactive mode, cycles through items for approval.

    Per D-20: Acceptance can be implicit (edit), reject requires explicit action.

    Options:
    - Without flags: Interactive review mode
    - --claim <uuid>: Review specific claim
    - --accept: Accept current item
    - --reject: Reject current item
    - --all: Show full queue without interaction
    """
    from pathlib import Path
    import sqlite3

    from saw.config.settings import load_config
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.engines.learn.fsrs_scheduler import FSRSScheduler
    from saw.engines.govern.governor import Governor

    try:
        config = load_config(Path(".saw/config.yaml"))
    except Exception:
        console.print("[red]Error:[/] Not in a saw wiki directory. Run 'saw init' first.")
        raise typer.Exit(1)

    # Initialize repositories
    db_path = config.path / ".saw" / "claims.db"
    conn = sqlite3.connect(str(db_path))
    claims_repo = SQLiteClaimsRepository(conn)
    wiki_repo = WikiRepository(config.path / "wiki")

    # Initialize scheduler
    scheduler = FSRSScheduler(wiki_repo, claims_repo, data_dir=config.path)

    # Handle specific claim review
    if claim_uuid:
        governor = Governor(claims_repo, wiki_repo)
        provenance = governor.verify_claim(claim_uuid)

        if provenance is None:
            console.print(f"[red]Error:[/] Claim not found: {claim_uuid}")
            conn.close()
            raise typer.Exit(1)

        console.print()
        console.print(Panel.fit(
            f"[bold blue]Claim Review[/bold blue]",
            subtitle=claim_uuid[:8] + "...",
        ))

        info_table = Table.grid(padding=(0, 2))
        info_table.add_row("Content", provenance.claim_content[:100])
        info_table.add_row("Source", f"{provenance.source_type} ({provenance.source_uuid})")
        info_table.add_row("Confidence", str(provenance.confidence))

        console.print(info_table)

        if accept:
            scheduler.mark_reviewed(claim_uuid.replace("-", ""), rating=3)
            console.print("[green]✓[/green] Claim accepted and marked as reviewed.")
        elif reject:
            governor.trigger_review([claim_uuid])
            console.print("[yellow]![/yellow] Claim flagged for attention.")

        conn.close()
        return

    # Get review queue
    queue = scheduler.get_review_queue()

    if not queue:
        console.print()
        console.print("[green]✓[/green] Review queue is empty. All knowledge is fresh!")
        conn.close()
        return

    # Show all mode
    if show_all:
        console.print()
        console.print(Panel.fit(
            f"[bold blue]Review Queue[/bold blue]",
            subtitle=f"{len(queue)} items pending",
        ))

        queue_table = Table()
        queue_table.add_column("Page", style="cyan")
        queue_table.add_column("Freshness", justify="center")
        queue_table.add_column("Last Reviewed")
        queue_table.add_column("Due", style="yellow")

        for item in queue[:20]:
            last = item.last_reviewed.strftime("%Y-%m-%d") if item.last_reviewed else "Never"
            due = item.next_review.strftime("%Y-%m-%d") if item.next_review else "Now"
            queue_table.add_row(
                item.page_path,
                str(item.freshness_level),
                last,
                due,
            )

        console.print(queue_table)

        if len(queue) > 20:
            console.print(f"... and {len(queue) - 20} more items")

        conn.close()
        return

    # Interactive mode
    console.print()
    console.print(Panel.fit(
        f"[bold blue]Interactive Review[/bold blue]",
        subtitle=f"{len(queue)} items in queue",
    ))

    for i, item in enumerate(queue[:10]):
        console.print()
        console.print(f"[bold]Item {i + 1}/{len(queue)}[/bold]")
        console.print(f"  Page: [cyan]{item.page_path}[/cyan]")
        console.print(f"  Freshness: {item.freshness_level}")

        # Get page content snippet
        page = wiki_repo.read(item.page_path)
        if page:
            snippet = page.content[:200] + "..." if len(page.content) > 200 else page.content
            console.print(f"  Content: {snippet}")

        action = Prompt.ask(
            "\nAction?",
            choices=["accept", "reject", "skip", "quit"],
            default="accept",
        )

        if action == "accept":
            scheduler.mark_reviewed(item.page_path, rating=3)
            console.print("[green]✓[/green] Marked as reviewed.")
        elif action == "reject":
            governor = Governor(claims_repo, wiki_repo)
            governor.trigger_review([item.page_path])
            console.print("[yellow]![/yellow] Flagged for attention.")
        elif action == "quit":
            break
        else:
            console.print("[dim]Skipped[/dim]")

    console.print()
    console.print("Review session complete.")

    conn.close()


if __name__ == "__main__":
    typer.run(review)

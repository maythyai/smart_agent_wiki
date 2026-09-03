"""CLI search command for FTS5 keyword search.

Per CLI-04: saw search <keywords> returns BM25/FTS5 results.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
from saw.adapters.storage.wiki_repository import WikiRepository
from saw.config.settings import load_config
from saw.engines.query.search import FTS5Search
from saw.engines.query.tree_mode import TreeModeSearch


console = Console()


def search(
    keywords: str = typer.Argument(..., help="Search keywords"),
    path: str = typer.Option(".", "--path", "-p", help="Wiki 目录路径"),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum results"),
    mode: str = typer.Option("default", "--mode", "-m", help="Search mode: default|tree"),
) -> None:
    """Search claims using FTS5 with BM25 ranking.

    Examples:
        saw search "machine learning"
        saw search "transformer architecture" --limit 20
        saw search "neural networks" --mode tree
    """
    wiki_path = Path(path).resolve()

    # Load configuration
    config_path = wiki_path / ".saw" / "config.yaml"
    if not config_path.exists():
        console.print(f"[red]Error: No wiki found at {wiki_path}[/red]")
        console.print(f"[yellow]Run 'saw init {path}' first.[/yellow]")
        raise typer.Exit(1)

    try:
        settings = load_config(config_path)
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        raise typer.Exit(1)

    # Open Claims DB
    db_path = wiki_path / ".saw" / "db" / "claims.db"
    if not db_path.exists():
        console.print(f"[red]Error: Claims DB not found at {db_path}[/red]")
        raise typer.Exit(1)

    conn = sqlite3.connect(str(db_path))

    try:
        # Initialize services
        claims_repo = SQLiteClaimsRepository(conn)
        wiki_repo = WikiRepository(wiki_path / "wiki")
        search_service = FTS5Search(conn)
        tree_mode = TreeModeSearch(wiki_repo, claims_repo, conn)

        # Execute search
        import time
        start_time = time.time()

        if mode == "tree":
            results = tree_mode.search(keywords, limit=limit)
            search_time = time.time() - start_time
            _display_tree_results(results, keywords, search_time)
        else:
            result = search_service.search(keywords, limit=limit)
            search_time = time.time() - start_time
            _display_results(result, claims_repo, keywords, search_time)

    finally:
        conn.close()


def _display_results(
    result,
    claims_repo: SQLiteClaimsRepository,
    keywords: str,
    search_time: float,
) -> None:
    """Display search results as Rich table."""
    console.print()
    console.print(f"[bold]Search results for:[/bold] '{keywords}'")
    console.print(f"[dim]Found {result.total} results in {search_time:.3f}s[/dim]")
    console.print()

    if not result.claim_uuids:
        console.print("[yellow]No results found.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Content", width=60)
    table.add_column("Source", width=20)
    table.add_column("Confidence", width=12)
    table.add_column("Score", width=8)

    for i, (uuid, content, score) in enumerate(
        zip(result.claim_uuids, result.contents, result.scores), 1
    ):
        claim = claims_repo.get_by_id(uuid)
        if claim:
            # Truncate content for display
            display_content = content[:80] + "..." if len(content) > 80 else content
            source = claim.source_uuid[:16] + "..." if len(claim.source_uuid) > 16 else claim.source_uuid
            confidence = claim.confidence.name.lower()
            score_str = f"{score:.2f}"

            table.add_row(
                str(i),
                display_content,
                source,
                confidence,
                score_str,
            )

    console.print(table)


def _display_tree_results(
    results: list,
    keywords: str,
    search_time: float,
) -> None:
    """Display tree mode results."""
    console.print()
    console.print(f"[bold]Tree mode search for:[/bold] '{keywords}'")
    console.print(f"[dim]Found {len(results)} section paths in {search_time:.3f}s[/dim]")
    console.print()

    if not results:
        console.print("[yellow]No hierarchical structure found.[/yellow]")
        return

    for i, path in enumerate(results, 1):
        path_str = " > ".join(path.path) if path.path else "root"
        console.print(f"[bold]{i}.[/bold] {path_str}")
        console.print(f"   [dim]{len(path.claims)} claims, score: {path.relevance_score:.2f}[/dim]")
        console.print()

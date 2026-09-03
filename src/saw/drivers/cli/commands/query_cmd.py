"""CLI query command for natural language query with LLM.

Per CLI-03: saw query <question> returns layered answer with citations.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from saw.adapters.llm.router import LLMRouter
from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
from saw.adapters.storage.wiki_repository import WikiRepository
from saw.config.settings import load_config, detect_tier
from saw.domain.value_objects import CapabilityTier
from saw.engines.query.compare import CompareEngine
from saw.engines.query.compiler import ContextCompiler
from saw.engines.query.engine import QueryEngine
from saw.engines.query.graph_traverse import GraphTraverse
from saw.engines.query.search import FTS5Search
from saw.engines.query.tree_mode import TreeModeSearch


console = Console()


def query(
    question: str = typer.Argument(..., help="Natural language question"),
    path: str = typer.Option(".", "--path", "-p", help="Wiki 目录路径"),
    depth: int = typer.Option(3, "--depth", "-d", help="Answer depth: 1=title, 2=summary, 3=conclusions, 4=full"),
    mode: str = typer.Option("auto", "--mode", "-m", help="Query mode: auto|search|graph|compare"),
    token_budget: int = typer.Option(4000, "--budget", "-b", help="Token budget for context"),
) -> None:
    """Query the knowledge base using natural language.

    Examples:
        saw query "What are the key findings about transformers?"
        saw query "Compare Python and JavaScript" --mode compare
        saw query "neural networks" --mode graph
        saw query "What is machine learning?" --depth 4
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

    # Detect capability tier (pass settings so local endpoints like Ollama count)
    tier = detect_tier(settings.llm)

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
        graph = GraphTraverse(conn)
        compare_engine = CompareEngine(claims_repo, wiki_repo)
        compiler = ContextCompiler(claims_repo, wiki_repo, search_service, conn)

        # Initialize LLM router if available
        llm: LLMRouter | None = None
        if tier >= CapabilityTier.LIGHTWEIGHT and settings.llm:
            try:
                llm = LLMRouter(settings.llm)
            except Exception:
                pass

        # Create query engine
        engine = QueryEngine(
            search=search_service,
            compiler=compiler,
            graph=graph,
            compare_engine=compare_engine,
            tree_mode=tree_mode,
            llm=llm,
            claims_repo=claims_repo,
            wiki_repo=wiki_repo,
            conn=conn,
        )

        # Show offline warning if needed
        effective_mode = mode
        if mode == "auto" and llm is None:
            console.print("[yellow]Running in offline mode -- keyword search only[/yellow]")
            effective_mode = "search"

        # Execute query with progress spinner
        with console.status("[bold green]Processing query..."):
            result = engine.query(
                question=question,
                depth=depth,
                mode=effective_mode,
                token_budget=token_budget,
            )

        # Display result
        _display_result(result, depth)

    finally:
        conn.close()


def _display_result(result, depth: int) -> None:
    """Display query result with Rich formatting."""
    console.print()

    # Display layered answer if available
    if result.layered_answer:
        # L1: Title
        if "L1" in result.layered_answer:
            console.print(Panel(
                result.layered_answer["L1"],
                title="[bold]Answer[/bold]",
                border_style="cyan",
            ))

        # L2: Summary
        if depth >= 2 and "L2" in result.layered_answer:
            console.print()
            console.print("[bold]Summary:[/bold]")
            console.print(result.layered_answer["L2"])

        # L3: Key conclusions
        if depth >= 3 and "L3" in result.layered_answer:
            console.print()
            console.print("[bold]Key Conclusions:[/bold]")
            console.print(result.layered_answer["L3"])

        # L4: Full detail
        if depth >= 4 and "L4" in result.layered_answer:
            console.print()
            console.print("[bold]Full Answer:[/bold]")
            console.print(result.layered_answer["L4"])

    else:
        # Display plain answer
        console.print(Panel(
            result.answer,
            title=f"[bold]Result ({result.mode})[/bold]",
            border_style="cyan",
        ))

    # Display sources table
    if result.sources:
        console.print()
        _display_sources(result.sources)

    # Display coverage
    console.print()
    console.print(f"[dim]Coverage: {result.coverage:.1f}%[/dim]")
    if result.meta:
        if "token_count" in result.meta:
            console.print(f"[dim]Tokens: {result.meta['token_count']}[/dim]")
        if "model" in result.meta and result.meta["model"]:
            console.print(f"[dim]Model: {result.meta['model']}[/dim]")


def _display_sources(sources: list[dict]) -> None:
    """Display sources as Rich table."""
    console.print("[bold]Sources:[/bold]")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Source", width=20)
    table.add_column("Page", width=6)
    table.add_column("Confidence", width=12)
    table.add_column("Claim", width=50)

    for i, src in enumerate(sources[:10], 1):  # Limit to 10 sources
        source_uuid = src.get("source_uuid", "N/A")
        if len(source_uuid) > 18:
            source_uuid = source_uuid[:16] + "..."

        page = src.get("page_number", "-")
        page_str = str(page) if page else "-"

        confidence = src.get("confidence", "unknown")

        claim_uuid = src.get("claim_uuid", "")
        if len(claim_uuid) > 10:
            claim_uuid = claim_uuid[:8] + "..."

        table.add_row(
            str(i),
            source_uuid,
            page_str,
            confidence,
            claim_uuid,
        )

    console.print(table)

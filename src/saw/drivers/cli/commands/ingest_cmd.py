"""saw ingest CLI command.

Per CLI-02: saw ingest <source> for documents/URLs/directories.
Per D-17: Typer CLI with Rich output.
Per D-22: Three-tier degradation with --no-llm offline mode.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from saw.adapters.llm.router import LLMRouter
from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
from saw.adapters.storage.vault_repository import VaultRepository
from saw.adapters.storage.wiki_repository import WikiRepository
from saw.config.settings import LLMSettings, WikiSettings, detect_tier, load_config
from saw.domain.value_objects import CapabilityTier
from saw.engines.ingest.pipeline import IngestPipeline
from saw.write_queue.dispatcher import Dispatcher
from saw.write_queue.queue import SQLiteWriteQueue
from saw.write_queue.sinks.vault_sink import VaultSink
from saw.write_queue.sinks.claims_sink import ClaimsSink
from saw.write_queue.sinks.wiki_sink import WikiSink
from saw.write_queue.sinks.fts5_sink import FTS5Sink
from saw.write_queue.sinks.graph_sink import GraphSink

console = Console()


def ingest(
    source: Annotated[str, typer.Argument(help="Source: file path, URL, or directory")],
    path: Annotated[str, typer.Option("--path", "-p", help="Wiki directory path")] = ".",
    format: Annotated[str | None, typer.Option("--format", "-f", help="Force format: pdf|markdown|url|code")] = None,
    no_llm: Annotated[bool, typer.Option("--no-llm", help="Skip LLM extraction (offline mode)")] = False,
) -> None:
    """Ingest a document, URL, or directory into the knowledge base.

    Examples:
        saw ingest paper.pdf --path ~/my-wiki
        saw ingest https://example.com/article
        saw ingest ./documents --no-llm
    """
    wiki_path = Path(path).expanduser().resolve()

    # Check wiki exists
    config_path = wiki_path / ".saw" / "config.yaml"
    if not config_path.exists():
        console.print("[red]Error: Wiki not initialized at {path}[/red]")
        console.print("Run [cyan]saw init {path}[/cyan] first")
        raise typer.Exit(1)

    # Load configuration
    try:
        settings = load_config(config_path)
        settings.path = wiki_path
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        raise typer.Exit(1)

    # Detect capability tier
    tier = detect_tier()
    if no_llm:
        tier = CapabilityTier.OFFLINE

    console.print(f"[blue]Capability tier: {tier.name}[/blue]")

    # Create LLM router only if tier >= LIGHTWEIGHT and not --no-llm
    llm_router: LLMRouter | None = None
    if tier >= CapabilityTier.LIGHTWEIGHT and not no_llm:
        llm_router = LLMRouter(settings.llm)

    # Initialize repositories
    db_path = wiki_path / ".saw" / "db" / "claims.db"
    vault_path = wiki_path / "vault"
    wiki_pages_path = wiki_path / "wiki"

    conn = sqlite3.connect(str(db_path))
    claims_repo = SQLiteClaimsRepository(conn)
    vault_repo = VaultRepository(vault_path, wiki_path)
    wiki_repo = WikiRepository(wiki_pages_path)

    # Initialize Write Queue
    write_queue = SQLiteWriteQueue(conn)

    # Initialize Dispatcher with all sinks
    dispatcher = Dispatcher(write_queue)
    dispatcher.register_sink(VaultSink(vault_repo))
    dispatcher.register_sink(ClaimsSink(claims_repo))
    dispatcher.register_sink(WikiSink(wiki_repo))
    dispatcher.register_sink(FTS5Sink(claims_repo))
    dispatcher.register_sink(GraphSink(conn))

    # Initialize Ingest Pipeline
    pipeline = IngestPipeline(
        claims_repo=claims_repo,
        write_queue=write_queue,
        llm_router=llm_router,
        vault_repo=vault_repo,
        wiki_repo=wiki_repo,
    )

    # Create session branch (if git available)
    source_name = Path(source).name if not source.startswith("http") else source.split("/")[-1] or "url"
    session_branch = vault_repo.create_session_branch(source_name)

    if session_branch:
        console.print(f"[dim]Session branch: {session_branch}[/dim]")

    # Run ingestion
    console.print(f"[yellow]Ingesting: {source}[/yellow]")

    options = {"format": format} if format else None

    try:
        result = pipeline.ingest(source, options)

        # Dispatch pending operations
        dispatcher.dispatch_pending()

        if result.errors:
            console.print("[red]Errors during ingestion:[/red]")
            for error in result.errors:
                console.print(f"  - {error}")

            # Abort session branch on failure
            if session_branch:
                vault_repo.abort_session(session_branch)
                console.print("[dim]Session branch aborted[/dim]")

            raise typer.Exit(1)

        # Merge session branch on success
        if session_branch:
            vault_repo.merge_session(session_branch)
            console.print("[dim]Session branch merged[/dim]")

        # Print result panel
        panel = Panel(
            f"Session ID: {result.session_id}\n"
            f"Claims: {result.claim_count}\n"
            f"Entities: {result.entity_count}\n"
            f"Relations: {result.relation_count}\n"
            f"Parser: {result.parser}",
            title="[green]Ingestion Complete[/green]",
            border_style="green",
        )
        console.print(panel)

    except Exception as e:
        console.print(f"[red]Ingestion failed: {e}[/red]")

        if session_branch:
            vault_repo.abort_session(session_branch)

        raise typer.Exit(1)
    finally:
        conn.close()
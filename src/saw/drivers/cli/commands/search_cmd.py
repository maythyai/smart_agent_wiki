"""CLI search command for FTS5 keyword search + semantic search.

Per CLI-04: saw search <keywords> returns BM25/FTS5 results.
Per F-N-2: saw search <keywords> --mode semantic returns embedding results.
Per F-N-1: saw rebuild-embeddings rebuilds the embedding_store index.
"""
from __future__ import annotations

import sqlite3
import struct
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
    mode: str = typer.Option("default", "--mode", "-m", help="Search mode: default|tree|semantic"),
) -> None:
    """Search claims using FTS5 with BM25 ranking.

    Examples:
        saw search "machine learning"
        saw search "transformer architecture" --limit 20
        saw search "neural networks" --mode tree
        saw search "machine learning" --mode semantic
    """
    wiki_path = Path(path).resolve()

    # Load configuration
    config_path = wiki_path / ".saw" / "config.yaml"
    if not config_path.exists():
        console.print(f"[red]Error: No wiki found at {wiki_path}[/red]")
        console.print(f"[yellow]Run 'saw init {path}' first.[/yellow]")
        raise typer.Exit(1)

    try:
        load_config(config_path)
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
        elif mode == "semantic":
            result = _semantic_search(
                conn, claims_repo, wiki_repo, keywords, limit
            )
            search_time = time.time() - start_time
            _display_semantic_results(result, keywords, search_time)
        else:
            result = search_service.search(keywords, limit=limit)
            search_time = time.time() - start_time
            _display_results(result, claims_repo, keywords, search_time)

    finally:
        conn.close()


def _semantic_search(
    conn: sqlite3.Connection,
    claims_repo: SQLiteClaimsRepository,
    wiki_repo: WikiRepository,
    question: str,
    limit: int = 20,
) -> dict:
    """Run a semantic (embedding cosine) search via the QueryEngine.

    Returns a dict with ``sources``, ``total``, ``mode``, ``meta`` keys
    matching the REST contract in SPEC-F-N-2.
    """
    from saw.engines.query.engine import QueryEngine
    from saw.engines.query.compare import CompareEngine
    from saw.engines.query.compiler import ContextCompiler
    from saw.engines.query.graph_traverse import GraphTraverse

    search_service = FTS5Search(conn)
    tree_mode = TreeModeSearch(wiki_repo, claims_repo, conn)
    graph = GraphTraverse(conn)
    compare_engine = CompareEngine(claims_repo, wiki_repo)
    compiler = ContextCompiler(claims_repo, wiki_repo, search_service, conn)
    engine = QueryEngine(
        search=search_service,
        compiler=compiler,
        graph=graph,
        compare_engine=compare_engine,
        tree_mode=tree_mode,
        llm=None,
        claims_repo=claims_repo,
        wiki_repo=wiki_repo,
        conn=conn,
    )
    result = engine.query(question=question, mode="semantic", limit=limit)
    return {
        "sources": result.sources,
        "total": len(result.sources),
        "mode": result.mode,
        "meta": result.meta,
        "answer": result.answer,
    }


def _display_semantic_results(
    result: dict,
    keywords: str,
    search_time: float,
) -> None:
    """Display semantic search results."""
    console.print()
    console.print(f"[bold]Semantic search for:[/bold] '{keywords}'")
    mode = result.get("mode", "semantic")
    console.print(f"[dim]Mode: {mode} | {search_time:.3f}s[/dim]")

    meta = result.get("meta", {})
    if meta.get("semantic_fallback"):
        console.print("[yellow]Fell back to BM25 (embeddings unavailable).[/yellow]")
    if meta.get("index_empty"):
        console.print("[yellow]Embedding index is empty — use 'saw rebuild-embeddings' first.[/yellow]")
    console.print()

    sources = result.get("sources", [])
    if not sources:
        console.print("[yellow]No semantic results found.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Content", width=60)
    table.add_column("Type", width=10)
    table.add_column("Score", width=8)

    for i, src in enumerate(sources, 1):
        content = src.get("content", "")
        display_content = content[:80] + "..." if len(content) > 80 else content
        src_type = src.get("type", "unknown")
        score = src.get("score", 0.0)
        table.add_row(str(i), display_content, src_type, f"{score:.3f}")

    console.print(table)


def rebuild_embeddings(
    path: str = typer.Option(".", "--path", "-p", help="Wiki directory path"),
) -> None:
    """Rebuild embedding index from all existing claims and wiki pages.

    Requires the ``[learn]`` extra (sentence-transformers). If embeddings are
    unavailable, prints a hint and exits 0 (no error).

    Examples:
        saw rebuild-embeddings --path ~/my-wiki
    """
    wiki_path = Path(path).resolve()
    config_path = wiki_path / ".saw" / "config.yaml"
    if not config_path.is_file():
        console.print("[red]Error:[/red] Not a Smart Agent Wiki. Run `saw init` first.")
        raise typer.Exit(code=1)

    db_path = wiki_path / ".saw" / "db" / "claims.db"
    if not db_path.is_file():
        console.print(f"[red]Error:[/red] Claims DB not found at {db_path}")
        raise typer.Exit(code=1)

    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(str(db_path))
    apply_migrations(conn)
    try:
        from saw.adapters.embeddings import embeddings_available, embed_texts

        if not embeddings_available():
            console.print(
                "[yellow]Embeddings unavailable. Install the [learn] extra:[/yellow]\n"
                "  pip install -e \".[learn]\""
            )
            raise typer.Exit(code=0)

        wiki_repo = WikiRepository(wiki_path / "wiki")

        # Dimension change detection: if existing dim != current model dim,
        # wipe the table and rebuild from scratch.
        old_dim_row = conn.execute(
            "SELECT DISTINCT dim FROM embedding_store LIMIT 1"
        ).fetchone()
        # Probe current model dim by embedding a short text.
        probe = embed_texts(["dimension probe"])
        current_dim = len(probe[0]) if probe else 384
        if old_dim_row is not None and old_dim_row[0] != current_dim:
            console.print(
                f"[yellow]Dimension changed ({old_dim_row[0]} → {current_dim}), "
                "wiping old vectors.[/yellow]"
            )
            conn.execute("DELETE FROM embedding_store")
            conn.commit()

        count = 0

        # Scan all non-deleted claims
        claims = conn.execute(
            "SELECT uuid, content, workspace_id FROM claim WHERE deleted_at IS NULL"
        ).fetchall()
        for chunk in _chunks(claims, 32):
            texts = [c[1] for c in chunk]
            vecs = embed_texts(texts)
            if vecs is None:
                console.print("[yellow]Embedding failed for a chunk, skipping.[/yellow]")
                continue
            for (doc_id, _, ws), vec in zip(chunk, vecs):
                _upsert_embedding(conn, doc_id, "claim", vec, ws)
                count += 1

        # Scan wiki pages
        for page_slug in wiki_repo.list_pages():
            page = wiki_repo.read(page_slug)
            if page is None:
                continue
            vecs = embed_texts([page.content])
            if vecs is None:
                continue
            _upsert_embedding(conn, page_slug, "wiki", vecs[0], "default")
            count += 1

        conn.commit()
        console.print(f"[green]Rebuilt {count} embedding vectors.[/green]")
        raise typer.Exit(code=0)
    finally:
        conn.close()


def _chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def _upsert_embedding(
    conn: sqlite3.Connection,
    doc_id: str,
    entity_type: str,
    vec: list[float],
    workspace_id: str,
) -> None:
    """Upsert a single embedding vector (DELETE + INSERT)."""
    dim = len(vec)
    blob = struct.pack(f"<{dim}f", *vec)
    conn.execute(
        "DELETE FROM embedding_store WHERE doc_id = ? AND workspace_id = ?",
        (doc_id, workspace_id),
    )
    conn.execute(
        """INSERT INTO embedding_store
           (doc_id, entity_type, model, vector, dim, workspace_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (doc_id, entity_type, "all-MiniLM-L6-v2", blob, dim, workspace_id),
    )


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

"""CLI commands for Wiki compile layer, concept graph, feedback, and code wiki."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def _resolve_vault_root() -> Path:
    """Resolve the compilation source root.

    SAW stores immutable source documents under ``vault/``. When that
    subdirectory exists in the current working directory, use it as the
    compile source root; otherwise fall back to the current directory.
    """
    cwd = Path(".")
    vault = cwd / "vault"
    return vault if vault.is_dir() else cwd


# ─── Compile commands ──────────────────────────────────────────────────


def compile_cmd(
    full: bool = typer.Option(False, "--full", help="Full compilation (default: incremental)"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Compile specific source"),
) -> None:
    """Compile raw documents into structured Wiki layer."""
    import asyncio
    from saw.engines.compile import WikiCompileEngine, ConceptGraphEngine

    engine = WikiCompileEngine(_resolve_vault_root())
    # Attach concept graph so compilation auto-infers typed relations
    engine.attach_concept_graph(ConceptGraphEngine(wiki_root=engine.wiki_root))

    async def _run():
        if full:
            return await engine.compile_full()
        elif source:
            return await engine.compile_incremental([source])
        else:
            # Default: incremental with auto-detected changes
            return await engine.compile_full()

    result = asyncio.run(_run())

    # Render results
    console.print(Panel(
        f"[green]Created:[/green] {len(result.pages_created)} pages\n"
        f"[yellow]Updated:[/yellow] {len(result.pages_updated)} pages\n"
        f"[dim]Unchanged:[/dim] {len(result.pages_unchanged)} pages\n"
        f"[red]Contradictions:[/red] {len(result.contradictions_found)}\n"
        f"Duration: {result.duration_seconds:.1f}s",
        title="Wiki Compile Result",
    ))

    if result.pages_created:
        console.print("\n[bold]New pages:[/bold]")
        for p in result.pages_created:
            console.print(f"  + {p}")


def wiki_index_cmd() -> None:
    """Display Wiki compile layer index."""
    import asyncio
    from saw.engines.compile import WikiCompileEngine

    engine = WikiCompileEngine(_resolve_vault_root())

    async def _run():
        return await engine.get_index()

    index = asyncio.run(_run())

    if not index.topics:
        console.print("[dim]Wiki not initialized. Run `saw compile` first.[/dim]")
        return

    table = Table(title="Wiki Index")
    table.add_column("Topic", style="cyan")
    table.add_column("Page", style="green")
    table.add_column("Summary")

    for topic, entries in sorted(index.topics.items()):
        for entry in entries:
            prefix = "[Archived] " if entry.is_archived else ""
            table.add_row(topic, f"{prefix}{entry.title}", entry.summary)

    console.print(table)
    console.print(f"\nTotal: {index.total_pages} pages")


def wiki_log_cmd(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of entries"),
) -> None:
    """Display Wiki compile log."""
    from saw.engines.compile import WikiCompileEngine

    engine = WikiCompileEngine(_resolve_vault_root())
    entries = engine.get_log(limit)

    if not entries:
        console.print("[dim]No log entries found.[/dim]")
        return

    for entry in entries:
        ts = entry.timestamp.strftime("%Y-%m-%d %H:%M")
        console.print(f"[bold]{ts}[/bold] — [cyan]{entry.action.upper()}[/cyan]")
        if entry.summary:
            console.print(f"  {entry.summary}")
        console.print()


def wiki_page_cmd(
    name: str = typer.Argument(..., help="Page filename (e.g. concepts/event-sourcing.md)"),
) -> None:
    """Read a Wiki compile layer page."""
    from saw.engines.compile import WikiCompileEngine

    engine = WikiCompileEngine(_resolve_vault_root())
    page = engine.read_page(name)

    if not page:
        console.print(f"[red]Page not found:[/red] {name}")
        raise typer.Exit(1)

    console.print(Panel(page.content, title=page.title))
    console.print(f"\n[dim]Type: {page.metadata.type.value} | Confidence: {page.metadata.confidence.value}[/dim]")
    if page.metadata.sources:
        console.print("[dim]Sources:[/dim]")
        for src in page.metadata.sources:
            console.print(f"  - {src.title} ({src.page_id})")


# ─── Archive commands ──────────────────────────────────────────────────


def archive_cmd(
    query: str = typer.Argument(..., help="Query to archive"),
    answer: str = typer.Option("", "--answer", "-a", help="Answer content"),
    pages: Optional[str] = typer.Option(None, "--pages", "-p", help="Comma-separated referenced pages"),
) -> None:
    """Archive a query result as a Wiki page."""
    import asyncio
    from saw.engines.compile import WikiCompileEngine, QueryArchiver

    engine = WikiCompileEngine(_resolve_vault_root())
    archiver = QueryArchiver(engine.wiki_root)

    referenced = [p.strip() for p in pages.split(",")] if pages else []

    async def _run():
        return await archiver.archive(query, answer, referenced)

    page = asyncio.run(_run())
    console.print(f"[green]Archived:[/green] {page.filename}")


def archive_list_cmd() -> None:
    """List all archived pages."""
    from saw.engines.compile import WikiCompileEngine, QueryArchiver

    engine = WikiCompileEngine(_resolve_vault_root())
    archiver = QueryArchiver(engine.wiki_root)
    archives = archiver.list_archives()

    if not archives:
        console.print("[dim]No archives found.[/dim]")
        return

    for a in archives:
        console.print(f"  {a}")


# ─── Lint commands ─────────────────────────────────────────────────────


def wiki_lint_cmd(
    no_fix: bool = typer.Option(False, "--no-fix", help="Report only, don't auto-fix"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Check specific category"),
) -> None:
    """Wiki health check with tiered governance."""
    import asyncio
    from saw.engines.compile import WikiCompileEngine, WikiLinter

    engine = WikiCompileEngine(_resolve_vault_root())
    linter = WikiLinter(engine.wiki_root)

    async def _run():
        return await linter.lint(auto_fix=not no_fix)

    report = asyncio.run(_run())

    # Render report
    console.print(Panel(
        f"Health Score: [bold]{report.health_score}/100[/bold]\n"
        f"Auto-fixed: {len(report.auto_fixed)} | Warnings: {len(report.warnings)} | Errors: {len(report.errors)}\n"
        f"Duration: {report.duration_seconds:.1f}s",
        title="Wiki Lint Report",
    ))

    if report.auto_fixed:
        console.print("\n[green]Auto-fixed:[/green]")
        for f in report.auto_fixed:
            console.print(f"  ✓ [{f.category.value}] {f.page}: {f.fix_detail}")

    if report.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for f in report.warnings:
            console.print(f"  ⚠ [{f.category.value}] {f.page}: {f.description}")
            if f.suggestion:
                console.print(f"    → {f.suggestion}")

    if report.errors:
        console.print("\n[red]Errors:[/red]")
        for f in report.errors:
            console.print(f"  ✗ [{f.category.value}] {f.page}: {f.description}")
            if f.suggestion:
                console.print(f"    → {f.suggestion}")

    if report.exploration_suggestions:
        console.print("\n[blue]Suggestions:[/blue]")
        for s in report.exploration_suggestions:
            console.print(f"  💡 {s}")


# ─── Concept commands ──────────────────────────────────────────────────


def concept_list_cmd() -> None:
    """List all concepts in the knowledge graph."""
    from saw.engines.compile import WikiCompileEngine, ConceptGraphEngine

    engine = WikiCompileEngine(_resolve_vault_root())
    graph = ConceptGraphEngine(engine.wiki_root)
    concepts = graph.list_concepts()

    if not concepts:
        console.print("[dim]No concepts found. Run `saw compile` first.[/dim]")
        return

    table = Table(title="Concepts")
    table.add_column("Name", style="cyan")
    table.add_column("Stability")
    table.add_column("Relations", justify="right")
    table.add_column("Wiki Page")

    for c in concepts:
        node = graph.get_concept(c.name)
        rel_count = node.total_relations if node else 0
        stability_style = "green" if c.stability.value == "stable" else "yellow"
        table.add_row(
            c.name,
            f"[{stability_style}]{c.stability.value}[/{stability_style}]",
            str(rel_count),
            c.wiki_page or "-",
        )

    console.print(table)


def concept_view_cmd(
    name: str = typer.Argument(..., help="Concept name"),
) -> None:
    """View concept details with relations."""
    from saw.engines.compile import WikiCompileEngine, ConceptGraphEngine

    engine = WikiCompileEngine(_resolve_vault_root())
    graph = ConceptGraphEngine(engine.wiki_root)
    node = graph.get_concept(name)

    if not node:
        console.print(f"[red]Concept not found:[/red] {name}")
        raise typer.Exit(1)

    console.print(Panel(
        f"[bold]{node.name}[/bold]\n"
        f"Stability: {node.stability.value}\n"
        f"Definition: {node.definition or '(none)'}\n"
        f"Wiki page: {node.wiki_page or '(none)'}",
        title="Concept Detail",
    ))

    if node.relations_out:
        console.print("\n[bold]Outgoing relations:[/bold]")
        for r in node.relations_out:
            console.print(f"  → [{r.relation_type.value}] {r.target}")

    if node.relations_in:
        console.print("\n[bold]Incoming relations:[/bold]")
        for r in node.relations_in:
            console.print(f"  ← [{r.relation_type.value}] {r.source}")


def concept_relate_cmd(
    source: str = typer.Argument(..., help="Source concept"),
    target: str = typer.Argument(..., help="Target concept"),
    relation: str = typer.Argument(..., help="Relation type (e.g. depends_on)"),
    remove: bool = typer.Option(False, "--remove", help="Remove relation"),
) -> None:
    """Add or remove a typed relation between concepts."""
    from saw.engines.compile import WikiCompileEngine, ConceptGraphEngine
    from saw.domain.concept import ConceptRelation, ConceptRelationType

    engine = WikiCompileEngine(_resolve_vault_root())
    graph = ConceptGraphEngine(engine.wiki_root)

    try:
        rel_type = ConceptRelationType(relation)
    except ValueError:
        valid = ", ".join(t.value for t in ConceptRelationType)
        console.print(f"[red]Invalid relation type.[/red] Valid: {valid}")
        raise typer.Exit(1)

    if remove:
        ok = graph.remove_relation(source, target, rel_type)
        if ok:
            console.print(f"[green]Removed:[/green] {source} —[{relation}]→ {target}")
        else:
            console.print(f"[yellow]Relation not found.[/yellow]")
    else:
        rel = ConceptRelation(source=source, target=target, relation_type=rel_type)
        ok = graph.add_relation(rel)
        if ok:
            console.print(f"[green]Added:[/green] {source} —[{relation}]→ {target}")
        else:
            console.print(f"[yellow]Relation already exists.[/yellow]")


def graph_overview_cmd() -> None:
    """Display knowledge graph global topology."""
    from saw.engines.compile import WikiCompileEngine, ConceptGraphEngine

    engine = WikiCompileEngine(_resolve_vault_root())
    graph = ConceptGraphEngine(engine.wiki_root)
    overview = graph.get_overview()

    console.print(Panel(
        f"Concepts: {overview.total_concepts} | Relations: {overview.total_relations}\n"
        f"Stability: {overview.stability_distribution}\n"
        f"Relation types: {overview.relation_type_distribution}",
        title="Graph Overview",
    ))

    if overview.densest_concepts:
        console.print("\n[bold]Most connected:[/bold]")
        for name in overview.densest_concepts[:5]:
            console.print(f"  • {name}")


# ─── Feedback commands ─────────────────────────────────────────────────


def issue_list_cmd(
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
) -> None:
    """List knowledge issues."""
    from saw.engines.compile import WikiCompileEngine, FeedbackEngine
    from saw.domain.feedback import IssueStatus

    engine = WikiCompileEngine(_resolve_vault_root())
    storage = engine.wiki_root.parent / ".saw" / "feedback.json"
    fb = FeedbackEngine(storage)

    filter_status = IssueStatus(status) if status else None
    issues = fb.list_issues(status=filter_status)

    if not issues:
        console.print("[dim]No issues found.[/dim]")
        return

    table = Table(title="Knowledge Issues")
    table.add_column("ID", style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Reporter")

    for i in issues:
        table.add_row(i.id, i.type.value, i.title, i.status.value, i.reporter)

    console.print(table)


def issue_create_cmd(
    type: str = typer.Option(..., "--type", "-t", help="Issue type: challenge|request|suggestion"),
    title: str = typer.Option(..., "--title", help="Issue title"),
    pages: Optional[str] = typer.Option(None, "--pages", "-p", help="Affected pages (comma-separated)"),
) -> None:
    """Create a knowledge issue."""
    from saw.engines.compile import WikiCompileEngine, FeedbackEngine
    from saw.domain.feedback import IssueType

    engine = WikiCompileEngine(_resolve_vault_root())
    storage = engine.wiki_root.parent / ".saw" / "feedback.json"
    fb = FeedbackEngine(storage)

    try:
        issue_type = IssueType(type)
    except ValueError:
        console.print(f"[red]Invalid type.[/red] Valid: challenge, request, suggestion")
        raise typer.Exit(1)

    affected = [p.strip() for p in pages.split(",")] if pages else []
    issue = fb.create_issue(issue_type, title, "", affected, "cli-user")
    console.print(f"[green]Created issue:[/green] {issue.id} — {issue.title}")


def cr_list_cmd(
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
) -> None:
    """List change requests."""
    from saw.engines.compile import WikiCompileEngine, FeedbackEngine
    from saw.domain.feedback import CRStatus

    engine = WikiCompileEngine(_resolve_vault_root())
    storage = engine.wiki_root.parent / ".saw" / "feedback.json"
    fb = FeedbackEngine(storage)

    filter_status = CRStatus(status) if status else None
    crs = fb.list_crs(status=filter_status)

    if not crs:
        console.print("[dim]No change requests found.[/dim]")
        return

    table = Table(title="Change Requests")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Target", style="cyan")
    table.add_column("Status")
    table.add_column("Creator")

    for cr in crs:
        table.add_row(cr.id, cr.title, cr.target_page, cr.status.value, cr.creator)

    console.print(table)


def cr_create_cmd(
    page: str = typer.Option(..., "--page", help="Target wiki page"),
    title: str = typer.Option(..., "--title", help="CR title"),
    content_file: Optional[str] = typer.Option(None, "--content-file", help="File with proposed content"),
) -> None:
    """Create a change request."""
    from saw.engines.compile import WikiCompileEngine, FeedbackEngine

    engine = WikiCompileEngine(_resolve_vault_root())
    storage = engine.wiki_root.parent / ".saw" / "feedback.json"
    fb = FeedbackEngine(storage)

    content = ""
    if content_file:
        content = Path(content_file).read_text(encoding="utf-8")

    cr = fb.create_cr(title=title, target_page=page, proposed_content=content, creator="cli-user")
    console.print(f"[green]Created CR:[/green] {cr.id} — {cr.title} → {cr.target_page}")


def cr_review_cmd(
    cr_id: str = typer.Argument(..., help="CR ID"),
    approve: bool = typer.Option(False, "--approve", help="Approve the CR"),
    reject: bool = typer.Option(False, "--reject", help="Reject the CR"),
    comment: str = typer.Option("", "--comment", "-m", help="Review comment"),
) -> None:
    """Review a change request."""
    from saw.engines.compile import WikiCompileEngine, FeedbackEngine

    engine = WikiCompileEngine(_resolve_vault_root())
    storage = engine.wiki_root.parent / ".saw" / "feedback.json"
    fb = FeedbackEngine(storage)

    if not approve and not reject:
        console.print("[red]Specify --approve or --reject[/red]")
        raise typer.Exit(1)

    cr = fb.review_cr(cr_id, reviewer="cli-reviewer", approved=approve, comment=comment)
    if not cr:
        console.print(f"[red]CR not found:[/red] {cr_id}")
        raise typer.Exit(1)

    status_color = "green" if cr.status.value == "approved" else "red"
    console.print(f"[{status_color}]CR {cr_id}: {cr.status.value}[/{status_color}]")


# ─── Code Wiki commands ────────────────────────────────────────────────


def code_wiki_generate_cmd(
    repo_path: str = typer.Argument(..., help="Path to code repository"),
    incremental: bool = typer.Option(False, "--incremental", help="Only update changed modules"),
    module: Optional[str] = typer.Option(None, "--module", "-m", help="Generate for specific module"),
) -> None:
    """Generate Code Wiki for a repository."""
    import asyncio
    from saw.engines.compile import WikiCompileEngine, CodeWikiEngine
    from saw.domain.code_wiki import CodeWikiConfig

    engine = WikiCompileEngine(_resolve_vault_root())
    code_wiki = CodeWikiEngine(engine.wiki_root)

    config = CodeWikiConfig(
        repo_path=Path(repo_path),
        skip_if_exists=incremental,
    )

    async def _run():
        return await code_wiki.generate(config)

    result = asyncio.run(_run())

    console.print(Panel(
        f"[green]Generated:[/green] {len(result.pages_generated)} pages\n"
        f"[yellow]Updated:[/yellow] {len(result.pages_updated)} pages\n"
        f"[dim]Skipped:[/dim] {len(result.pages_skipped)} pages\n"
        f"Source files: {result.total_source_files}\n"
        f"Duration: {result.duration_seconds:.1f}s",
        title="Code Wiki Generation",
    ))


def code_wiki_status_cmd(
    repo_path: str = typer.Argument(..., help="Path to code repository"),
) -> None:
    """Check Code Wiki status."""
    import asyncio
    from saw.engines.compile import WikiCompileEngine, CodeWikiEngine
    from saw.domain.code_wiki import CodeWikiConfig

    engine = WikiCompileEngine(_resolve_vault_root())
    code_wiki = CodeWikiEngine(engine.wiki_root)
    config = CodeWikiConfig(repo_path=Path(repo_path))

    async def _run():
        return await code_wiki.status(config)

    status = asyncio.run(_run())

    if not status.exists:
        console.print("[dim]Code Wiki not generated yet.[/dim]")
        return

    stale_indicator = " [red](STALE)[/red]" if status.is_stale else " [green](fresh)[/green]"
    console.print(Panel(
        f"Pages: {status.pages_count}{stale_indicator}\n"
        f"Last commit: {status.last_commit}\n"
        f"Current commit: {status.current_commit}",
        title="Code Wiki Status",
    ))


# ─── Registration helper ──────────────────────────────────────────────


def register_compile_commands(app: typer.Typer) -> None:
    """Register all compile-layer commands with the CLI app."""
    # Compile
    app.command(name="compile")(compile_cmd)

    # Wiki subcommands
    wiki_app = typer.Typer(help="Wiki compile layer operations")
    wiki_app.command(name="index")(wiki_index_cmd)
    wiki_app.command(name="log")(wiki_log_cmd)
    wiki_app.command(name="page")(wiki_page_cmd)
    wiki_app.command(name="lint")(wiki_lint_cmd)
    app.add_typer(wiki_app, name="wiki")

    # Archive
    archive_app = typer.Typer(help="Query archive operations")
    archive_app.command(name="create")(archive_cmd)
    archive_app.command(name="list")(archive_list_cmd)
    app.add_typer(archive_app, name="archive")

    # Concept
    concept_app = typer.Typer(help="Concept graph operations")
    concept_app.command(name="list")(concept_list_cmd)
    concept_app.command(name="view")(concept_view_cmd)
    concept_app.command(name="relate")(concept_relate_cmd)
    app.add_typer(concept_app, name="concept")

    # Graph overview
    app.command(name="graph-overview")(graph_overview_cmd)

    # Feedback: Issues
    issue_app = typer.Typer(help="Knowledge issue operations")
    issue_app.command(name="list")(issue_list_cmd)
    issue_app.command(name="create")(issue_create_cmd)
    app.add_typer(issue_app, name="issue")

    # Feedback: CRs
    cr_app = typer.Typer(help="Change request operations")
    cr_app.command(name="list")(cr_list_cmd)
    cr_app.command(name="create")(cr_create_cmd)
    cr_app.command(name="review")(cr_review_cmd)
    app.add_typer(cr_app, name="cr")

    # Code Wiki
    code_wiki_app = typer.Typer(help="Code Wiki operations")
    code_wiki_app.command(name="generate")(code_wiki_generate_cmd)
    code_wiki_app.command(name="status")(code_wiki_status_cmd)
    app.add_typer(code_wiki_app, name="code-wiki")

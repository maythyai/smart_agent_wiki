"""CLI `saw links` command — T-F-L-1 / F-L-2 (AC-LINK-1, AC-LINK-2).

suggest: recommend related-but-not-yet-linked wiki pages.
audit:   find orphan pages (no backlinks) and broken [[wiki-links]].

Both reuse the existing query engines (compute_related_pages,
parse_wiki_links, extract_unique_targets) — no new engine logic.
"""
from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(no_args_is_help=True, help="Wiki link suggestions + audit (F-L-1/2).")


def _wiki(path: str):
    """Open the wiki repo for a wiki directory (mirrors query_cmd)."""
    from saw.drivers.cli.main import console

    wiki_path = Path(path).resolve()
    config_path = wiki_path / ".saw" / "config.yaml"
    if not config_path.is_file():
        console.print("[red]Error:[/red] Not a Smart Agent Wiki. Run `saw init` first.")
        raise typer.Exit(code=1)
    from saw.adapters.storage.wiki_repository import WikiRepository

    return WikiRepository(wiki_path / "wiki"), console


def _resolve_page(wiki, page: str) -> str | None:
    """Resolve a user-supplied page id to a wiki path (forgiving)."""
    from saw.engines.query.wiki_links import slugify

    # 1. direct path
    if wiki.read(page) is not None:
        return page
    # 2. bare stem → find a page whose stem slug-matches
    target = slugify(Path(page).stem if page.endswith(".md") else page)
    for p in wiki.list_pages():
        if slugify(Path(p).stem) == target:
            return p
    return None


@app.command(name="suggest")
def suggest(
    page: str = typer.Argument(..., help="Page slug/path to suggest links for"),
    path: str = typer.Option(".", "--path", "-p", help="Wiki directory path"),
    top_k: int = typer.Option(8, "--top", "-n", help="Max suggestions"),
) -> None:
    """Suggest related pages not yet [[linked]] (AC-LINK-1)."""
    from rich.table import Table

    from saw.engines.query.related_pages import compute_related_pages
    from saw.engines.query.wiki_links import extract_unique_targets, slugify

    wiki, console = _wiki(path)
    resolved = _resolve_page(wiki, page)
    if resolved is None:
        console.print(f"[red]Error:[/red] page not found: {page}")
        raise typer.Exit(code=1)

    src = wiki.read(resolved)
    outlinked = extract_unique_targets(src.content) | {slugify(Path(resolved).stem)}

    related = compute_related_pages(resolved, wiki, top_k=top_k * 2)
    suggestions = [
        r for r in related
        if slugify(Path(r["slug"]).stem) not in outlinked
    ][:top_k]

    if not suggestions:
        console.print("[yellow]No link suggestions — all related pages already linked.[/yellow]")
        raise typer.Exit(code=0)

    table = Table(title=f"Link suggestions for {resolved}")
    table.add_column("page", style="cyan")
    table.add_column("score", justify="right")
    table.add_column("reason")
    for r in suggestions:
        table.add_row(r["slug"], f"{r['score']:.2f}", "; ".join(r.get("reasons", [])))
    console.print(table)
    raise typer.Exit(code=0)


@app.command(name="audit")
def audit(
    path: str = typer.Option(".", "--path", "-p", help="Wiki directory path"),
) -> None:
    """Audit for orphan pages + broken [[wiki-links]] (AC-LINK-2)."""
    from rich.table import Table

    from saw.engines.query.wiki_links import parse_wiki_links, slugify

    wiki, console = _wiki(path)
    pages = wiki.list_pages()
    identity = {slugify(Path(p).stem): p for p in pages}

    # Inbound link counts (by page identity).
    inbound: dict[str, int] = {}
    broken: list[tuple[str, str]] = []
    for src_path in pages:
        page = wiki.read(src_path)
        if page is None:
            continue
        for link in parse_wiki_links(page.content):
            inbound[link.target] = inbound.get(link.target, 0) + 1
            if link.target not in identity:
                broken.append((src_path, link.target))

    orphans = [p for p in pages if inbound.get(slugify(Path(p).stem), 0) == 0]

    # Orphans table
    if orphans:
        t = Table(title=f"{len(orphans)} orphan page(s) (no backlinks)")
        t.add_column("page", style="cyan")
        for p in orphans:
            t.add_row(p)
        console.print(t)
    else:
        console.print("[green]No orphan pages — every page has a backlink.[/green]")

    # Broken links table
    if broken:
        t = Table(title=f"{len(broken)} broken link(s)")
        t.add_column("from", style="cyan")
        t.add_column("missing target")
        for src, tgt in broken:
            t.add_row(src, tgt)
        console.print(t)
    else:
        console.print("[green]No broken links — all [[targets]] resolve.[/green]")
    raise typer.Exit(code=0)

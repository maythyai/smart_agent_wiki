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

    # T-F-N-3: pass conn + workspace_id when tier=FULL so the embedding
    # signal (weight 2.5) participates in related-page scoring.
    conn_to_pass = None
    workspace_id = "default"
    try:
        from saw.config.settings import detect_tier
        from saw.domain.value_objects import CapabilityTier
        import sqlite3
        from pathlib import Path as _Path

        wiki_path = _Path(path).resolve()
        db_path = wiki_path / ".saw" / "db" / "claims.db"
        tier = detect_tier()
        if tier >= CapabilityTier.FULL and db_path.is_file():
            conn_to_pass = sqlite3.connect(str(db_path))
    except Exception:
        pass  # degrade to 3-signal if anything goes wrong

    try:
        related = compute_related_pages(
            resolved, wiki, top_k=top_k * 2,
            conn=conn_to_pass, workspace_id=workspace_id,
        )
    finally:
        if conn_to_pass is not None:
            conn_to_pass.close()
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


@app.command(name="apply")
def apply(
    page: str = typer.Argument(..., help="Page slug/path to apply link suggestions to"),
    path: str = typer.Option(".", "--path", "-p", help="Wiki directory path"),
    confirm: bool = typer.Option(False, "--confirm", help="Confirm write-back (default: dry-run)"),
    top_k: int = typer.Option(0, "--top", "-n", help="Max suggestions to apply (0=all)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Explicit dry-run preview"),
    suggestion: str = typer.Option("", "--suggestion", "-s", help="Apply single suggestion slug"),
) -> None:
    """Apply suggested [[links]] to a wiki page (F-T-2, AC-B-1..4).

    Default: dry-run (preview only). Use ``--confirm`` to write back.
    Writes a ``## Related`` section + syncs the frontmatter ``related`` field
    via :meth:`WikiRepository.write`.
    """
    from rich.table import Table

    from saw.engines.query.related_pages import compute_related_pages
    from saw.engines.query.wiki_links import extract_unique_targets, slugify

    wiki, console = _wiki(path)
    resolved = _resolve_page(wiki, page)
    if resolved is None:
        console.print(f"[red]Error:[/red] page not found: {page}")
        raise typer.Exit(code=1)

    src = wiki.read(resolved)
    if src is None:
        console.print(f"[red]Error:[/red] could not read page: {page}")
        raise typer.Exit(code=1)

    outlinked = extract_unique_targets(src.content) | {slugify(Path(resolved).stem)}

    # Reuse the same conn+tier detection as ``suggest`` so the embedding
    # signal (weight 2.5) participates when tier=FULL.
    conn_to_pass = None
    workspace_id = "default"
    try:
        from saw.config.settings import detect_tier
        from saw.domain.value_objects import CapabilityTier
        import sqlite3
        from pathlib import Path as _Path

        wiki_path = _Path(path).resolve()
        db_path = wiki_path / ".saw" / "db" / "claims.db"
        tier = detect_tier()
        if tier >= CapabilityTier.FULL and db_path.is_file():
            conn_to_pass = sqlite3.connect(str(db_path))
    except Exception:
        pass

    try:
        related = compute_related_pages(
            resolved, wiki, top_k=top_k * 2 if top_k > 0 else 100,
            conn=conn_to_pass, workspace_id=workspace_id,
        )
    finally:
        if conn_to_pass is not None:
            conn_to_pass.close()

    # Filter out already-linked pages (dedup)
    suggestions = [
        r for r in related
        if slugify(Path(r["slug"]).stem) not in outlinked
    ]
    if top_k > 0:
        suggestions = suggestions[:top_k]
    if suggestion:
        suggestions = [
            r for r in suggestions
            if slugify(Path(r["slug"]).stem) == suggestion
        ]

    if not suggestions:
        console.print(
            "[yellow]No link suggestions to apply — "
            "all related pages already linked.[/yellow]"
        )
        raise typer.Exit(code=0)

    # 1. Dry-run or confirm
    is_dry_run = not confirm or dry_run
    if is_dry_run:
        table = Table(
            title=f"Dry run — {len(suggestions)} link(s) "
            f"would be applied to {resolved}"
        )
        table.add_column("page", style="cyan")
        table.add_column("score", justify="right")
        for r in suggestions:
            table.add_row(r["slug"], f"{r['score']:.2f}")
        console.print(table)
        console.print(
            f"\n[yellow]Dry run — {len(suggestions)} links would be applied. "
            f"Run with --confirm to apply.[/yellow]"
        )
        raise typer.Exit(code=0)

    # 2. Confirm: write back via WikiRepository.write()
    applied: list[str] = []
    skipped: list[str] = []
    failed: list[tuple[str, str]] = []

    for r in suggestions:
        link_slug = slugify(Path(r["slug"]).stem)
        # Dedup check: already linked?
        if f"[[{link_slug}]]" in src.content or link_slug in src.related:
            skipped.append(link_slug)
            console.print(
                f"[yellow]Link [[{link_slug}]] already exists in "
                f"{resolved}, skipped[/yellow]"
            )
            continue

        # Update content: append ## Related section
        if "## Related" in src.content:
            # Append to existing ## Related section
            src.content += f"- [[{link_slug}]]\n"
        else:
            src.content += f"\n## Related\n\n- [[{link_slug}]]\n"

        # Update frontmatter related field
        if link_slug not in src.related:
            src.related.append(link_slug)

        applied.append(link_slug)

    # Write back via WikiRepository.write()
    if applied:
        try:
            wiki.write(src)
        except Exception as e:
            failed.append((resolved, str(e)))
            console.print(f"[red]Failed to write {resolved}: {e}[/red]")

    # 3. Summary
    console.print(f"[green]{len(applied)} links applied to {resolved}[/green]")
    if skipped:
        console.print(
            f"[yellow]{len(skipped)} links skipped (already exist)[/yellow]"
        )
    if failed:
        console.print(f"[red]{len(failed)} pages failed:[/red]")
        for p, e in failed:
            console.print(f"  {p}: {e}")

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

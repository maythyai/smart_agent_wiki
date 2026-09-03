"""CLI `saw learn` command — T-F-I-2 (AC-LR-1, AC-LR-2).

Exposes the Learn engine's online paths as CLI: ``saw learn distill``
(Distiller.extract_sop via LLMRouter) and ``saw learn gaps``
(TrendSenser.detect_gaps). The engines already exist; this is the CLI
surface. distill requires an LLM (online path) — errors loudly when
unavailable rather than silently degrading (PRD §4 risk).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import typer

app = typer.Typer(no_args_is_help=True, help="Learn engine: SOP distillation + gap detection (F-I-2).")


def _open_db(path: str):
    """Open claims.db + run migrations. Returns (conn, wiki_path) or Exit."""
    from saw.drivers.cli.main import console

    wiki_path = Path(path).resolve()
    config_path = wiki_path / ".saw" / "config.yaml"
    db_path = wiki_path / ".saw" / "db" / "claims.db"
    if not config_path.is_file():
        console.print("[red]Error:[/red] Not a Smart Agent Wiki. Run `saw init` first.")
        raise typer.Exit(code=1)
    if not db_path.is_file():
        console.print(f"[red]Error:[/red] Claims DB not found at {db_path}")
        raise typer.Exit(code=1)
    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(str(db_path))
    apply_migrations(conn)
    return conn, wiki_path


@app.command(name="distill")
def distill(
    approved: str = typer.Option(
        ".saw/approved.yaml", "--approved", "-a", help="Path to approved patterns YAML"
    ),
    path: str = typer.Option(".", "--path", "-p", help="Wiki directory path"),
) -> None:
    """Extract SOPs from approved patterns via LLM (AC-LR-1, online)."""
    from rich.table import Table

    from saw.drivers.cli.main import console

    from saw.config.settings import load_config, detect_tier
    from saw.domain.value_objects import CapabilityTier

    wiki_path = Path(path).resolve()
    config_path = wiki_path / ".saw" / "config.yaml"
    settings = load_config(config_path)
    tier = detect_tier(settings.llm)
    if tier < CapabilityTier.LIGHTWEIGHT or not settings.llm:
        console.print(
            "[red]Error:[/red] LLM unavailable. `saw learn distill` requires an "
            "online LLM (configure .saw/config.yaml llm)."
        )
        raise typer.Exit(code=1)
    from saw.adapters.llm.router import LLMRouter

    try:
        llm = LLMRouter(settings.llm)
    except Exception as e:
        console.print(f"[red]Error initialising LLM router:[/red] {e}")
        raise typer.Exit(code=1)

    approved_file = Path(approved)
    if not approved_file.is_file():
        console.print(f"[red]Error:[/red] approved file not found: {approved_file}")
        raise typer.Exit(code=1)

    from saw.engines.learn.distiller import Distiller

    distiller = Distiller(llm_router=llm, sops_dir=wiki_path / ".saw" / "sops")
    sops = distiller.run_distillation(approved_file)
    if not sops:
        console.print("[yellow]No SOPs extracted (need ≥2 patterns per action).[/yellow]")
        raise typer.Exit(code=0)
    table = Table(title=f"Distilled {len(sops)} SOP(s)")
    table.add_column("name", style="cyan")
    table.add_column("trigger")
    table.add_column("steps")
    for sop in sops:
        table.add_row(sop.name, sop.trigger[:40], str(len(sop.steps)))
    console.print(table)
    console.print(f"[green]saved to[/green] {wiki_path / '.saw' / 'sops'}")
    raise typer.Exit(code=0)


@app.command(name="gaps")
def gaps(
    path: str = typer.Option(".", "--path", "-p", help="Wiki directory path"),
) -> None:
    """Detect knowledge gaps (AC-LR-2)."""
    from rich.table import Table

    from saw.drivers.cli.main import console

    conn, wiki_path = _open_db(path)
    try:
        from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
        from saw.adapters.storage.wiki_repository import WikiRepository
        from saw.engines.learn.trends import TrendSenser

        claims_repo = SQLiteClaimsRepository(conn)
        wiki_repo = WikiRepository(wiki_path / "wiki")
        senser = TrendSenser(claims_repo=claims_repo, wiki_repo=wiki_repo)
        detected = senser.detect_gaps()
    finally:
        conn.close()

    if not detected:
        console.print("[green]No knowledge gaps detected.[/green]")
        raise typer.Exit(code=0)
    table = Table(title=f"{len(detected)} knowledge gap(s)")
    table.add_column("topic", style="cyan")
    table.add_column("coverage")
    table.add_column("queries")
    for g in detected:
        table.add_row(g.topic, f"{g.coverage:.1f}", str(g.query_count))
    console.print(table)
    raise typer.Exit(code=0)

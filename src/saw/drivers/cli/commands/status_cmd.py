"""CLI `status` command - display wiki health overview.

Per D-19: Shows page count, claim count, storage size, recent ingestions, WIP state.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import typer
import yaml
from rich.table import Table

from saw.config.settings import detect_tier, load_config
from saw.domain.exceptions import ConfigError


def status(
    path: str = typer.Argument(".", help="Wiki \u76ee\u5f55\u8def\u5f84"),
) -> None:
    """Display wiki overview: page count, claim count, storage size, WIP state."""
    from saw.drivers.cli.main import console

    wiki_path = Path(path).resolve()
    saw_dir = wiki_path / ".saw"
    config_path = saw_dir / "config.yaml"

    if not config_path.is_file():
        console.print("[red]Error:[/red] Not a Smart Agent Wiki. Run `saw init` first.")
        raise typer.Exit(code=1)

    # Load configuration
    try:
        load_config(config_path)
    except ConfigError as e:
        console.print(f"[red]Config error:[/red] {e}")
        raise typer.Exit(code=1)

    # Build status table
    table = Table(title="Smart Agent Wiki Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    # Claim count
    db_path = saw_dir / "db" / "claims.db"
    claim_count = 0
    entity_count = 0
    pending_ops = 0
    processing_ops = 0

    if db_path.is_file():
        try:
            conn = sqlite3.connect(str(db_path))
            row = conn.execute(
                "SELECT count(*) FROM claim WHERE deleted_at IS NULL"
            ).fetchone()
            claim_count = row[0] if row else 0

            row = conn.execute("SELECT count(*) FROM entity").fetchone()
            entity_count = row[0] if row else 0

            row = conn.execute(
                "SELECT count(*) FROM write_outbox WHERE status = 'pending'"
            ).fetchone()
            pending_ops = row[0] if row else 0

            row = conn.execute(
                "SELECT count(*) FROM write_outbox WHERE status = 'processing'"
            ).fetchone()
            processing_ops = row[0] if row else 0

            conn.close()
        except sqlite3.Error:
            pass

    # Page count
    wiki_dir = wiki_path / "wiki"
    page_count = 0
    if wiki_dir.is_dir():
        page_count = sum(1 for _ in wiki_dir.rglob("*.md"))

    # Vault count
    vault_dir = wiki_path / "vault"
    vault_count = 0
    if vault_dir.is_dir():
        vault_count = sum(
            1 for d in vault_dir.iterdir() if d.is_dir()
        )

    # Storage size
    storage_size = _du_human(wiki_path / "vault") + _du_human(wiki_dir) + _du_human(saw_dir)

    # WIP state
    wip_path = saw_dir / "wip.yaml"
    active_tasks: list[str] = []
    if wip_path.is_file():
        try:
            with open(wip_path, encoding="utf-8") as f:
                wip = yaml.safe_load(f) or {}
            active_tasks = wip.get("active_tasks", [])
        except Exception:
            pass

    # Capability tier
    tier = detect_tier()

    table.add_row("Wiki Path", str(wiki_path))
    table.add_row("Claim Count", str(claim_count))
    table.add_row("Entity Count", str(entity_count))
    table.add_row("Wiki Pages", str(page_count))
    table.add_row("Vault Documents", str(vault_count))
    table.add_row("Storage Size", storage_size)
    table.add_row("Write Queue Pending", str(pending_ops))
    table.add_row("Write Queue Processing", str(processing_ops))
    table.add_row("Capability Tier", tier.name)
    table.add_row("Active Tasks", ", ".join(active_tasks) if active_tasks else "(none)")

    console.print(table)


def _du_human(path: Path) -> str:
    """Calculate directory size and return human-readable string."""
    if not path.exists():
        return "0 B"

    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            try:
                total += f.stat().st_size
            except OSError:
                pass

    if total < 1024:
        return f"{total} B"
    elif total < 1024 * 1024:
        return f"{total / 1024:.1f} KB"
    else:
        return f"{total / (1024 * 1024):.1f} MB"

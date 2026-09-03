"""CLI `saw health` command — T-F-P-3 (AC-OBS-3).

OPS health inspection: aggregates DB connectivity, receipt-chain integrity
(v1.2.0 ReceiptStore across sessions), and Redis (when configured) into one
report. CLI-side mirror of the web /health/ready probe — engines are not
constructed here, so the engine row reports DB/repo constructability.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import typer
from rich.table import Table


def health(
    path: str = typer.Argument(".", help="Wiki directory path"),
) -> None:
    """Aggregate health: DB, receipt chain, Redis (AC-OBS-3)."""
    from saw.drivers.cli.main import console

    wiki_path = Path(path).resolve()
    db_path = wiki_path / ".saw" / "db" / "claims.db"
    config_path = wiki_path / ".saw" / "config.yaml"

    if not config_path.is_file():
        console.print("[red]Error:[/red] Not a Smart Agent Wiki. Run `saw init` first.")
        raise typer.Exit(code=1)

    table = Table(title="Smart Agent Wiki Health")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Detail")

    failed = 0

    # 1. Database connectivity.
    db_ok = db_path.is_file()
    claims = 0
    if db_ok:
        try:
            conn = sqlite3.connect(str(db_path))
            claims = conn.execute(
                "SELECT COUNT(*) FROM claim WHERE deleted_at IS NULL"
            ).fetchone()[0]
            conn.close()
        except sqlite3.Error as e:
            db_ok = False
            failed += 1
            table.add_row("database", "[red]unhealthy[/red]", f"query failed: {e}")
    else:
        failed += 1
        table.add_row("database", "[red]unhealthy[/red]", "claims.db missing")
    if db_ok:
        table.add_row("database", "[green]healthy[/green]", f"{claims} claims")

    # 2. Receipt chain integrity (v1.2.0 ReceiptStore).
    receipt_detail = "no receipts table"
    receipt_ok = True
    if db_ok:
        try:
            from saw.write_queue.receipt_store import ReceiptStore

            conn = sqlite3.connect(str(db_path))
            sessions = [
                r[0] for r in conn.execute(
                    "SELECT DISTINCT session_id FROM receipts WHERE session_id IS NOT NULL"
                ).fetchall()
            ]
            store = ReceiptStore(conn)
            valid_n = 0
            invalid_sessions: list[str] = []
            for sid in sessions:
                res = store.verify_chain(sid)
                if res.valid:
                    valid_n += 1
                else:
                    invalid_sessions.append(f"{sid[:8]}..")
                    receipt_ok = False
            conn.close()
            receipt_detail = (
                f"{valid_n}/{len(sessions)} sessions valid"
                + (f"; invalid: {', '.join(invalid_sessions)}" if invalid_sessions else "")
            ) if sessions else "no receipts recorded"
        except sqlite3.OperationalError:
            receipt_detail = "receipts table absent (pre-v1.2.0 DB)"
        except Exception as e:  # noqa: BLE001
            receipt_ok = False
            receipt_detail = f"verify failed: {e}"
    if not receipt_ok:
        failed += 1
    status = "[green]healthy[/green]" if receipt_ok else "[red]unhealthy[/red]"
    table.add_row("receipt chain", status, receipt_detail)

    # 3. Redis (skipped when unconfigured).
    import os

    redis_url = os.environ.get("REDIS_URL", "")
    if not redis_url:
        table.add_row("redis", "[yellow]skipped[/yellow]", "not configured")
    else:
        try:
            import redis  # type: ignore[import-untyped]

            redis.from_url(redis_url).ping()
            table.add_row("redis", "[green]healthy[/green]", "ping ok")
        except Exception as e:  # noqa: BLE001
            failed += 1
            table.add_row("redis", "[red]unhealthy[/red]", str(e))

    console.print(table)
    console.print(
        f"\nhealth: {3 - failed}/3 checks healthy, {failed} failed"
    )
    raise typer.Exit(code=failed)

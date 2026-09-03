"""CLI `saw policy` command — T-F-Z-8 (AC-SEC-5 continued).

Exposes ``CedarPolicyEngine.reload()`` (already implemented, AC-SEC-5) as a
CLI trigger so operators don't have to call it programmatically. CLI is
local-first (no auth); the Web admin endpoint is deferred (SPEC-F-Z-8 thin).
"""
from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(no_args_is_help=True, help="Cedar policy management (F-Z-8).")


@app.command(name="reload")
def reload(
    path: str = typer.Option(
        ".", "--path", "-p", help="Wiki directory path"
    ),
) -> None:
    """Hot-reload the Cedar policy file (AC-SEC-5)."""
    from saw.drivers.cli.main import console

    wiki_path = Path(path).resolve()
    policy_path = wiki_path / ".saw" / "policies" / "saw.cedar"
    if not policy_path.is_file():
        console.print(
            f"[yellow]No Cedar policy at {policy_path}. "
            f"Nothing to reload (RBAC still enforced by the in-process default).[/yellow]"
        )
        raise typer.Exit(code=0)

    from saw.adapters.crypto.cedar_policy import CedarPolicyEngine

    engine = CedarPolicyEngine(policy_path)
    available = engine.reload()
    backend = "cedar-python" if available else "Cedar CLI (hot per-call)"
    console.print(
        f"[green]policy reloaded:[/green] {policy_path.name} "
        f"(backend: [cyan]{backend}[/cyan])"
    )
    raise typer.Exit(code=0)

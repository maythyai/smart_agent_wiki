"""CLI `smoke` command — T-F-A-1-1 end-to-end smoke skeleton.

Per PRD §3.1 / SPEC-F-A-1: a single command runs a registry of smoke nodes
(ingest→compile→query→govern→learn in later Wave 2), prints per-node
PASS/FAIL+duration, and exits non-zero on any failure. This skeleton defines
the runner + self-check nodes only; engine node bodies are added by F-A-2..4.

Fresh-DB initialization is a placeholder here (temp dir under .hub-run/);
real fresh `saw init` wiring lands with F-A-2 (ingest node).
"""
from __future__ import annotations

import time
import traceback
from dataclasses import dataclass
from typing import Callable

import typer


@dataclass
class SmokeNode:
    """A single smoke check: a name + a callable returning True on success."""
    name: str
    fn: Callable[[], bool]


def run_smoke(nodes: list[SmokeNode]) -> int:
    """Run each node, print PASS/FAIL + duration, return count of failures."""
    from saw.drivers.cli.main import console

    failed = 0
    for node in nodes:
        start = time.perf_counter()
        try:
            ok = node.fn()
            ok = bool(ok)
            err = "" if ok else "node returned False"
        except Exception as exc:  # noqa: BLE001 — smoke must not abort on one node
            ok = False
            err = f"{type(exc).__name__}: {exc}"
        dur = time.perf_counter() - start
        if ok:
            console.print(f"[green]PASS[/green] {node.name} ({dur:.3f}s)")
        else:
            failed += 1
            console.print(f"[red]FAIL[/red] {node.name} ({dur:.3f}s) — {err}")
            # surface traceback for diagnosis
            try:
                tb = traceback.format_exc()
                if tb and "Traceback" in tb:
                    console.print(f"[dim]{tb}[/dim]")
            except Exception:  # noqa: BLE001
                pass
    console.print(f"\nsmoke: {len(nodes) - failed}/{len(nodes)} passed, {failed} failed")
    return failed


# --- skeleton self-check nodes (engine nodes added in F-A-2..4) ---

def _selfcheck_import() -> bool:
    """saw package importable."""
    import saw  # noqa: F401
    return True


def _selfcheck_console() -> bool:
    """Rich console available (CLI render path healthy)."""
    from saw.drivers.cli.main import console

    return console is not None


def _skeleton_nodes() -> list[SmokeNode]:
    """Default skeleton nodes; F-A-2..4 will register real engine nodes."""
    return [
        SmokeNode("skeleton.import", _selfcheck_import),
        SmokeNode("skeleton.console", _selfcheck_console),
    ]


def smoke(
    self_check: bool = typer.Option(
        False,
        "--self-check",
        help="Run skeleton self-check nodes only (no engine chain).",
    ),
    path: str = typer.Argument(
        ".",
        help="Wiki directory (fresh temp DB initialized under .hub-run/smoke/).",
    ),
) -> None:
    """Run end-to-end smoke baseline; exit non-zero on any node failure."""
    from pathlib import Path

    from saw.drivers.cli.main import console

    wiki_path = Path(path).resolve()
    run_dir = wiki_path / ".saw" / ".hub-run" / "smoke"
    run_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[cyan]smoke[/cyan] work dir: {run_dir}")

    nodes: list[SmokeNode] = []
    if self_check:
        nodes.extend(_skeleton_nodes())
    else:
        # Full chain wiring lands in F-A-2..4; until then fall back to skeleton
        # so `saw smoke` never silently no-ops.
        nodes.extend(_skeleton_nodes())
        console.print(
            "[yellow]note:[/yellow] engine-chain nodes (ingest/query/govern/learn) "
            "land in F-A-2..4; running skeleton self-check only."
        )

    failed = run_smoke(nodes)
    raise typer.Exit(code=failed)

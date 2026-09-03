"""CLI `saw workflow` command — T-F-I-1 / T-F-I-4 (AC-WF-1/2, AC-AG-1).

Declares a Typer sub-app with: run / validate / lint / resume / status.
The heavy engine (WorkflowExecutor + parser + M-16 state machine + HI-9
crash recovery) already exists; this command is the CLI surface that wires
it to a runtime (dispatcher + a2a + conn) reusing the same assembly as
``drivers/web/app.py:create_app_from_config``.
"""
from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(no_args_is_help=True, help="Multi-agent workflow orchestration (F-I-1/4).")


def _bootstrap_runtime(path: str):
    """Assemble the collaborative stack for CLI execution.

    Mirrors ``create_app_from_config``'s collaborate wiring (DEF-1) but
    minimal: dispatcher + a2a + workflow_executor + conn. Returns
    ``(executor, conn)`` or raises typer.Exit on misconfiguration.
    """
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

    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    apply_migrations(conn)  # ensure workflow_executions table exists (v4)

    try:
        from saw.engines.collaborate.agents import build_default_agents
        from saw.engines.collaborate.a2a_protocol import A2AAdapter
        from saw.engines.collaborate.dispatcher import AgentDispatcher
        from saw.engines.collaborate.workflow_executor import WorkflowExecutor

        agents = build_default_agents(llm_router=None)
        dispatcher = AgentDispatcher(llm_router=None, agents=agents)
        a2a = A2AAdapter(agents=agents, audit_signer=None, dispatcher=dispatcher)
        executor = WorkflowExecutor(
            dispatcher=dispatcher,
            a2a_adapter=a2a,
            governor=None,
            event_bus=None,
            conn=conn,
        )
        return executor, conn
    except Exception as e:  # pragma: no cover — defensive
        conn.close()
        console.print(f"[red]Error bootstrapping workflow runtime:[/red] {e}")
        raise typer.Exit(code=1)


def _parse_inputs(values: list[str]) -> dict:
    """Turn ``KEY=VAL`` args into a dict."""
    out: dict = {}
    for v in values:
        if "=" not in v:
            raise typer.BadParameter(f"input must be KEY=VAL, got: {v}")
        k, _, val = v.partition("=")
        out[k] = val
    return out


@app.command(name="run")
def run(
    definition: str = typer.Argument(..., help="Path to workflow YAML definition"),
    path: str = typer.Option(".", "--path", "-p", help="Wiki directory path"),
    input_kv: list[str] = typer.Option(
        [], "--input", "-i", help="Input context as KEY=VAL (repeatable)"
    ),
) -> None:
    """Execute a multi-agent workflow (AC-WF-1)."""
    from saw.drivers.cli.main import console

    def_path = Path(definition).resolve()
    if not def_path.is_file():
        console.print(f"[red]Error:[/red] workflow definition not found: {def_path}")
        raise typer.Exit(code=1)
    inputs = _parse_inputs(input_kv)
    executor, conn = _bootstrap_runtime(path)
    try:
        result = asyncio.run(executor.execute(def_path, inputs))
        console.print(
            f"workflow [cyan]{result.name}[/cyan] → [bold]{result.status}[/bold] "
            f"({result.steps_completed}/{result.steps_total} steps)"
        )
        console.print(f"id: [dim]{result.workflow_id}[/dim]")
        if result.errors:
            console.print("[red]errors:[/red]")
            for e in result.errors:
                console.print(f"  - {e}")
        raise typer.Exit(code=0 if result.status == "completed" else 1)
    finally:
        conn.close()


@app.command(name="validate")
def validate(
    definition: str = typer.Argument(..., help="Path to workflow YAML definition"),
) -> None:
    """Validate workflow schema (AC-WF-2). Exits 1 on invalid."""
    from saw.drivers.cli.main import console

    from saw.engines.collaborate.workflow_parser import WorkflowParseError, WorkflowParser

    def_path = Path(definition).resolve()
    parser = WorkflowParser()
    try:
        wf = parser.parse(def_path)
    except WorkflowParseError as e:
        console.print(f"[red]invalid:[/red] {e}")
        raise typer.Exit(code=1)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] file not found: {def_path}")
        raise typer.Exit(code=1)
    console.print(f"[green]valid:[/green] {wf.name} ({len(wf.steps)} steps, timeout={wf.timeout}s)")
    raise typer.Exit(code=0)


@app.command(name="lint")
def lint(
    definition: str = typer.Argument(..., help="Path to workflow YAML definition"),
    path: str = typer.Option(".", "--path", "-p", help="Wiki directory path"),
) -> None:
    """Lint agent-role consistency (AC-AG-1).

    Checks that every step's declared ``agent`` is in the registered agent
    roster (6 default agents) and that gate syntax is valid. Exits 1 on
    any unknown agent / invalid gate.
    """
    from saw.drivers.cli.main import console

    from saw.engines.collaborate.workflow_parser import WorkflowParseError, WorkflowParser

    def_path = Path(definition).resolve()
    if not def_path.is_file():
        console.print(f"[red]Error:[/red] file not found: {def_path}")
        raise typer.Exit(code=1)
    parser = WorkflowParser()
    try:
        wf = parser.parse(def_path)
    except WorkflowParseError as e:
        console.print(f"[red]parse error:[/red] {e}")
        raise typer.Exit(code=1)

    # Registered agents come from the dispatcher roster; for CLI lint we
    # build the default roster (no LLM) and read its keys — same source of
    # truth the runtime uses (orchestrator.get_available_agents).
    from saw.engines.collaborate.agents import build_default_agents

    available = set(build_default_agents(llm_router=None).keys())
    errors = parser.validate(wf, available)
    if errors:
        console.print(f"[red]{len(errors)} issue(s):[/red]")
        for e in errors:
            console.print(f"  - {e}")
        raise typer.Exit(code=1)
    console.print(
        f"[green]lint ok:[/green] {wf.name} — all agents in roster "
        f"({', '.join(sorted(available))})"
    )
    raise typer.Exit(code=0)


@app.command(name="resume")
def resume(
    workflow_id: str = typer.Argument(..., help="Persisted workflow_id to resume"),
    definition: str = typer.Option(..., "--def", "-d", help="Path to workflow YAML (re-parsed)"),
    path: str = typer.Option(".", "--path", "-p", help="Wiki directory path"),
    input_kv: list[str] = typer.Option(
        [], "--input", "-i", help="Input context as KEY=VAL (repeatable)"
    ),
) -> None:
    """Resume an interrupted/failed workflow (AC-WF-1 crash recovery)."""
    from saw.drivers.cli.main import console

    def_path = Path(definition).resolve()
    if not def_path.is_file():
        console.print(f"[red]Error:[/red] workflow definition not found: {def_path}")
        raise typer.Exit(code=1)
    inputs = _parse_inputs(input_kv)
    executor, conn = _bootstrap_runtime(path)
    try:
        result = asyncio.run(executor.resume(workflow_id, def_path, inputs))
        console.print(
            f"workflow [cyan]{result.name}[/cyan] resumed → [bold]{result.status}[/bold] "
            f"({result.steps_completed}/{result.steps_total} steps)"
        )
        if result.errors:
            console.print("[red]errors:[/red]")
            for e in result.errors:
                console.print(f"  - {e}")
        raise typer.Exit(code=0 if result.status == "completed" else 1)
    except RuntimeError as e:
        console.print(f"[red]resume failed:[/red] {e}")
        raise typer.Exit(code=1)
    finally:
        conn.close()


@app.command(name="status")
def status(
    workflow_id: str = typer.Argument(..., help="Persisted workflow_id"),
    path: str = typer.Option(".", "--path", "-p", help="Wiki directory path"),
) -> None:
    """Show persisted workflow execution state."""
    from rich.table import Table

    from saw.drivers.cli.main import console

    wiki_path = Path(path).resolve()
    db_path = wiki_path / ".saw" / "db" / "claims.db"
    if not db_path.is_file():
        console.print(f"[red]Error:[/red] Claims DB not found at {db_path}")
        raise typer.Exit(code=1)
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT workflow_id, definition_name, status, steps_completed, "
            "steps_total, errors_json, updated_at, finished_at "
            "FROM workflow_executions WHERE workflow_id = ?",
            (workflow_id,),
        ).fetchone()
    except sqlite3.OperationalError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    finally:
        conn.close()
    if row is None:
        console.print(f"[yellow]no workflow found with id {workflow_id}[/yellow]")
        raise typer.Exit(code=1)
    wid, name, st, sc, tot, errs_json, updated, finished = row
    table = Table(title=f"Workflow {wid[:8]}…")
    table.add_column("field", style="cyan")
    table.add_column("value")
    table.add_row("name", str(name))
    table.add_row("status", str(st))
    table.add_row("steps", f"{sc}/{tot}")
    table.add_row("updated", str(updated))
    table.add_row("finished", str(finished))
    errs = json.loads(errs_json or "[]")
    table.add_row("errors", f"{len(errs)}")
    console.print(table)
    for e in errs:
        console.print(f"  [red]-[/red] {e}")
    raise typer.Exit(code=0)

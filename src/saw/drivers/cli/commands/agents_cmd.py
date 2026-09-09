"""CLI ``saw agents`` command — T-F-M-2 (AC-AG-2) + F-T-1 custom + F-T-3 activity.

Lists the agent roster (name / model tier / tools / rule flag / custom flag)
from ``build_agent_roster`` — the same source the dispatcher registers.
Also provides ``saw agents activity <name>`` for per-agent activity aggregation.
No DB, no LLM; static roster + file-loaded custom roles + in-memory activity.
"""
from __future__ import annotations

import typer

app = typer.Typer(invoke_without_command=True, help="Agent roster + activity (F-T-1/3).")


@app.callback(invoke_without_command=True)
def agents(ctx: typer.Context) -> None:
    """List the agent roster (AC-AG-2, F-T-1 custom roles).

    Includes custom roles loaded from ``.saw/agents/*.yaml`` (marked
    ``custom``). No DB, no LLM; static roster + file-loaded custom roles.
    Only runs when no subcommand (``activity``/``export``/``import``) is
    given — otherwise yield to the subcommand.
    """
    if ctx.invoked_subcommand is not None:
        return  # a subcommand was requested; let it run, don't list the roster
    from rich.table import Table

    from saw.drivers.cli.main import console
    from saw.engines.collaborate.agents import build_agent_roster

    BUILTIN_NAMES = {"Librarian", "Writer", "Critic", "Linker", "Scholar", "Guardian"}
    roster = build_agent_roster(llm_router=None)
    table = Table(title=f"{len(roster)} agent role(s)")
    table.add_column("name", style="cyan")
    table.add_column("model_tier")
    table.add_column("tools_allowed")
    table.add_column("rule", justify="center")
    table.add_column("custom", justify="center")
    for name in sorted(roster):
        a = roster[name]
        tools = ", ".join(getattr(a, "_tools_allowed", []) or []) or "-"
        table.add_row(
            a.name,
            a.model_tier,
            tools,
            "✓" if a.model_tier == "rule" else "",
            "custom" if name not in BUILTIN_NAMES else "",
        )
    console.print(table)
    raise typer.Exit(code=0)


@app.command(name="activity")
def activity(
    name: str = typer.Argument(..., help="Agent name"),
    path: str = typer.Option(".", "--path", "-p", help="Wiki directory path"),
) -> None:
    """Show agent activity aggregation (F-T-3, AC-C-1..3).

    Reads the in-memory activity tracker (calls/failures/last_action/
    last_active_at). When no tracker is available (CLI-only mode, no
    ``saw web`` running), prints empty activity.
    """
    from saw.drivers.cli.main import console

    tracker = None
    try:
        from saw.engines.collaborate.activity_tracker import get_activity_tracker

        tracker = get_activity_tracker()
    except Exception:
        pass

    if tracker is None:
        console.print(
            "[yellow]No activity tracker available "
            "(run `saw web` to enable activity aggregation).[/yellow]"
        )
        console.print(f"Agent: {name}")
        console.print("  Calls: 0")
        console.print("  Failures: 0")
        console.print("  Last action: (none)")
        console.print("  Last active: (never)")
        raise typer.Exit(code=0)

    data = tracker.get_activity(name)
    console.print(f"Agent: {name}")
    console.print(f"  Calls: {data['calls']}")
    console.print(f"  Failures: {data['failures']}")
    console.print(f"  Last action: {data['last_action'] or '(none)'}")
    console.print(f"  Last active: {data['last_active_at'] or '(never)'}")
    raise typer.Exit(code=0)


def _custom_agents_dir(path: str):
    """Resolve the ``.saw/agents/`` dir for a wiki path."""
    from pathlib import Path

    return Path(path).resolve() / ".saw" / "agents"


def _find_custom_role_file(path: str, name: str):
    """Locate the YAML file defining a custom role by its ``name`` field."""
    import yaml

    agents_dir = _custom_agents_dir(path)
    if not agents_dir.is_dir():
        return None
    for yaml_file in sorted(agents_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("name") == name:
                return yaml_file
        except (yaml.YAMLError, OSError):
            continue
    return None


@app.command(name="export")
def export(
    name: str = typer.Argument(..., help="Custom agent role name to export"),
    out: str = typer.Option("", "--out", "-o", help="Output file path (default: stdout)"),
    path: str = typer.Option(".", "--path", "-p", help="Wiki directory path"),
) -> None:
    """Export a custom agent role to a portable YAML file (T3, Letta-inspired).

    Custom roles live in ``.saw/agents/*.yaml``; this copies the matching
    definition so it can be shared and re-imported on another wiki via
    ``saw agents import``.
    """
    from saw.drivers.cli.main import console

    yaml_file = _find_custom_role_file(path, name)
    if yaml_file is None:
        console.print(
            f"[red]Error:[/red] no custom role named '{name}' "
            f"in {_custom_agents_dir(path)}"
        )
        raise typer.Exit(code=1)

    content = yaml_file.read_text(encoding="utf-8")
    if not out:
        console.print(content)
        raise typer.Exit(code=0)

    from pathlib import Path

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    console.print(f"[green]Exported role '{name}' → {out_path}[/green]")
    raise typer.Exit(code=0)


@app.command(name="import")
def import_role(
    source: str = typer.Argument(..., help="Path to the agent YAML file to import"),
    path: str = typer.Option(".", "--path", "-p", help="Wiki directory path"),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing role file"),
) -> None:
    """Import a custom agent role YAML into ``.saw/agents/`` (T3).

    Validates the YAML has the required ``name`` / ``model_tier`` /
    ``system_prompt`` fields and warns if the name collides with a built-in.
    """
    import shutil

    import yaml
    from pathlib import Path

    from saw.drivers.cli.main import console

    src = Path(source).resolve()
    if not src.is_file():
        console.print(f"[red]Error:[/red] file not found: {source}")
        raise typer.Exit(code=1)

    try:
        data = yaml.safe_load(src.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        console.print(f"[red]Error:[/red] invalid YAML: {e}")
        raise typer.Exit(code=1)
    if not isinstance(data, dict):
        console.print("[red]Error:[/red] agent definition is not a mapping")
        raise typer.Exit(code=1)

    role_name = data.get("name", "")
    _BUILTIN = {"Librarian", "Writer", "Critic", "Linker", "Scholar", "Guardian"}
    if not role_name:
        console.print("[red]Error:[/red] agent YAML missing 'name' field")
        raise typer.Exit(code=1)
    if role_name in _BUILTIN:
        console.print(
            f"[red]Error:[/red] name '{role_name}' collides with a built-in role; "
            "choose a different name."
        )
        raise typer.Exit(code=1)
    if not data.get("model_tier"):
        console.print("[red]Error:[/red] agent YAML missing 'model_tier' field")
        raise typer.Exit(code=1)
    if not (data.get("system_prompt") or "").strip():
        console.print("[red]Error:[/red] agent YAML missing 'system_prompt' field")
        raise typer.Exit(code=1)

    agents_dir = _custom_agents_dir(path)
    agents_dir.mkdir(parents=True, exist_ok=True)
    dest = agents_dir / src.name
    if dest.is_file() and not force:
        console.print(
            f"[red]Error:[/red] {dest.name} already exists; use --force to overwrite"
        )
        raise typer.Exit(code=1)

    shutil.copyfile(src, dest)
    console.print(f"[green]Imported role '{role_name}' → {dest}[/green]")
    console.print(
        "[dim]It will be picked up by `saw agents` and the dispatcher on next run.[/dim]"
    )
    raise typer.Exit(code=0)

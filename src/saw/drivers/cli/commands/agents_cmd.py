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
def agents() -> None:
    """List the agent roster (AC-AG-2, F-T-1 custom roles).

    Includes custom roles loaded from ``.saw/agents/*.yaml`` (marked
    ``custom``). No DB, no LLM; static roster + file-loaded custom roles.
    """
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
        from saw.drivers.web.app import get_activity_tracker

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

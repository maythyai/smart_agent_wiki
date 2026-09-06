"""CLI `saw agents` command — T-F-M-2 (AC-AG-2).

Lists the 6-agent roster (name / model tier / tools / rule flag) from
``build_default_agents`` — the same source the dispatcher registers.
No DB, no LLM; static roster.
"""
from __future__ import annotations

import typer


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

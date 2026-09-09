"""CLI smoke tests — every `saw <cmd> --help` must exit 0.

A cheap, no-side-effect way to exercise the registration + help-rendering
entry points of every CLI command, lifting coverage on the low-coverage
command modules (review/lint/search/freshness/learn/feed/verify/compile/query…)
without requiring a live wiki/DB/LLM. Real functional behavior stays covered by
the per-command test modules; this guards against import/registration
regressions and typer-wiring breakage.
"""
from __future__ import annotations

import pytest
from typer.testing import CliRunner

# Every top-level command + sub-typer group registered on the `saw` app.
# (Mirrors src/saw/drivers/cli/main.py command registration order.)
_COMMANDS = [
    "init", "status", "ingest", "ingest-media", "preview",
    "query", "search", "rebuild-embeddings", "lint", "verify",
    "freshness", "review", "conflicts", "audit", "health",
    "mcp", "web", "feed", "tutorial", "config", "completion",
    "docs", "smoke", "workflow", "learn", "token", "policy",
    "links", "summarize",
]


@pytest.mark.parametrize("cmd", _COMMANDS)
def test_command_help_exits_zero(cmd: str) -> None:
    """`saw <cmd> --help` exits 0 and renders usage."""
    from saw.drivers.cli.main import app

    res = CliRunner().invoke(app, [cmd, "--help"])
    assert res.exit_code == 0, (
        f"`saw {cmd} --help` failed (exit {res.exit_code}):\n{res.output}"
    )
    # Typer/click always renders a Usage line for --help
    assert "Usage" in res.output or "usage" in res.output.lower()


def test_root_help_lists_commands() -> None:
    """`saw --help` lists the core commands."""
    from saw.drivers.cli.main import app

    res = CliRunner().invoke(app, ["--help"])
    assert res.exit_code == 0, res.output
    for core in ("ingest", "query", "lint", "verify", "freshness", "web"):
        assert core in res.output, f"{core!r} missing from `saw --help`"

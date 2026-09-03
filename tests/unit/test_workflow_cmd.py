"""CLI `saw workflow` command tests — T-F-I-1 (AC-WF-1/2) + T-F-I-4 (AC-AG-1).

validate / lint are exercised via CliRunner (no DB needed). resume is
exercised as a direct WorkflowExecutor unit test with an in-memory conn
(the CLI is thin wiring over ``executor.resume``).
"""
from __future__ import annotations

import asyncio
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from typer.testing import CliRunner


# ── AC-WF-2: schema validation (CLI) ────────────────────────────────

def test_validate_valid_yaml_exits_0():
    """AC-WF-2: a valid workflow validates cleanly."""
    from saw.drivers.cli.main import app

    yaml_content = """
name: seq
steps:
  - agent: Librarian
    action: search
"""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "wf.yaml"
        p.write_text(yaml_content)
        res = CliRunner().invoke(app, ["workflow", "validate", str(p)])
        assert res.exit_code == 0, res.output
        assert "valid" in res.output.lower()


def test_validate_missing_field_exits_1():
    """AC-WF-2: missing required field reports error + exit 1."""
    from saw.drivers.cli.main import app

    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "bad.yaml"
        p.write_text("steps:\n  - agent: Librarian\n    action: search\n")  # no name
        res = CliRunner().invoke(app, ["workflow", "validate", str(p)])
        assert res.exit_code == 1
        assert "name" in res.output


# ── AC-AG-1: agent-role consistency lint (CLI) ──────────────────────

def test_lint_valid_agents_exits_0():
    """AC-AG-1: all declared agents in roster → exit 0."""
    from saw.drivers.cli.main import app

    yaml_content = """
name: lint_ok
steps:
  - agent: Librarian
    action: search
  - agent: Scholar
    action: synthesize
"""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "wf.yaml"
        p.write_text(yaml_content)
        res = CliRunner().invoke(app, ["workflow", "lint", str(p), "--path", d])
        assert res.exit_code == 0, res.output
        assert "lint ok" in res.output.lower()


def test_lint_unknown_agent_exits_1():
    """AC-AG-1: an unknown agent role is rejected with exit 1."""
    from saw.drivers.cli.main import app

    yaml_content = """
name: lint_bad
steps:
  - agent: Librarian
    action: search
  - agent: GhostAgent
    action: haunt
"""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "wf.yaml"
        p.write_text(yaml_content)
        res = CliRunner().invoke(app, ["workflow", "lint", str(p), "--path", d])
        assert res.exit_code == 1
        assert "GhostAgent" in res.output


# ── AC-WF-1: crash recovery / resume (direct executor) ────────────

@pytest.mark.asyncio
async def test_resume_continues_from_persisted_step_index():
    """AC-WF-1: resume re-executes only the steps past the saved index."""
    from saw.db.migrations import apply_migrations
    from saw.domain.agent import AgentResult
    from saw.engines.collaborate.workflow_executor import WorkflowExecutor

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)

    dispatcher = MagicMock()
    dispatcher._agents = {"Librarian": MagicMock(), "Scholar": MagicMock()}
    dispatcher.dispatch = AsyncMock(
        return_value=AgentResult(success=True, payload={"x": 1}, confidence=3)
    )
    a2a = MagicMock()
    executor = WorkflowExecutor(dispatcher, a2a, None, conn=conn)

    yaml_content = """
name: resume_wf
steps:
  - agent: Librarian
    action: search
    output: a
  - agent: Scholar
    action: synthesize
    output: b
"""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "wf.yaml"
        p.write_text(yaml_content)

        # Simulate a crash after step 0: persist an interrupted row at index 1.
        executor._persist_workflow("wf-crash", "resume_wf", "interrupted", 1, 2, [])

        result = await executor.resume("wf-crash", p, {})
        assert result.status == "completed"
        assert result.workflow_id == "wf-crash"
        # Only step 1 (Scholar) should have dispatched — step 0 skipped.
        assert dispatcher.dispatch.call_count == 1
        called_agent = dispatcher.dispatch.call_args.args[0]
        assert called_agent == "Scholar"

        # Row should now be completed.
        row = conn.execute(
            "SELECT status, steps_completed FROM workflow_executions WHERE workflow_id=?",
            ("wf-crash",),
        ).fetchone()
        assert row[0] == "completed"
    conn.close()


@pytest.mark.asyncio
async def test_resume_refuses_completed_workflow():
    """AC-WF-1: a completed workflow cannot be resumed (state guard)."""
    from saw.db.migrations import apply_migrations
    from saw.domain.agent import AgentResult
    from saw.engines.collaborate.workflow_executor import WorkflowExecutor

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    dispatcher = MagicMock()
    dispatcher._agents = {"Librarian": MagicMock()}
    dispatcher.dispatch = AsyncMock(
        return_value=AgentResult(success=True, payload={}, confidence=3)
    )
    executor = WorkflowExecutor(dispatcher, MagicMock(), None, conn=conn)

    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "wf.yaml"
        p.write_text("name: r\nsteps:\n  - agent: Librarian\n    action: search\n")
        executor._persist_workflow("wf-done", "r", "completed", 1, 1, [])
        with pytest.raises(RuntimeError, match="illegal transition"):
            await executor.resume("wf-done", p, {})
    conn.close()

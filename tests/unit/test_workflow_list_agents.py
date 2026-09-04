"""Workflow list + agents CLI tests — T-F-M-1 / F-M-2 (AC-WF-3, AC-AG-2)."""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from typer.testing import CliRunner


def _wiki_with_db(tmp_path: Path) -> Path:
    (tmp_path / ".saw").mkdir(parents=True)
    (tmp_path / ".saw" / "config.yaml").write_text("llm: null\n")
    db = tmp_path / ".saw" / "db" / "claims.db"
    db.parent.mkdir(parents=True)
    conn = sqlite3.connect(str(db))
    from saw.db.migrations import apply_migrations
    apply_migrations(conn)
    conn.executemany(
        "INSERT INTO workflow_executions (workflow_id, definition_name, status, "
        "steps_completed, steps_total, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("wf-old", "seq", "completed", 2, 2, "2026-09-01T10:00:00"),
            ("wf-new", "seq", "interrupted", 1, 3, "2026-09-04T10:00:00"),
        ],
    )
    conn.commit()
    conn.close()
    return tmp_path


def test_workflow_list_shows_recent(tmp_path):
    """AC-WF-3: list shows recent durable runs, newest first."""
    from saw.drivers.cli.main import app

    _wiki_with_db(tmp_path)
    res = CliRunner().invoke(app, ["workflow", "list", "--path", str(tmp_path)])
    assert res.exit_code == 0, res.output
    # newest (wf-new) appears before oldest (wf-old)
    out = res.output
    assert "wf-new"[:6] in out or "wf-new" in out
    assert out.index("wf-new") < out.index("wf-old")
    assert "interrupted" in out


def test_workflow_list_empty(tmp_path):
    """AC-WF-3: empty DB reports cleanly."""
    from saw.drivers.cli.main import app

    (tmp_path / ".saw").mkdir(parents=True)
    (tmp_path / ".saw" / "config.yaml").write_text("llm: null\n")
    (tmp_path / ".saw" / "db").mkdir(parents=True)
    sqlite3.connect(str(tmp_path / ".saw" / "db" / "claims.db")).close()
    res = CliRunner().invoke(app, ["workflow", "list", "--path", str(tmp_path)])
    assert res.exit_code == 0
    assert "No workflow runs" in res.output


def test_agents_lists_six_roles():
    """AC-AG-2: saw agents lists the 6 roles, Guardian flagged rule."""
    from saw.drivers.cli.main import app

    res = CliRunner().invoke(app, ["agents"])
    assert res.exit_code == 0, res.output
    out = res.output
    for role in ["Librarian", "Writer", "Critic", "Linker", "Scholar", "Guardian"]:
        assert role in out
    # Guardian is the rule agent.
    assert "rule" in out

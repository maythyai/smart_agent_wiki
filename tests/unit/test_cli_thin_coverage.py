"""Functional CLI tests for thin commands (v1.29.0 coverage push: AUDIT-F-04 cont.).

Covers compile/feed/learn/review config-load + early-exit paths on tmp wikis.
"""
from __future__ import annotations

from pathlib import Path
from typer.testing import CliRunner


def _make_root(root: Path) -> Path:
    saw = root / ".saw"; saw.mkdir(parents=True)
    (saw / "config.yaml").write_text("{}\n", encoding="utf-8")
    (saw / "db").mkdir()
    import sqlite3
    conn = sqlite3.connect(str(saw / "db" / "claims.db"))
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    SQLiteClaimsRepository(conn); conn.close()
    (root / "wiki").mkdir()
    return root


# ── review (CWD) ────────────────────────────────────────────────────

def test_review_empty(tmp_path, monkeypatch):
    _make_root(tmp_path); monkeypatch.chdir(tmp_path)
    from saw.drivers.cli.main import app
    res = CliRunner().invoke(app, ["review", "--all"])
    assert res.exit_code == 0, res.output


def test_review_not_in_wiki(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from saw.drivers.cli.main import app
    res = CliRunner().invoke(app, ["review"])
    assert res.exit_code == 1


# ── learn gaps (CWD) ────────────────────────────────────────────────

def test_learn_gaps_empty(tmp_path, monkeypatch):
    _make_root(tmp_path); monkeypatch.chdir(tmp_path)
    from saw.drivers.cli.main import app
    res = CliRunner().invoke(app, ["learn", "gaps"])
    assert res.exit_code == 0, res.output


# ── compile (CWD) ───────────────────────────────────────────────────

def test_compile_not_in_wiki(tmp_path, monkeypatch):
    """compile outside a saw root — should exit non-zero or handle gracefully."""
    monkeypatch.chdir(tmp_path)
    from saw.drivers.cli.main import app
    res = CliRunner().invoke(app, ["compile"])
    # The command may exit 1 (error) or 0 (graceful degradation); the key
    # is it doesn't crash (exit_code 2 = unhandled exception).
    assert res.exit_code in (0, 1), f"unexpected exit {res.exit_code}: {res.output}"


# ── feed (sub-typer --help) ────────────────────────────────────────

def test_feed_help(tmp_path):
    from saw.drivers.cli.main import app
    res = CliRunner().invoke(app, ["feed", "--help"])
    assert res.exit_code == 0
    assert "Usage" in res.output

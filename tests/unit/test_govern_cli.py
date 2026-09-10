"""Functional CLI tests for `saw freshness` / `saw verify` (govern commands).

These commands resolve ``.saw/config.yaml`` from CWD (no --path flag), so
tests chdir into a tmp wiki root. Exercises the config-load → repo-init →
Governor-wiring path that the --help smoke test cannot reach.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from typer.testing import CliRunner


def _make_saw_root(root: Path) -> Path:
    """Create a minimal saw root: .saw/config.yaml + .saw/db/claims.db (schema)."""
    saw = root / ".saw"
    saw.mkdir(parents=True)
    (saw / "config.yaml").write_text("{}\n", encoding="utf-8")
    db_dir = saw / "db"
    db_dir.mkdir()
    db_path = db_dir / "claims.db"
    # Initialize the claims schema so the CLI's own connection sees the tables.
    conn = sqlite3.connect(str(db_path))
    try:
        from saw.adapters.storage.claims_repository import SQLiteClaimsRepository

        SQLiteClaimsRepository(conn)  # runs CREATE TABLE IF NOT EXISTS
    finally:
        conn.close()
    (root / "wiki").mkdir()
    return root


# ── freshness ──────────────────────────────────────────────────────

def test_freshness_empty_report(tmp_path: Path, monkeypatch) -> None:
    """`saw freshness` in a fresh wiki prints the distribution report (0 claims)."""
    _make_saw_root(tmp_path)
    monkeypatch.chdir(tmp_path)

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(app, ["freshness"])
    assert res.exit_code == 0, res.output
    assert "Freshness Distribution" in res.output


def test_freshness_not_in_wiki(tmp_path: Path, monkeypatch) -> None:
    """`saw freshness` outside a saw root exits 1 with a clear error."""
    monkeypatch.chdir(tmp_path)

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(app, ["freshness"])
    assert res.exit_code == 1, res.output
    assert "not in a saw wiki" in res.output.lower() or "saw init" in res.output.lower()


# ── verify ─────────────────────────────────────────────────────────

def test_verify_claim_not_found(tmp_path: Path, monkeypatch) -> None:
    """`saw verify <uuid>` for a non-existent claim exits 1 (claim not found)."""
    _make_saw_root(tmp_path)
    monkeypatch.chdir(tmp_path)

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(app, ["verify", "nonexistent-uuid"])
    assert res.exit_code == 1, res.output
    assert "not found" in res.output.lower()


def test_verify_not_in_wiki(tmp_path: Path, monkeypatch) -> None:
    """`saw verify` outside a saw root exits 1."""
    monkeypatch.chdir(tmp_path)

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(app, ["verify", "any-uuid"])
    assert res.exit_code == 1, res.output
    assert "not in a saw wiki" in res.output.lower() or "saw init" in res.output.lower()


# ── lint (CWD-based, like freshness/verify) ───────────────────────

def test_lint_empty_wiki(tmp_path: Path, monkeypatch) -> None:
    """`saw lint` in a fresh wiki prints the health report (no issues)."""
    _make_saw_root(tmp_path)
    monkeypatch.chdir(tmp_path)

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(app, ["lint"])
    assert res.exit_code == 0, res.output
    assert "Health" in res.output or "health" in res.output.lower()


def test_lint_not_in_wiki(tmp_path: Path, monkeypatch) -> None:
    """`saw lint` outside a saw root exits 1."""
    monkeypatch.chdir(tmp_path)

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(app, ["lint"])
    assert res.exit_code == 1, res.output
    assert "not in a saw wiki" in res.output.lower() or "saw init" in res.output.lower()


# ── search (--path based) ──────────────────────────────────────────

def test_search_not_in_wiki(tmp_path: Path) -> None:
    """`saw search` against a non-wiki path exits 1 (no wiki found)."""
    from saw.drivers.cli.main import app

    res = CliRunner().invoke(app, ["search", "anything", "--path", str(tmp_path / "nope")])
    assert res.exit_code == 1, res.output
    assert "no wiki found" in res.output.lower() or "saw init" in res.output.lower()


def test_search_empty_wiki(tmp_path: Path) -> None:
    """`saw search` in a fresh wiki exits 0 (no results, no crash)."""
    _make_saw_root(tmp_path)

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(app, ["search", "anything", "--path", str(tmp_path)])
    # Empty index → either "no results" or graceful empty; must not crash (exit 0)
    assert res.exit_code == 0, res.output


# ── review (CWD-based) ─────────────────────────────────────────────

def test_review_not_in_wiki(tmp_path: Path, monkeypatch) -> None:
    """`saw review` outside a saw root exits 1."""
    monkeypatch.chdir(tmp_path)
    from saw.drivers.cli.main import app
    res = CliRunner().invoke(app, ["review"])
    assert res.exit_code == 1, res.output


def test_review_empty_queue(tmp_path: Path, monkeypatch) -> None:
    """`saw review --all` in a fresh wiki exits 0 (empty review queue)."""
    _make_saw_root(tmp_path)
    monkeypatch.chdir(tmp_path)
    from saw.drivers.cli.main import app
    res = CliRunner().invoke(app, ["review", "--all"])
    assert res.exit_code == 0, res.output


# ── learn distill (LLM-gated branch) ───────────────────────────────

def test_learn_distill_no_llm(tmp_path: Path) -> None:
    """`saw learn distill` without an LLM configured exits non-zero with a
    clear 'LLM unavailable' message (covers the tier-check branch)."""
    _make_saw_root(tmp_path)
    from saw.drivers.cli.main import app
    res = CliRunner().invoke(app, ["learn", "distill", "--path", str(tmp_path)])
    assert res.exit_code != 0, res.output
    assert "llm" in res.output.lower() or "unavailable" in res.output.lower()

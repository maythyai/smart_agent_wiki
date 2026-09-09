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

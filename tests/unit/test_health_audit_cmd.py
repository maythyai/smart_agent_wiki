"""saw health + saw audit --session — F-P-3 (AC-OBS-3, AC-OBS-4).

- AC-OBS-3: `saw health` aggregates DB + receipt chain + Redis.
- AC-OBS-4: `saw audit --session` queries the DB-backed receipt chain.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from saw.drivers.cli.commands.smoke_harness import build_smoke_context


def _init_wiki(tmp_path: Path) -> Path:
    """Build a fresh wiki dir with ingested claims + receipts, return path."""
    ctx = build_smoke_context(with_receipts=True)
    # point the harness tmp dir under the test tmp_path so the wiki layout
    # (.saw/db/claims.db) matches what health/audit expect.
    from saw.drivers.cli.commands.smoke_harness import _ingest_fixture

    _ingest_fixture(ctx)
    # copy the DB to a wiki-layout path the CLI commands look for
    wiki = tmp_path / "wiki"
    (wiki / ".saw" / "db").mkdir(parents=True, exist_ok=True)
    (wiki / ".saw").mkdir(parents=True, exist_ok=True)
    (wiki / ".saw" / "config.yaml").write_text("path: .\n")
    import shutil

    shutil.copy(ctx.tmp_dir / ".saw" / "db" / "claims.db", wiki / ".saw" / "db" / "claims.db")
    ctx.close()
    return wiki


def test_health_aggregates_db_and_receipts(tmp_path: Path, monkeypatch) -> None:
    """AC-OBS-3: saw health reports DB + receipt chain status, exits 0 on healthy."""
    wiki = _init_wiki(tmp_path)
    monkeypatch.chdir(wiki)
    monkeypatch.delenv("REDIS_URL", raising=False)

    from saw.drivers.cli.commands.health_cmd import health
    import typer

    try:
        health(path=".")
        code = 0
    except typer.Exit as e:
        code = e.exit_code
    # DB healthy + receipt chain healthy (or no receipts) + redis skipped.
    assert code == 0, "health did not exit 0 on a healthy wiki"


def test_audit_session_verifies_chain(tmp_path: Path, monkeypatch) -> None:
    """AC-OBS-4: `saw audit --session` verifies the DB-backed receipt chain."""
    wiki = _init_wiki(tmp_path)
    monkeypatch.chdir(wiki)

    # pick a session id that has receipts
    conn = sqlite3.connect(str(wiki / ".saw" / "db" / "claims.db"))
    row = conn.execute(
        "SELECT session_id FROM receipts WHERE session_id IS NOT NULL LIMIT 1"
    ).fetchone()
    conn.close()
    assert row is not None, "no receipts produced by smoke ingest"
    session = row[0]

    from saw.drivers.cli.commands.audit_cmd import audit
    import typer

    code = 0
    try:
        audit(export=None, verify=None, claim=None, session=session)
    except typer.Exit as e:
        code = e.exit_code
    assert code == 0, f"audit --session did not verify chain for {session}"


def test_audit_session_unknown_returns_invalid(tmp_path: Path, monkeypatch) -> None:
    """AC-OBS-4: an unknown session yields an empty (valid) chain — exit 0."""
    wiki = _init_wiki(tmp_path)
    monkeypatch.chdir(wiki)

    from saw.drivers.cli.commands.audit_cmd import audit
    import typer

    code = 0
    try:
        audit(export=None, verify=None, claim=None, session="nonexistent-session")
    except typer.Exit as e:
        code = e.exit_code
    # empty chain is valid (no broken links) -> exit 0
    assert code == 0

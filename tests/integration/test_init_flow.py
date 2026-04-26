"""Integration test for `saw init` and `saw status` commands.

Tests the full init flow: directory creation, DB schema, agent templates.
Uses tmp_path fixture for isolation.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml
from typer.testing import CliRunner

from saw.drivers.cli.main import app

runner = CliRunner()


class TestInitFlow:
    """Test `saw init` creates all directories and files."""

    def test_init_creates_all_directories(self, tmp_path: Path):
        wiki_path = tmp_path / "test-wiki"
        result = runner.invoke(app, ["init", str(wiki_path)])
        assert result.exit_code == 0, f"Exit code {result.exit_code}: {result.output}"

        # Check .saw/ directory
        assert (wiki_path / ".saw").is_dir()
        assert (wiki_path / ".saw" / "config.yaml").is_file()
        assert (wiki_path / ".saw" / "wip.yaml").is_file()
        assert (wiki_path / ".saw" / "db" / "claims.db").is_file()

        # Check vault/
        assert (wiki_path / "vault").is_dir()

        # Check wiki/ namespaces
        assert (wiki_path / "wiki" / "concepts").is_dir()
        assert (wiki_path / "wiki" / "entities").is_dir()
        assert (wiki_path / "wiki" / "sources").is_dir()
        assert (wiki_path / "wiki" / "collections").is_dir()

    def test_init_creates_gitignore(self, tmp_path: Path):
        wiki_path = tmp_path / "test-wiki"
        runner.invoke(app, ["init", str(wiki_path)])

        gitignore = wiki_path / ".gitignore"
        assert gitignore.is_file()
        content = gitignore.read_text()
        assert ".saw/db/*.db-wal" in content
        assert ".saw/db/*.db-shm" in content
        assert ".env" in content

    def test_init_creates_git_repo(self, tmp_path: Path):
        wiki_path = tmp_path / "test-wiki"
        runner.invoke(app, ["init", str(wiki_path)])

        # .git/ should exist (or git init gracefully skipped)
        git_dir = wiki_path / ".git"
        assert git_dir.exists()

    def test_init_db_has_correct_tables(self, tmp_path: Path):
        wiki_path = tmp_path / "test-wiki"
        runner.invoke(app, ["init", str(wiki_path)])

        db_path = wiki_path / ".saw" / "db" / "claims.db"
        conn = sqlite3.connect(str(db_path))

        # Get all table names
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

        # Core tables
        assert "claim" in tables
        assert "claim_relation" in tables
        assert "entity" in tables
        assert "entity_relation" in tables
        assert "write_outbox" in tables
        assert "sink_tracking" in tables

        # FTS5 virtual table
        fts_tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND sql LIKE '%fts5%'"
            ).fetchall()
        }
        assert "fts_index" in fts_tables

        conn.close()

    def test_init_config_yaml_valid(self, tmp_path: Path):
        wiki_path = tmp_path / "test-wiki"
        runner.invoke(app, ["init", str(wiki_path)])

        config_path = wiki_path / ".saw" / "config.yaml"
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        assert "path" in config
        assert "llm" in config

    def test_init_wip_yaml_valid(self, tmp_path: Path):
        wiki_path = tmp_path / "test-wiki"
        runner.invoke(app, ["init", str(wiki_path)])

        wip_path = wiki_path / ".saw" / "wip.yaml"
        with open(wip_path, encoding="utf-8") as f:
            wip = yaml.safe_load(f)

        assert "active_tasks" in wip
        assert "next_steps" in wip
        assert "pending_questions" in wip
        assert "last_session" in wip


class TestInitWithAgent:
    """Test `saw init --agent` generates agent config files."""

    def test_init_with_claude_code(self, tmp_path: Path):
        wiki_path = tmp_path / "test-wiki"
        result = runner.invoke(
            app, ["init", str(wiki_path), "--agent", "claude-code"]
        )
        assert result.exit_code == 0

        claude_md = wiki_path / "CLAUDE.md"
        assert claude_md.is_file()
        content = claude_md.read_text()
        assert "Smart Agent Wiki" in content
        assert "saw status" in content

    def test_init_with_cursor(self, tmp_path: Path):
        wiki_path = tmp_path / "test-wiki"
        result = runner.invoke(
            app, ["init", str(wiki_path), "--agent", "cursor"]
        )
        assert result.exit_code == 0
        assert (wiki_path / ".cursorrules").is_file()

    def test_init_with_copilot(self, tmp_path: Path):
        wiki_path = tmp_path / "test-wiki"
        result = runner.invoke(
            app, ["init", str(wiki_path), "--agent", "copilot"]
        )
        assert result.exit_code == 0
        assert (wiki_path / "AGENTS.md").is_file()

    def test_init_with_gemini(self, tmp_path: Path):
        wiki_path = tmp_path / "test-wiki"
        result = runner.invoke(
            app, ["init", str(wiki_path), "--agent", "gemini"]
        )
        assert result.exit_code == 0
        assert (wiki_path / "GEMINI.md").is_file()


class TestStatusCommand:
    """Test `saw status` runs without error on initialized wiki."""

    def test_status_on_initialized_wiki(self, tmp_path: Path):
        wiki_path = tmp_path / "test-wiki"
        runner.invoke(app, ["init", str(wiki_path)])

        result = runner.invoke(app, ["status", str(wiki_path)])
        assert result.exit_code == 0
        assert "Claim Count" in result.output
        assert "Wiki Pages" in result.output

    def test_status_on_uninitialized_wiki(self, tmp_path: Path):
        result = runner.invoke(app, ["status", str(tmp_path)])
        assert result.exit_code == 1

    def test_status_shows_capability_tier(self, tmp_path: Path):
        wiki_path = tmp_path / "test-wiki"
        runner.invoke(app, ["init", str(wiki_path)])

        result = runner.invoke(app, ["status", str(wiki_path)])
        assert result.exit_code == 0
        # Tier should appear (OFFLINE in test env with no API keys)
        assert "Capability Tier" in result.output

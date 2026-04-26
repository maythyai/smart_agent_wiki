"""CLI `init` command - initialize a new Smart Agent Wiki.

Per D-18: Creates .saw/, vault/, wiki/, SQLite DB, Git repo.
Per D-23: WIP file .saw/wip.yaml for cross-session momentum.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import typer
import yaml
from rich.panel import Panel

from saw.adapters.storage.sqlite_connection import create_wiki_engine
from saw.config.agent_templates import generate_agent_config
from saw.config.defaults import DEFAULT_CONFIG, WIP_TEMPLATE
from saw.config.settings import detect_tier
from saw.domain.exceptions import SAWError


def init(
    path: str = typer.Argument(".", help="Wiki \u76ee\u5f55\u8def\u5f84"),
    agent: str | None = typer.Option(
        None, "--agent",
        help="Agent \u517c\u5bb9\u5c42: claude-code, cursor, copilot, gemini",
    ),
) -> None:
    """Create an empty wiki and initialize all storage layers."""
    try:
        wiki_path = Path(path).resolve()
        wiki_path.mkdir(parents=True, exist_ok=True)

        # 1. Create .saw/ config directory
        saw_dir = wiki_path / ".saw"
        saw_dir.mkdir(exist_ok=True)

        # 2. Write .saw/config.yaml
        config = dict(DEFAULT_CONFIG)
        config["path"] = str(wiki_path)
        config["agent"] = agent
        config_path = saw_dir / "config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        # 3. Write .saw/wip.yaml (per D-23)
        wip_path = saw_dir / "wip.yaml"
        with open(wip_path, "w", encoding="utf-8") as f:
            yaml.dump(WIP_TEMPLATE, f, default_flow_style=False, allow_unicode=True)

        # 4. Create SQLite DB with Claims schema
        db_dir = saw_dir / "db"
        db_dir.mkdir(exist_ok=True)
        db_path = db_dir / "claims.db"

        # Use raw SQLite to create all tables (claims + write_outbox + sink_tracking)
        engine = create_wiki_engine(db_path)
        from sqlalchemy import text
        with engine.connect() as conn:
            # Claims DB schema is initialized via the connection PRAGMA
            # We need to create the tables here
            from saw.adapters.storage.claims_repository import CLAIMS_DB_SCHEMA
            conn.execute(text("SELECT 1"))
        engine.dispose()

        # Use raw sqlite3 for schema init (FTS5 requires raw SQL)
        import sqlite3
        raw_conn = sqlite3.connect(str(db_path))
        from saw.adapters.storage.claims_repository import CLAIMS_DB_SCHEMA
        from saw.write_queue.queue import OUTBOX_DDL
        raw_conn.executescript(CLAIMS_DB_SCHEMA + OUTBOX_DDL)
        raw_conn.close()

        # 5. Create vault/ directory
        (wiki_path / "vault").mkdir(exist_ok=True)

        # 6. Create wiki/ namespace directories (per D-07)
        for subdir in ("concepts", "entities", "sources", "collections"):
            (wiki_path / "wiki" / subdir).mkdir(parents=True, exist_ok=True)

        # 7. Initialize Git repo
        _init_git(wiki_path)

        # 8. Create .gitignore
        gitignore = wiki_path / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text(
                ".saw/db/*.db-wal\n.saw/db/*.db-shm\n.env\n",
                encoding="utf-8",
            )

        # 9. Agent compatibility layer
        if agent:
            agent_path = generate_agent_config(agent, wiki_path)

        # 10. Display success
        from saw.drivers.cli.main import console
        tier = detect_tier()

        info = (
            f"[green]Wiki initialized at:[/green] {wiki_path}\n\n"
            f"[blue]Directories created:[/blue]\n"
            f"  {saw_dir}/\n"
            f"  {wiki_path / 'vault'}/\n"
            f"  {wiki_path / 'wiki'}/\n\n"
            f"[blue]Database:[/blue] {db_path}\n"
            f"[blue]Capability tier:[/blue] {tier.name}"
        )
        if agent:
            info += f"\n[blue]Agent config:[/blue] {agent_path}"

        console.print(Panel(info, title="Smart Agent Wiki Initialized"))

    except SAWError:
        raise
    except Exception as e:
        from saw.drivers.cli.main import console
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


def _init_git(wiki_path: Path) -> None:
    """Initialize Git repo if not already initialized."""
    git_dir = wiki_path / ".git"
    if git_dir.exists():
        return

    try:
        subprocess.run(
            ["git", "init"],
            cwd=str(wiki_path),
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Git init is best-effort; non-critical failure
        pass

"""``saw agents export/import`` tests — T3 (custom-role portability, Letta-inspired).

Covers exporting a custom role YAML to a file/stdout and importing a validated
YAML into ``.saw/agents/``. Uses ``tmp_path`` wikis; no LLM/DB.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

_CUSTOM_YAML = (
    "name: Researcher\n"
    "model_tier: sonnet\n"
    "system_prompt: You are a research agent.\n"
    "tools_allowed: [search, read]\n"
    "constraints: {max_steps: 5}\n"
)


def _make_wiki_with_role(root: Path) -> Path:
    """Create a wiki with one custom role under .saw/agents/."""
    (root / "wiki").mkdir(parents=True)
    (root / ".saw").mkdir(parents=True)
    (root / ".saw" / "config.yaml").write_text("llm: null\n")
    agents_dir = root / ".saw" / "agents"
    agents_dir.mkdir()
    (agents_dir / "researcher.yaml").write_text(_CUSTOM_YAML, encoding="utf-8")
    return root


# ── export ──────────────────────────────────────────────────────────

def test_t3_export_to_file(tmp_path: Path) -> None:
    """``saw agents export Researcher --out <file>`` copies the role YAML."""
    _make_wiki_with_role(tmp_path)
    out = tmp_path / "exported.yaml"

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(
        app,
        ["agents", "export", "Researcher", "--path", str(tmp_path), "--out", str(out)],
    )
    assert res.exit_code == 0, res.output
    assert out.is_file()
    # Content matches the source role (round-trippable YAML)
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert data["name"] == "Researcher"
    assert data["model_tier"] == "sonnet"


def test_t3_export_stdout(tmp_path: Path) -> None:
    """``saw agents export`` without --out prints YAML to stdout."""
    _make_wiki_with_role(tmp_path)

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(
        app, ["agents", "export", "Researcher", "--path", str(tmp_path)]
    )
    assert res.exit_code == 0, res.output
    data = yaml.safe_load(res.output)
    assert data["name"] == "Researcher"


def test_t3_export_unknown_role(tmp_path: Path) -> None:
    """Exporting a role that doesn't exist → error exit."""
    _make_wiki_with_role(tmp_path)

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(
        app, ["agents", "export", "Ghost", "--path", str(tmp_path)]
    )
    assert res.exit_code == 1, res.output
    assert "no custom role" in res.output.lower()


# ── import ──────────────────────────────────────────────────────────

def test_t3_import_copies_role(tmp_path: Path) -> None:
    """``saw agents import <file>`` copies a validated YAML into .saw/agents/."""
    _make_wiki_with_role(tmp_path)  # has .saw/agents/ already
    src = tmp_path / "new-role.yaml"
    src.write_text(
        "name: Archivist\n"
        "model_tier: rule\n"
        "system_prompt: Archive and dedupe.\n"
        "tools_allowed: []\n",
        encoding="utf-8",
    )

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(
        app, ["agents", "import", str(src), "--path", str(tmp_path)]
    )
    assert res.exit_code == 0, res.output
    dest = tmp_path / ".saw" / "agents" / "new-role.yaml"
    assert dest.is_file()
    assert yaml.safe_load(dest.read_text())["name"] == "Archivist"


def test_t3_import_rejects_builtin_name(tmp_path: Path) -> None:
    """Importing a YAML whose name collides with a built-in role → error."""
    _make_wiki_with_role(tmp_path)
    src = tmp_path / "builtin.yaml"
    src.write_text(
        "name: Librarian\nmodel_tier: sonnet\nsystem_prompt: hi\n", encoding="utf-8"
    )

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(
        app, ["agents", "import", str(src), "--path", str(tmp_path)]
    )
    assert res.exit_code == 1, res.output
    assert "collides" in res.output.lower()


def test_t3_import_rejects_missing_fields(tmp_path: Path) -> None:
    """Importing a YAML missing required fields → error."""
    _make_wiki_with_role(tmp_path)
    src = tmp_path / "bad.yaml"
    src.write_text("name: NoPrompt\nmodel_tier: sonnet\n", encoding="utf-8")

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(
        app, ["agents", "import", str(src), "--path", str(tmp_path)]
    )
    assert res.exit_code == 1, res.output
    assert "missing" in res.output.lower()


def test_t3_import_existing_no_force(tmp_path: Path) -> None:
    """Importing a file whose name already exists → error without --force."""
    _make_wiki_with_role(tmp_path)  # has .saw/agents/researcher.yaml
    src = tmp_path / "researcher.yaml"  # same filename
    src.write_text(
        "name: Researcher\nmodel_tier: rule\nsystem_prompt: x\n", encoding="utf-8"
    )

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(
        app, ["agents", "import", str(src), "--path", str(tmp_path)]
    )
    assert res.exit_code == 1, res.output
    assert "already exists" in res.output.lower()

    # --force overwrites
    res2 = CliRunner().invoke(
        app, ["agents", "import", str(src), "--path", str(tmp_path), "--force"]
    )
    assert res2.exit_code == 0, res2.output


# ── T4: shared activity-tracker accessor ───────────────────────────

def test_t4_shared_activity_tracker_accessor() -> None:
    """get_activity_tracker / set_activity_tracker live in the collaborate
    module (not web.app), so the CLI doesn't import the web layer."""
    from saw.engines.collaborate.activity_tracker import (
        AgentActivityTracker,
        get_activity_tracker,
        set_activity_tracker,
    )

    # Singleton starts unset (or whatever prior tests left); set, verify,
    # restore to None so this is order-independent.
    set_activity_tracker(None)
    assert get_activity_tracker() is None
    t = AgentActivityTracker()
    set_activity_tracker(t)
    assert get_activity_tracker() is t
    set_activity_tracker(None)  # cleanup
    assert get_activity_tracker() is None
    # web.app must still re-export it (backward compat for any importer)
    from saw.drivers.web import app as web_app
    assert web_app.get_activity_tracker is get_activity_tracker
    assert web_app.set_activity_tracker is set_activity_tracker

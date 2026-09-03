"""Policy reload CLI tests — T-F-Z-8 (AC-SEC-5 continued)."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner


def test_reload_no_policy_file_exits_0(tmp_path):
    """AC-SEC-5: when no Cedar policy exists, reload is a no-op (exit 0)."""
    from saw.drivers.cli.main import app

    res = CliRunner().invoke(app, ["policy", "reload", "--path", str(tmp_path)])
    assert res.exit_code == 0
    assert "No Cedar policy" in res.output


def test_reload_with_policy_file_invokes_engine(tmp_path):
    """AC-SEC-5: a policy file triggers CedarPolicyEngine.reload via CLI."""
    from saw.drivers.cli.main import app

    pol_dir = tmp_path / ".saw" / "policies"
    pol_dir.mkdir(parents=True)
    (pol_dir / "saw.cedar").write_text('permit (principal, action, resource);\n')

    fake_engine = MagicMock()
    fake_engine.reload.return_value = True
    with patch(
        "saw.adapters.crypto.cedar_policy.CedarPolicyEngine",
        return_value=fake_engine,
    ):
        res = CliRunner().invoke(app, ["policy", "reload", "--path", str(tmp_path)])
    assert res.exit_code == 0
    assert "reloaded" in res.output
    fake_engine.reload.assert_called_once()

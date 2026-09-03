"""Coverage gate — F-E-2 (AC-TEST-1).

Verifies the coverage ratchet config exists and that the gate mechanism
(fail_under) actually blocks a sub-threshold run. The gate is a regression
floor (60%, just below the 62% baseline); 80% is the documented raise-target.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_pyproject() -> dict:
    with (_REPO_ROOT / "pyproject.toml").open("rb") as f:
        return tomllib.load(f)


def test_coverage_gate_configured() -> None:
    """AC-TEST-1: a coverage fail_under ratchet is configured in pyproject."""
    cfg = _load_pyproject()
    report = cfg.get("tool", {}).get("coverage", {}).get("report", {})
    assert "fail_under" in report, "no [tool.coverage.report] fail_under gate"
    floor = report["fail_under"]
    # Floor must be at/below the measured baseline (62%) so it is a
    # regression ratchet, not a day-one-blocker. Target = 80% (raise over time).
    assert 50 <= floor <= 62, f"fail_under {floor} outside the ratchet band [50,62]"
    run_cfg = cfg["tool"]["coverage"]["run"]
    assert "src/saw" in run_cfg.get("source", []), "coverage source not src/saw"


def test_gate_blocks_below_threshold() -> None:
    """AC-TEST-1: the coverage CLI gate exits non-zero below fail_under.

    Drives the real `coverage` tool on a <100%-covered fixture so the gate
    mechanism (not just the config) is proven to block sub-threshold runs.
    """
    with tempfile.TemporaryDirectory() as tmp:
        mod = Path(tmp) / "partial.py"
        # An uncalled function leaves its body uncovered -> coverage < 100%.
        mod.write_text("a = 1\nb = 2\ndef uncalled():\n    return 3\n")
        run = subprocess.run(
            [sys.executable, "-m", "coverage", "run", "--source", str(mod.parent), str(mod)],
            capture_output=True,
            text=True,
            check=False,
            cwd=tmp,
        )
        assert run.returncode == 0, run.stderr

        # Coverage is <100% (c=3 never runs): gate at 99 must block, at 1 pass.
        block = subprocess.run(
            [sys.executable, "-m", "coverage", "report", "--fail-under=99"],
            capture_output=True,
            text=True,
            check=False,
            cwd=tmp,
        )
        assert block.returncode != 0, "gate did not block a <100% run at fail_under=99"

        allow = subprocess.run(
            [sys.executable, "-m", "coverage", "report", "--fail-under=1"],
            capture_output=True,
            text=True,
            check=False,
            cwd=tmp,
        )
        assert allow.returncode == 0, "gate blocked a covered run at fail_under=1"

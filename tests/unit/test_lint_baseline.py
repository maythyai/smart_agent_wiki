"""Lint baseline gate — F-Z-4/F-Z-6 (AC-LINT-2 continued).

Asserts ruff reports 0 unused-import (F401) and 0 unused-variable (F841)
errors on ``src/saw``. F401 was closed in v1.4.0 (Z-4); F841 was closed in
v1.5.0 (Z-6, 27 dead assigns hand-audited). Both rules are now enforced in
``pyproject.toml``; this test pins the floor so a drift regresses the gate.
"""
from __future__ import annotations

import subprocess
import sys


def _run_ruff(select: str) -> tuple[int, str]:
    """Run ruff on src/saw with the given --select; return (rc, output)."""
    proc = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "src/saw", "--select", select],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def test_no_unused_imports_f401() -> None:
    """AC-LINT-2: F401 (unused import) baseline is 0 (closed v1.4.0 Z-4)."""
    rc, out = _run_ruff("F401")
    assert rc == 0, f"F401 regressions detected:\n{out}"


def test_no_unused_variables_f841() -> None:
    """AC-LINT-2: F841 (unused variable) baseline is 0 (closed v1.5.0 Z-6)."""
    rc, out = _run_ruff("F841")
    assert rc == 0, f"F841 regressions detected:\n{out}"

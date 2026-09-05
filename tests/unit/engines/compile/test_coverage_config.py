"""TC-COV-01: pyproject.toml fail_under=65 (AC-COV-2)."""
from __future__ import annotations

import tomllib
from pathlib import Path


def test_fail_under_is_65():
    """pyproject.toml [tool.coverage.report] fail_under must be 65."""
    pyproject = Path(__file__).resolve().parents[4] / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    fail_under = data["tool"]["coverage"]["report"]["fail_under"]
    assert fail_under == 65, f"Expected fail_under=65, got {fail_under}"

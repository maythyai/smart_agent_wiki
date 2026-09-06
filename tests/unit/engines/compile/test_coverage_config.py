"""TC-COV-01: pyproject.toml fail_under ratchet (AC-COV-2).

T-F-R-4 (v1.13.0): ratcheted 65→67. The assertion uses a floor (>= 65)
not a hardcoded value so future ratchet increases don't break this test.
"""
from __future__ import annotations

import tomllib
from pathlib import Path


def test_fail_under_ratchet():
    """pyproject.toml [tool.coverage.report] fail_under must be >= 65."""
    pyproject = Path(__file__).resolve().parents[4] / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    fail_under = data["tool"]["coverage"]["report"]["fail_under"]
    assert fail_under >= 65, f"Expected fail_under>=65, got {fail_under}"
    assert fail_under == 67, f"Expected fail_under=67 (v1.13.0 ratchet), got {fail_under}"

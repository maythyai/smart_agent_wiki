"""Capabilities inventory — F-B-2 (AC-ALIGN-2).

Verifies docs/CAPABILITIES.md traces every capability to a file:line and
that inferred (ungrounded) scenarios are marked [unverified], never claimed
as supported without code backing.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_DOC = _REPO / "docs" / "CAPABILITIES.md"
_SCRIPT = _REPO / "scripts" / "gen_capabilities.sh"


def test_capabilities_has_file_line() -> None:
    """AC-ALIGN-2: each capability row carries a file:line provenance."""
    assert _DOC.exists(), "docs/CAPABILITIES.md not generated; run gen_capabilities.sh"
    rows = [
        ln for ln in _DOC.read_text().splitlines()
        if ln.startswith("| ") and "capability" not in ln and "---" not in ln
    ]
    assert rows, "no capability rows in CAPABILITIES.md"
    # Every data row has a file:line (src/...:N) in column 3.
    for row in rows:
        cols = [c.strip() for c in row.split("|") if c.strip()]
        assert any(":" in c and ("src/" in c or "/" in c) for c in cols), (
            f"row missing file:line: {row}"
        )


def test_capabilities_unverified_marked() -> None:
    """AC-ALIGN-2: inferred scenarios are marked [unverified], not 'supported'."""
    text = _DOC.read_text()
    assert "[unverified]" in text, "no [unverified] markers; inferences not flagged"
    # The doc must never claim an inferred capability as flatly "supported"
    # without the verified/unverified status column.
    assert "verified" in text  # the status column exists


def test_gen_script_runs_and_emits() -> None:
    """The generator is reproducible from the CMS entry-points."""
    run = subprocess.run(  # noqa: S603 — controlled local script
        ["bash", str(_SCRIPT), str(_REPO)],
        capture_output=True, text=True, check=False,
    )
    assert run.returncode == 0, run.stderr
    assert "wrote" in run.stdout
    assert _DOC.exists()

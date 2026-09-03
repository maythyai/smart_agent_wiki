"""CI workflow gates — F-A-6 / F-E-3 (AC-TEST-2, AC-E2E-1).

Asserts the CI workflow wires the smoke job (A-6) and the coverage gate
(E-3) so a regression in either turns CI red. Parses the YAML statically
(can't run GitHub Actions in-unit).
"""

from __future__ import annotations

from pathlib import Path

import yaml

_CI = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


def _ci() -> dict:
    return yaml.safe_load(_CI.read_text())


def test_ci_has_smoke_job() -> None:
    """AC-E2E-1: a `smoke` job runs `saw smoke` as a CI gate."""
    jobs = _ci()["jobs"]
    assert "smoke" in jobs, "no smoke job in ci.yml"
    steps = jobs["smoke"]["steps"]
    run_steps = [s for s in steps if "run" in s]
    assert any("saw smoke" in s["run"] for s in run_steps), (
        "smoke job does not invoke `saw smoke`"
    )


def test_ci_has_coverage_gate() -> None:
    """AC-TEST-1: the python job enforces the coverage ratchet."""
    python_steps = _ci()["jobs"]["python"]["steps"]
    cov_steps = [
        s for s in python_steps
        if "run" in s and "--cov" in s["run"]
    ]
    assert cov_steps, "python job has no coverage gate step"
    # The gate must reference the ratchet floor (configured in pyproject).
    assert any("src/saw" in s["run"] for s in cov_steps)


def test_ci_lint_gate_present() -> None:
    """The ruff lint gate is wired (baseline-debt cleanup tracked as F-Z-1)."""
    python_steps = _ci()["jobs"]["python"]["steps"]
    assert any(
        "run" in s and "ruff check" in s["run"] for s in python_steps
    ), "no ruff lint step"


def test_ci_coverage_no_heavy_ignore() -> None:
    """AC-LINT-3: the coverage gate no longer --ignores heavy-SDK learn tests;
    they skip via importorskip instead."""
    cov_steps = [
        s for s in _ci()["jobs"]["python"]["steps"]
        if "run" in s and "--cov" in s["run"]
    ]
    assert cov_steps
    run = cov_steps[0]["run"]
    assert "--ignore=tests/unit/engines/learn" not in run, (
        "coverage step still --ignores learn tests (should rely on importorskip)"
    )


def test_fsrs_skips_without_sdk() -> None:
    """AC-LINT-3: test_fsrs guards its `fsrs` import with importorskip."""
    src = (Path(__file__).resolve().parents[2] / "tests/unit/engines/learn/test_fsrs.py").read_text()
    assert "importorskip" in src and "fsrs" in src, (
        "test_fsrs does not importorskip the optional fsrs extra"
    )

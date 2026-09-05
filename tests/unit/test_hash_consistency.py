"""Tag hash consistency test (F-O-4, AC-HASH-1).

Verifies that the v1.10.0 git tag commit hash is consistent across:
  1. ``git rev-list -n1 v1.10.0`` (authoritative)
  2. ``docs/strategy/ROADMAP.md``
  3. ``.csp/lifecycle-state.json``
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ac_hash_1_tag_hash_consistent():
    """``git rev-list -n1 v1.10.0`` short hash must match the hash recorded
    in ROADMAP.md and lifecycle-state.json."""
    result = subprocess.run(
        ["git", "rev-list", "-n1", "v1.10.0"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        import pytest
        pytest.skip("git not available or tag v1.10.0 not found")

    full_hash = result.stdout.strip()
    short_hash = full_hash[:7]

    # Check ROADMAP
    roadmap = REPO_ROOT / "docs" / "strategy" / "ROADMAP.md"
    roadmap_content = roadmap.read_text(encoding="utf-8")
    assert short_hash in roadmap_content, (
        f"ROADMAP.md should reference tag hash {short_hash}"
    )

    # Check lifecycle-state.json
    lifecycle = REPO_ROOT / ".csp" / "lifecycle-state.json"
    lifecycle_content = lifecycle.read_text(encoding="utf-8")
    assert short_hash in lifecycle_content, (
        f"lifecycle-state.json should reference tag hash {short_hash}"
    )

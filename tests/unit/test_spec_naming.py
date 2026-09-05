"""Spec naming tests (F-O-4, AC-SPEC-1/2)."""
from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_F_N_1 = REPO_ROOT / ".csp" / "specs" / "SPEC-F-N-1.md"


# ── AC-SPEC-1: no stale command name in SPEC-F-N-1 ──────────────────

def test_ac_spec_1_no_stale_command_name():
    """SPEC-F-N-1.md must not contain the old 'saw search rebuild-embeddings'
    command name (implementation is a top-level ``saw rebuild-embeddings``
    per main.py:73)."""
    content = SPEC_F_N_1.read_text(encoding="utf-8")
    assert "saw search rebuild-embeddings" not in content, (
        "SPEC-F-N-1.md still contains the stale 'saw search rebuild-embeddings' "
        "command name — should be 'saw rebuild-embeddings'"
    )


def test_ac_spec_1_correct_command_name_present():
    """SPEC-F-N-1.md should reference the correct 'saw rebuild-embeddings'
    top-level command."""
    content = SPEC_F_N_1.read_text(encoding="utf-8")
    assert "saw rebuild-embeddings" in content


# ── AC-SPEC-2: implementation unchanged (top-level command exists) ───

def test_ac_spec_2_rebuild_command_registered():
    """``saw rebuild-embeddings`` is a registered top-level command in
    main.py (AC-SPEC-2). We verify via the source file rather than a
    subprocess so the test is CI-safe without a full CLI install."""
    main_py = REPO_ROOT / "src" / "saw" / "drivers" / "cli" / "main.py"
    content = main_py.read_text(encoding="utf-8")
    assert 'rebuild-embeddings' in content, (
        "main.py should register the 'rebuild-embeddings' command"
    )

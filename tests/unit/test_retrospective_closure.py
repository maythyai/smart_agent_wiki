"""T-F-R-5: retrospective Q1/Q3 closure notes assertions (AC-E-1/2)."""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_RETRO = _REPO_ROOT / ".csp" / "artifacts" / "retrospective-v1.12.0.md"


def _read_retrospective() -> str:
    assert _RETRO.exists(), "retrospective-v1.12.0.md must exist"
    return _RETRO.read_text(encoding="utf-8")


def test_ac_e_1_q1_closure_note():
    """AC-E-1: Q1 finding contains v1.13.0 closure note + commit 84e1776."""
    text = _read_retrospective()
    # Find Q1 section
    q1_start = text.find("### Q1")
    assert q1_start != -1, "Q1 section must exist"
    # Get the Q1 section content (up to next ### or end)
    q1_end = text.find("### Q2", q1_start)
    if q1_end == -1:
        q1_end = len(text)
    q1_section = text[q1_start:q1_end]

    assert "v1.13.0 闭合" in q1_section, (
        "Q1 must contain 'v1.13.0 闭合' closure annotation"
    )
    assert "84e1776" in q1_section, (
        "Q1 closure must reference commit 84e1776"
    )
    assert "closed" in q1_section.lower(), "Q1 must be marked closed"


def test_ac_e_2_q3_closure_note():
    """AC-E-2: Q3 finding contains v1.13.0 closure note + ST fallback removed."""
    text = _read_retrospective()
    # Find Q3 section
    q3_start = text.find("### Q3")
    assert q3_start != -1, "Q3 section must exist"
    # Get the Q3 section content
    q3_end = text.find("### 续留", q3_start)
    if q3_end == -1:
        q3_end = text.find("\n---\n", q3_start)
    if q3_end == -1:
        q3_end = len(text)
    q3_section = text[q3_start:q3_end]

    assert "v1.13.0 闭合" in q3_section, (
        "Q3 must contain 'v1.13.0 闭合' closure annotation"
    )
    assert "ST fallback" in q3_section, (
        "Q3 closure must mention ST fallback removal"
    )
    assert "closed" in q3_section.lower(), "Q3 must be marked closed"

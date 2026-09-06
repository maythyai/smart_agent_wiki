"""T-F-R-3: CHANGELOG.md existence + retrospective assertions (AC-C-2/3)."""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_changelog() -> str:
    changelog = _REPO_ROOT / "CHANGELOG.md"
    assert changelog.exists(), "CHANGELOG.md must exist at project root"
    return changelog.read_text(encoding="utf-8")


def test_ac_c_2_changelog_exists_and_has_v1_11_0():
    """AC-C-2: CHANGELOG.md exists + contains v1.11.0 /workflows change."""
    text = _read_changelog()
    assert "v1.11.0" in text, "CHANGELOG must contain v1.11.0 section"
    assert "workflows" in text.lower(), (
        "CHANGELOG must mention /workflows REST behavior change"
    )
    assert "definition_name" in text, (
        "CHANGELOG must mention definition_name field rename"
    )


def test_ac_c_3_changelog_retrospective():
    """AC-C-3: CHANGELOG contains v1.12.0 embedding pivot + v1.13.0 entries."""
    text = _read_changelog()
    assert "v1.12.0" in text, "CHANGELOG must contain v1.12.0 section"
    assert "embedding" in text.lower(), (
        "CHANGELOG must mention embedding API pivot"
    )
    assert "v1.13.0" in text, "CHANGELOG must contain v1.13.0 section"
    assert "ingest" in text.lower(), (
        "CHANGELOG must mention ingest directory recursion fix"
    )

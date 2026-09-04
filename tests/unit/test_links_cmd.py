"""Links suggest + audit tests — T-F-L-1 / F-L-2 (AC-LINK-1, AC-LINK-2)."""
from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner


def _make_wiki(root: Path) -> Path:
    """Create a minimal wiki under root/wiki with frontmatter pages."""
    wiki = root / "wiki" / "concepts"
    wiki.mkdir(parents=True)
    (root / ".saw").mkdir(parents=True)
    (root / ".saw" / "config.yaml").write_text("llm: null\n")
    # Page A: tags [ml], links to [[C]] only.
    (wiki / "alpha.md").write_text(
        "---\ntitle: Alpha\ntags: [ml]\n---\n# Alpha\nSee [[C]] for more.\n"
    )
    # Page B: tags [ml], not yet linked from A.
    (wiki / "beta.md").write_text(
        "---\ntitle: Beta\ntags: [ml]\n---\n# Beta\nBeta content.\n"
    )
    # Page C: already linked from A.
    (wiki / "c.md").write_text(
        "---\ntitle: C\ntags: [ml]\n---\n# C\nC content.\n"
    )
    # Page Orphan: nothing links to it, it links to nothing.
    (wiki / "orphan.md").write_text(
        "---\ntitle: Orphan\ntags: [misc]\n---\n# Orphan\nNo links here.\n"
    )
    # Page with a broken link.
    (wiki / "broken.md").write_text(
        "---\ntitle: Broken\ntags: [misc]\n---\n# Broken\nSee [[nonexistent]].\n"
    )
    return root


def test_suggest_excludes_already_linked(tmp_path):
    """AC-LINK-1: suggest recommends related unlinked pages; already-linked excluded."""
    from saw.drivers.cli.main import app

    _make_wiki(tmp_path)
    res = CliRunner().invoke(app, ["links", "suggest", "alpha", "--path", str(tmp_path)])
    assert res.exit_code == 0, res.output
    # Beta shares the [ml] tag → suggested. C is already linked → not suggested.
    assert "beta" in res.output.lower()
    assert "/c.md" not in res.output or "c.md" not in "".join(
        line for line in res.output.splitlines() if "beta" not in line.lower()
    )


def test_suggest_unknown_page_exits_1(tmp_path):
    from saw.drivers.cli.main import app

    _make_wiki(tmp_path)
    res = CliRunner().invoke(app, ["links", "suggest", "nope", "--path", str(tmp_path)])
    assert res.exit_code == 1


def test_audit_finds_orphans_and_broken(tmp_path):
    """AC-LINK-2: audit reports orphan pages + broken links."""
    from saw.drivers.cli.main import app

    _make_wiki(tmp_path)
    res = CliRunner().invoke(app, ["links", "audit", "--path", str(tmp_path)])
    assert res.exit_code == 0, res.output
    out = res.output.lower()
    # Orphan page has no backlinks.
    assert "orphan" in out
    # Broken link to [[nonexistent]].
    assert "nonexistent" in out

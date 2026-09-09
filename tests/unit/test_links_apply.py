"""Links apply tests — T-F-T-2 (AC-B-1/2/3/4).

Tests the ``saw links apply`` subcommand: dry-run preview, ``--confirm``
write-back, dedup, and post-apply audit. All tests use ``tmp_path`` wikis
and mock ``compute_related_pages`` — no embedding/vLLM.
"""
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
    return root


def _mock_related_pages(suggestions: list[dict]):
    """Return a mock function that ignores args and returns *suggestions*."""
    def _mock(slug, wiki_repo, top_k=8, conn=None, workspace_id="default"):
        return suggestions
    return _mock


# ── AC-B-1: dry-run does not write ──────────────────────────────────

def test_ac_b_1_dry_run_no_write(tmp_path: Path, monkeypatch) -> None:
    """AC-B-1: ``saw links apply alpha`` (no --confirm) → file unchanged."""
    _make_wiki(tmp_path)
    alpha_file = tmp_path / "wiki" / "concepts" / "alpha.md"
    original = alpha_file.read_text()

    monkeypatch.setattr(
        "saw.engines.query.related_pages.compute_related_pages",
        _mock_related_pages([
            {"slug": "beta.md", "title": "Beta", "score": 0.8,
             "reasons": ["shared tags"]},
        ]),
    )

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(
        app, ["links", "apply", "alpha", "--path", str(tmp_path)]
    )
    assert res.exit_code == 0, res.output
    # File must not be modified
    assert alpha_file.read_text() == original
    # Output mentions dry run
    assert "dry run" in res.output.lower() or "dry" in res.output.lower()


# ── AC-B-2: confirm writes ## Related + related sync ───────────────

def test_ac_b_2_confirm_writes_related(tmp_path: Path, monkeypatch) -> None:
    """AC-B-2: ``--confirm`` → page gets ``## Related`` + ``[[beta]]``
    + frontmatter ``related`` synced."""
    _make_wiki(tmp_path)
    alpha_file = tmp_path / "wiki" / "concepts" / "alpha.md"

    monkeypatch.setattr(
        "saw.engines.query.related_pages.compute_related_pages",
        _mock_related_pages([
            {"slug": "beta.md", "title": "Beta", "score": 0.8,
             "reasons": ["shared tags"]},
        ]),
    )

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(
        app, ["links", "apply", "alpha", "--path", str(tmp_path), "--confirm"]
    )
    assert res.exit_code == 0, res.output
    assert "1 links applied" in res.output

    # Read the page back
    from saw.adapters.storage.wiki_repository import WikiRepository

    wiki = WikiRepository(tmp_path / "wiki")
    page = wiki.read("concepts/alpha.md")
    assert page is not None
    # Content has ## Related section with [[beta]]
    assert "## Related" in page.content
    assert "[[beta]]" in page.content
    # Frontmatter related field synced
    assert "beta" in page.related


# ── AC-B-3: already linked → skipped ────────────────────────────────

def test_ac_b_3_already_linked_skipped(tmp_path: Path, monkeypatch) -> None:
    """AC-B-3: page already has ``[[c]]`` → suggest c again → c is filtered
    out (not duplicated). Only beta is applied; ``[[c]]`` appears once."""
    _make_wiki(tmp_path)

    # Suggest both beta (not linked) and c (already linked via [[C]])
    monkeypatch.setattr(
        "saw.engines.query.related_pages.compute_related_pages",
        _mock_related_pages([
            {"slug": "beta.md", "title": "Beta", "score": 0.8,
             "reasons": ["shared tags"]},
            {"slug": "c.md", "title": "C", "score": 0.9,
             "reasons": ["shared tags"]},
        ]),
    )

    from saw.drivers.cli.main import app

    res = CliRunner().invoke(
        app, ["links", "apply", "alpha", "--path", str(tmp_path), "--confirm"]
    )
    assert res.exit_code == 0, res.output
    # Only beta applied (c was pre-filtered as already-linked)
    assert "1 links applied" in res.output

    from saw.adapters.storage.wiki_repository import WikiRepository

    wiki = WikiRepository(tmp_path / "wiki")
    page = wiki.read("concepts/alpha.md")
    assert page is not None
    # [[c]] should appear exactly once (original link, not duplicated)
    assert page.content.lower().count("[[c]]") == 1
    # beta was applied
    assert "[[beta]]" in page.content


# ── AC-B-4: post-apply audit → no new broken links ─────────────────

def test_ac_b_4_apply_then_audit_no_broken(tmp_path: Path, monkeypatch) -> None:
    """AC-B-4: after apply, ``saw links audit`` shows no new broken links."""
    _make_wiki(tmp_path)

    monkeypatch.setattr(
        "saw.engines.query.related_pages.compute_related_pages",
        _mock_related_pages([
            {"slug": "beta.md", "title": "Beta", "score": 0.8,
             "reasons": ["shared tags"]},
        ]),
    )

    from saw.drivers.cli.main import app

    runner = CliRunner()
    # Apply links
    res = runner.invoke(
        app, ["links", "apply", "alpha", "--path", str(tmp_path), "--confirm"]
    )
    assert res.exit_code == 0, res.output

    # Audit: no broken links (beta exists)
    res2 = runner.invoke(
        app, ["links", "audit", "--path", str(tmp_path)]
    )
    assert res2.exit_code == 0, res2.output
    assert "beta" not in res2.output.lower().replace("no broken", "") or \
        "no broken links" in res2.output.lower()


# ── T2: rollback restores pre-apply state ───────────────────────────

def test_t2_apply_saves_rollback_snapshot(tmp_path: Path, monkeypatch) -> None:
    """``links apply --confirm`` persists a rollback snapshot before writing."""
    _make_wiki(tmp_path)
    monkeypatch.setattr(
        "saw.engines.query.related_pages.compute_related_pages",
        _mock_related_pages([
            {"slug": "beta.md", "title": "Beta", "score": 0.8,
             "reasons": ["shared tags"]},
        ]),
    )
    from saw.drivers.cli.main import app

    res = CliRunner().invoke(
        app, ["links", "apply", "alpha", "--path", str(tmp_path), "--confirm"]
    )
    assert res.exit_code == 0, res.output
    snap = tmp_path / ".saw" / "links-rollback" / "alpha.json"
    assert snap.is_file(), "rollback snapshot not saved"


def test_t2_rollback_restores_pre_apply(tmp_path: Path, monkeypatch) -> None:
    """``links rollback`` restores content + related to pre-apply state."""
    _make_wiki(tmp_path)
    alpha_file = tmp_path / "wiki" / "concepts" / "alpha.md"
    original = alpha_file.read_text()

    monkeypatch.setattr(
        "saw.engines.query.related_pages.compute_related_pages",
        _mock_related_pages([
            {"slug": "beta.md", "title": "Beta", "score": 0.8,
             "reasons": ["shared tags"]},
        ]),
    )
    from saw.drivers.cli.main import app

    runner = CliRunner()
    # Apply mutates alpha (adds [[beta]] + related)
    res = runner.invoke(
        app, ["links", "apply", "alpha", "--path", str(tmp_path), "--confirm"]
    )
    assert res.exit_code == 0, res.output
    assert "[[beta]]" in alpha_file.read_text()

    # Rollback restores the pre-apply state
    res2 = runner.invoke(
        app, ["links", "rollback", "alpha", "--path", str(tmp_path)]
    )
    assert res2.exit_code == 0, res2.output
    assert "rolled back" in res2.output.lower()
    # Re-read the restored page: the applied [[beta]] link and related entry
    # must be gone. (We assert on the parsed page rather than raw bytes
    # because WikiRepository.write normalizes frontmatter field order/adds
    # metadata fields, so byte-equality with the original file does not hold.)
    from saw.adapters.storage.wiki_repository import WikiRepository
    wiki = WikiRepository(tmp_path / "wiki")
    page = wiki.read("concepts/alpha.md")
    assert page is not None
    assert "[[beta]]" not in page.content
    assert "## Related" not in page.content
    assert "beta" not in page.related
    # Snapshot cleared after rollback
    assert not (tmp_path / ".saw" / "links-rollback" / "alpha.json").is_file()


def test_t2_rollback_no_snapshot(tmp_path: Path) -> None:
    """``links rollback`` with no prior apply is a graceful no-op."""
    _make_wiki(tmp_path)
    from saw.drivers.cli.main import app

    res = CliRunner().invoke(
        app, ["links", "rollback", "alpha", "--path", str(tmp_path)]
    )
    assert res.exit_code == 0, res.output
    assert "no rollback snapshot" in res.output.lower()

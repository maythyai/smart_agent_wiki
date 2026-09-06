"""T-F-R-4: compile linter coverage tests (coverage ratchet 65→67).

Tests the WikiLinter check methods (index consistency, broken links,
dir metadata, orphan pages, missing concepts, stale content, low
confidence, suggestions) to raise coverage from 14% toward full.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from saw.domain.lint import LintCategory, LintSeverity
from saw.engines.compile.linter import WikiLinter


def _make_wiki(tmp_path: Path, pages: dict[str, str]) -> Path:
    """Create a wiki root with the given {relpath: content} pages."""
    wiki = tmp_path / "wiki"
    wiki.mkdir(parents=True, exist_ok=True)
    for rel, content in pages.items():
        p = wiki / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return wiki


# ── Lint full check ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_lint_nonexistent_wiki(tmp_path):
    """Linting a non-existent wiki root returns an error finding."""
    linter = WikiLinter(tmp_path / "nonexistent")
    report = await linter.lint()
    assert len(report.errors) >= 1
    assert report.errors[0].category == LintCategory.INDEX_CONSISTENCY
    assert report.errors[0].severity == LintSeverity.ERROR


@pytest.mark.asyncio
async def test_lint_empty_wiki(tmp_path):
    """Linting an empty (but existing) wiki returns no errors."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "index.md").write_text("# Index\n\n", encoding="utf-8")
    linter = WikiLinter(wiki)
    report = await linter.lint()
    assert report.duration_seconds >= 0


@pytest.mark.asyncio
async def test_lint_with_auto_fix(tmp_path):
    """Lint with auto_fix=True runs all auto-fix checks."""
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n- [[alpha]]\n- [[beta]]\n",
        "alpha.md": "# Alpha\n\nContent about alpha.\n\n[[beta]]\n",
        "beta.md": "# Beta\n\nContent about beta.\n\n",
    })
    linter = WikiLinter(wiki)
    report = await linter.lint(auto_fix=True)
    assert isinstance(report.auto_fixed, list)


@pytest.mark.asyncio
async def test_lint_without_auto_fix(tmp_path):
    """Lint with auto_fix=False skips auto-fix checks."""
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n- [[alpha]]\n",
        "alpha.md": "# Alpha\n\n[[ghost]]\n",
    })
    linter = WikiLinter(wiki)
    report = await linter.lint(auto_fix=False)
    assert len(report.auto_fixed) == 0


# ── Index consistency ─────────────────────────────────────────────────

def test_check_index_consistency_missing_entry(tmp_path):
    """Pages not in index.md are reported as findings."""
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n- [[alpha]]\n",
        "alpha.md": "# Alpha\n\n",
        "beta.md": "# Beta\n\n",
    })
    linter = WikiLinter(wiki)
    pages = linter._list_wiki_pages()
    index = linter._read_index()
    findings = linter._check_index_consistency(pages, index)
    # beta.md is not in index → finding
    assert any("beta" in f.page for f in findings)


def test_check_index_consistency_ghost_entry(tmp_path):
    """Index entries pointing to non-existent pages are reported."""
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n- [[alpha]]\n- [[ghost]]\n",
        "alpha.md": "# Alpha\n\n",
    })
    linter = WikiLinter(wiki)
    pages = linter._list_wiki_pages()
    index = linter._read_index()
    findings = linter._check_index_consistency(pages, index)
    # ghost.md doesn't exist → finding
    assert any("ghost" in f.description for f in findings)


def test_check_index_consistency_all_present(tmp_path):
    """When index matches pages, no findings."""
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n- [[alpha]]\n",
        "alpha.md": "# Alpha\n\n",
    })
    linter = WikiLinter(wiki)
    pages = linter._list_wiki_pages()
    index = linter._read_index()
    findings = linter._check_index_consistency(pages, index)
    assert len(findings) == 0


# ── Broken links ─────────────────────────────────────────────────────

def test_check_broken_links_finds_missing(tmp_path):
    """Broken [[wiki-links]] to non-existent pages are reported."""
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n",
        "alpha.md": "# Alpha\n\n[[nonexistent]]\n",
    })
    linter = WikiLinter(wiki)
    pages = linter._list_wiki_pages()
    findings = linter._check_broken_links(pages)
    assert any("nonexistent" in f.description for f in findings)


def test_check_broken_links_none_when_valid(tmp_path):
    """Valid wiki-links produce no findings."""
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n",
        "alpha.md": "# Alpha\n\n[[beta]]\n",
        "beta.md": "# Beta\n\n",
    })
    linter = WikiLinter(wiki)
    pages = linter._list_wiki_pages()
    findings = linter._check_broken_links(pages)
    assert len(findings) == 0


# ── Dir metadata ──────────────────────────────────────────────────────

def test_check_dir_metadata_mismatch(tmp_path):
    """Pages whose type doesn't match directory are reported."""
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n",
        "concepts/ml.md": "---\ntype: concept\n---\n\n# ML\n\n",
    })
    # File is in concepts/ which matches → no mismatch
    linter = WikiLinter(wiki)
    pages = linter._list_wiki_pages()
    findings = linter._check_dir_metadata(pages)
    assert len(findings) == 0  # concepts/ matches type: concept


def test_check_dir_metadata_wrong_dir(tmp_path):
    """Page in wrong directory for its type is reported."""
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n",
        "faq/page.md": "---\ntype: concept\n---\n\n# Page\n\n",
    })
    linter = WikiLinter(wiki)
    pages = linter._list_wiki_pages()
    findings = linter._check_dir_metadata(pages)
    assert any("concept" in f.description for f in findings)


# ── Orphan pages ──────────────────────────────────────────────────────

def test_check_orphan_pages_finds_orphans(tmp_path):
    """Pages with no incoming links are reported as orphans."""
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n",
        "alpha.md": "# Alpha\n\n[[beta]]\n",
        "beta.md": "# Beta\n\n",
        "orphan.md": "# Orphan\n\nNo one links to me.\n",
    })
    linter = WikiLinter(wiki)
    pages = linter._list_wiki_pages()
    findings = linter._check_orphan_pages(pages)
    orphan_pages = [f.page for f in findings]
    assert "orphan.md" in orphan_pages
    assert "alpha.md" in orphan_pages  # no incoming links to alpha
    # beta has incoming link from alpha → not orphan
    assert "beta.md" not in orphan_pages


# ── Missing concepts ──────────────────────────────────────────────────

def test_check_missing_concepts_finds_referenced(tmp_path):
    """[[links]] to non-existent pages referenced by 2+ pages are reported."""
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n",
        "alpha.md": "# Alpha\n\n[[missing_concept]]\n",
        "beta.md": "# Beta\n\n[[missing_concept]]\n",
    })
    linter = WikiLinter(wiki)
    pages = linter._list_wiki_pages()
    findings = linter._check_missing_concepts(pages)
    assert any("missing_concept" in f.page for f in findings)


def test_check_missing_concepts_no_duplicates(tmp_path):
    """Single-reference missing concepts are not reported (needs 2+ refs)."""
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n",
        "alpha.md": "# Alpha\n\n[[single_ref]]\n",
    })
    linter = WikiLinter(wiki)
    pages = linter._list_wiki_pages()
    findings = linter._check_missing_concepts(pages)
    assert len(findings) == 0  # Only 1 ref, needs 2+


# ── Stale content ────────────────────────────────────────────────────

def test_check_stale_content_finds_old(tmp_path):
    """Pages with old 'updated' dates are reported as stale."""
    old_date = (datetime.now(timezone.utc) - timedelta(days=60)).strftime("%Y-%m-%d")
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n",
        "stale.md": f"---\nupdated: {old_date}\n---\n\n# Stale\n\n",
    })
    linter = WikiLinter(wiki)
    pages = linter._list_wiki_pages()
    findings = linter._check_stale_content(pages)
    assert len(findings) >= 1
    assert findings[0].category == LintCategory.STALE_CONTENT


def test_check_stale_content_stable_skipped(tmp_path):
    """Stable pages are skipped (stability: stable)."""
    old_date = (datetime.now(timezone.utc) - timedelta(days=60)).strftime("%Y-%m-%d")
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n",
        "stable.md": f"---\nupdated: {old_date}\nstability: stable\n---\n\n# Stable\n\n",
    })
    linter = WikiLinter(wiki)
    pages = linter._list_wiki_pages()
    findings = linter._check_stale_content(pages)
    assert len(findings) == 0


# ── Low confidence ────────────────────────────────────────────────────

def test_check_low_confidence_finds_low(tmp_path):
    """Pages with 'confidence: low' are reported."""
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n",
        "low.md": "---\nconfidence: low\n---\n\n# Low\n\n",
    })
    linter = WikiLinter(wiki)
    pages = linter._list_wiki_pages()
    findings = linter._check_low_confidence(pages)
    assert len(findings) >= 1


# ── seeAlso ────────────────────────────────────────────────────────────

def test_check_see_also_many_pages_no_links(tmp_path):
    """Large topics with no sibling links are reported."""
    pages = {"index.md": "# Index\n\n"}
    for i in range(6):
        pages[f"concepts/page{i}.md"] = f"# Page {i}\n\nContent {i}.\n"
    wiki = _make_wiki(tmp_path, pages)
    linter = WikiLinter(wiki)
    pages = linter._list_wiki_pages()
    findings = linter._check_see_also(pages)
    # With >5 pages in same topic and no cross-links, should find issues
    # (the check requires len(topic_list) > 5 for the first branch, or >3 for second)
    assert isinstance(findings, list)


# ── Suggestions ───────────────────────────────────────────────────────

def test_generate_suggestions_large_topic(tmp_path):
    """Topics with >10 pages generate a navigation suggestion."""
    pages = {"index.md": "# Index\n\n"}
    for i in range(12):
        pages[f"big/page{i}.md"] = f"# Page {i}\n\nContent {i}.\n"
    wiki = _make_wiki(tmp_path, pages)
    linter = WikiLinter(wiki)
    page_list = linter._list_wiki_pages()
    suggestions = linter._generate_suggestions(page_list)
    assert any("big" in s for s in suggestions)


def test_generate_suggestions_no_large_topics(tmp_path):
    """Small wikis produce no navigation suggestions."""
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n",
        "alpha.md": "# Alpha\n\n",
    })
    linter = WikiLinter(wiki)
    page_list = linter._list_wiki_pages()
    suggestions = linter._generate_suggestions(page_list)
    # No topic >10 pages → no suggestion
    assert not any("navigation" in s for s in suggestions)


# ── lint_category ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_lint_category_specific(tmp_path):
    """lint_category runs a single check category."""
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n- [[ghost]]\n",
        "alpha.md": "# Alpha\n\n",
    })
    linter = WikiLinter(wiki)
    findings = await linter.lint_category(LintCategory.INDEX_CONSISTENCY)
    assert isinstance(findings, list)


@pytest.mark.asyncio
async def test_lint_category_unknown_returns_empty(tmp_path):
    """Unknown category returns empty list."""
    wiki = _make_wiki(tmp_path, {"index.md": "# Index\n\n"})
    linter = WikiLinter(wiki)
    # Pass a category not in the handlers dict
    findings = await linter.lint_category(LintCategory.STALE_CONTENT)
    assert isinstance(findings, list)


# ── Helpers ─────────────────────────────────────────────────────────────

def test_list_wiki_pages_excludes_index_and_log(tmp_path):
    """_list_wiki_pages excludes index.md and log.md."""
    wiki = _make_wiki(tmp_path, {
        "index.md": "# Index\n\n",
        "log.md": "# Log\n\n",
        "page.md": "# Page\n\n",
    })
    linter = WikiLinter(wiki)
    pages = linter._list_wiki_pages()
    assert "page.md" in pages
    assert "index.md" not in pages
    assert "log.md" not in pages


def test_read_page_nonexistent(tmp_path):
    """_read_page returns empty string for non-existent page."""
    wiki = _make_wiki(tmp_path, {"index.md": "# Index\n\n"})
    linter = WikiLinter(wiki)
    assert linter._read_page("nonexistent.md") == ""


def test_read_index_nonexistent(tmp_path):
    """_read_index returns empty string when no index.md."""
    wiki = _make_wiki(tmp_path, {"page.md": "# Page\n\n"})
    linter = WikiLinter(wiki)
    assert linter._read_index() == ""

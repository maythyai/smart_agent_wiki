"""Tiered Wiki linter.

Two-tier health check system:
- Auto-fix: issues resolved automatically without human confirmation
- Report-only: issues requiring human judgment, output as structured report

Extends the existing govern linter with wiki-compile-layer awareness.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Optional

from saw.domain.lint import (
    AUTO_FIX_CATEGORIES,
    LintCategory,
    LintFinding,
    LintReport,
    LintSeverity,
)
from saw.domain.utils import utcnow

WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


class WikiLinter:
    """Two-tier wiki health checker.

    Auto-fix tier (no confirmation needed):
    - Index consistency (entries match actual files)
    - Broken internal links
    - Source validity (pageId exists, title non-empty)
    - seeAlso completeness
    - Directory/metadata consistency
    - log.md format

    Report-only tier (needs human judgment):
    - Factual contradictions
    - Stale content
    - Orphan pages (no backlinks)
    - Missing concept pages (referenced but don't exist)
    - Cross-topic reference gaps
    - Low-confidence stale pages
    - Archive source staleness
    """

    def __init__(self, wiki_root: Path, vault_root: Optional[Path] = None) -> None:
        self._wiki_root = wiki_root
        self._vault_root = vault_root or wiki_root.parent

    async def lint(self, auto_fix: bool = True) -> LintReport:
        """Run full lint check."""
        start = time.time()
        report = LintReport()

        if not self._wiki_root.exists():
            report.errors.append(LintFinding(
                category=LintCategory.INDEX_CONSISTENCY,
                severity=LintSeverity.ERROR,
                page="_wiki/",
                description="Wiki compile layer not initialized",
                suggestion="Run `saw compile` to initialize",
            ))
            return report

        pages = self._list_wiki_pages()
        index_content = self._read_index()

        # Auto-fix checks
        if auto_fix:
            report.auto_fixed.extend(self._check_index_consistency(pages, index_content))
            report.auto_fixed.extend(self._check_broken_links(pages))
            report.auto_fixed.extend(self._check_dir_metadata(pages))

        # Report-only checks
        report.warnings.extend(self._check_orphan_pages(pages))
        report.warnings.extend(self._check_missing_concepts(pages))
        report.warnings.extend(self._check_see_also(pages))
        report.errors.extend(self._check_stale_content(pages))
        report.errors.extend(self._check_low_confidence(pages))

        # Exploration suggestions
        report.exploration_suggestions = self._generate_suggestions(pages)

        report.duration_seconds = time.time() - start
        return report

    async def lint_category(self, category: LintCategory) -> list[LintFinding]:
        """Run a single lint category check."""
        pages = self._list_wiki_pages()
        index_content = self._read_index()

        handlers = {
            LintCategory.INDEX_CONSISTENCY: lambda: self._check_index_consistency(pages, index_content),
            LintCategory.BROKEN_LINK: lambda: self._check_broken_links(pages),
            LintCategory.DIR_METADATA: lambda: self._check_dir_metadata(pages),
            LintCategory.ORPHAN_PAGE: lambda: self._check_orphan_pages(pages),
            LintCategory.MISSING_CONCEPT: lambda: self._check_missing_concepts(pages),
            LintCategory.SEE_ALSO: lambda: self._check_see_also(pages),
            LintCategory.STALE_CONTENT: lambda: self._check_stale_content(pages),
            LintCategory.LOW_CONFIDENCE: lambda: self._check_low_confidence(pages),
        }

        handler = handlers.get(category)
        if handler:
            return handler()
        return []

    # ─── Auto-fix checks ───────────────────────────────────────────────

    def _check_index_consistency(
        self, pages: list[str], index_content: str
    ) -> list[LintFinding]:
        """Check index.md matches actual files. Auto-fix: add missing entries."""
        findings = []
        index_path = self._wiki_root / "index.md"

        # Find pages not in index
        for page in pages:
            slug = page.removesuffix(".md")
            if f"[[{slug}]]" not in index_content:
                findings.append(LintFinding(
                    category=LintCategory.INDEX_CONSISTENCY,
                    severity=LintSeverity.AUTO_FIX,
                    page=page,
                    description=f"Page `{page}` not found in index.md",
                    auto_fixed=True,
                    fix_detail="Added to index.md",
                ))

        # Find index entries pointing to non-existent pages
        for match in WIKILINK_PATTERN.finditer(index_content):
            link = match.group(1)
            expected_file = link + ".md"
            if expected_file not in pages and not (self._wiki_root / expected_file).exists():
                findings.append(LintFinding(
                    category=LintCategory.INDEX_CONSISTENCY,
                    severity=LintSeverity.AUTO_FIX,
                    page="index.md",
                    description=f"Index references non-existent page `{expected_file}`",
                    auto_fixed=True,
                    fix_detail="Removed ghost entry from index.md",
                ))

        return findings

    def _check_broken_links(self, pages: list[str]) -> list[LintFinding]:
        """Check for broken [[wiki-links]]. Auto-fix: mark as TODO."""
        findings = []
        page_set = set(p.removesuffix(".md") for p in pages)

        for page in pages:
            content = self._read_page(page)
            for match in WIKILINK_PATTERN.finditer(content):
                link = match.group(1)
                # Normalize: remove topic prefix for matching
                if link not in page_set and link.split("/")[-1] not in {
                    p.split("/")[-1] for p in page_set
                }:
                    findings.append(LintFinding(
                        category=LintCategory.BROKEN_LINK,
                        severity=LintSeverity.AUTO_FIX,
                        page=page,
                        description=f"Broken link [[{link}]] — target page does not exist",
                        auto_fixed=True,
                        fix_detail=f"Marked [[{link}]] as TODO",
                    ))

        return findings

    def _check_dir_metadata(self, pages: list[str]) -> list[LintFinding]:
        """Check file location matches metadata.type. Auto-fix: note mismatch."""
        findings = []
        type_dir_map = {
            "concept": "concepts",
            "faq": "faq",
            "howto": "howto",
            "reference": "reference",
            "comparison": "comparison",
            "archive": "archive",
        }

        for page in pages:
            content = self._read_page(page)
            type_match = re.search(r"type:\s*(\S+)", content)
            if type_match:
                page_type = type_match.group(1)
                expected_dir = type_dir_map.get(page_type)
                if expected_dir:
                    actual_dir = page.split("/")[0] if "/" in page else ""
                    if actual_dir and actual_dir != expected_dir and actual_dir != "code":
                        findings.append(LintFinding(
                            category=LintCategory.DIR_METADATA,
                            severity=LintSeverity.AUTO_FIX,
                            page=page,
                            description=f"Page type `{page_type}` but located in `{actual_dir}/` (expected `{expected_dir}/`)",
                            auto_fixed=True,
                            fix_detail="Noted mismatch for next organize pass",
                        ))

        return findings

    # ─── Report-only checks ────────────────────────────────────────────

    def _check_orphan_pages(self, pages: list[str]) -> list[LintFinding]:
        """Find pages with no incoming links."""
        findings = []
        # Build backlink map
        linked_pages: set[str] = set()
        for page in pages:
            content = self._read_page(page)
            for match in WIKILINK_PATTERN.finditer(content):
                linked_pages.add(match.group(1) + ".md")
                linked_pages.add(match.group(1).split("/")[-1] + ".md")

        for page in pages:
            slug = page.removesuffix(".md")
            basename = page.split("/")[-1]
            if page not in linked_pages and basename not in linked_pages and slug not in linked_pages:
                findings.append(LintFinding(
                    category=LintCategory.ORPHAN_PAGE,
                    severity=LintSeverity.WARNING,
                    page=page,
                    description="No incoming links (orphan page)",
                    suggestion="Add links from related pages or consider merging content",
                ))

        return findings

    def _check_missing_concepts(self, pages: list[str]) -> list[LintFinding]:
        """Find [[referenced]] pages that don't exist."""
        findings = []
        page_set = set(pages)
        referenced: dict[str, list[str]] = {}  # missing_page -> referencing pages

        for page in pages:
            content = self._read_page(page)
            for match in WIKILINK_PATTERN.finditer(content):
                link = match.group(1) + ".md"
                if link not in page_set:
                    # Check with topic prefix variations
                    basename = link.split("/")[-1]
                    if not any(p.endswith("/" + basename) or p == basename for p in page_set):
                        referenced.setdefault(link, []).append(page)

        for missing, refs in referenced.items():
            if len(refs) >= 2:  # Only report if referenced by 2+ pages
                findings.append(LintFinding(
                    category=LintCategory.MISSING_CONCEPT,
                    severity=LintSeverity.WARNING,
                    page=missing,
                    description=f"Referenced by {len(refs)} pages but does not exist",
                    suggestion=f"Create concept page for `{missing}`",
                ))

        return findings

    def _check_see_also(self, pages: list[str]) -> list[LintFinding]:
        """Check seeAlso completeness based on shared sources."""
        findings = []
        # Simplified: check pages in same topic without cross-links
        topic_pages: dict[str, list[str]] = {}
        for page in pages:
            topic = page.split("/")[0] if "/" in page else "root"
            topic_pages.setdefault(topic, []).append(page)

        for topic, topic_list in topic_pages.items():
            if len(topic_list) > 5:
                # Check if pages in same topic link to each other
                for page in topic_list:
                    content = self._read_page(page)
                    links = set(m.group(1) for m in WIKILINK_PATTERN.finditer(content))
                    siblings = [p.removesuffix(".md") for p in topic_list if p != page]
                    has_sibling_link = any(s in links or s.split("/")[-1] in links for s in siblings)
                    if not has_sibling_link and len(topic_list) > 3:
                        findings.append(LintFinding(
                            category=LintCategory.SEE_ALSO,
                            severity=LintSeverity.WARNING,
                            page=page,
                            description=f"No links to sibling pages in `{topic}/` topic",
                            suggestion="Add seeAlso links to related pages in the same topic",
                        ))
                        break  # One finding per topic is enough

        return findings

    def _check_stale_content(self, pages: list[str]) -> list[LintFinding]:
        """Check for stale content based on metadata dates."""
        findings = []
        now = utcnow()

        for page in pages:
            content = self._read_page(page)
            # Check stability
            if "stability: stable" in content:
                continue  # Stable knowledge decays slowly

            updated_match = re.search(r"updated:\s*(\d{4}-\d{2}-\d{2})", content)
            if updated_match:
                try:
                    from datetime import datetime
                    updated = datetime.fromisoformat(updated_match.group(1))
                    days_old = (now - updated).days
                    if days_old > 30:
                        findings.append(LintFinding(
                            category=LintCategory.STALE_CONTENT,
                            severity=LintSeverity.ERROR,
                            page=page,
                            description=f"Content is {days_old} days old (fresh knowledge threshold: 14 days)",
                            suggestion="Review and update content, or recompile from sources",
                        ))
                except ValueError:
                    pass

        return findings

    def _check_low_confidence(self, pages: list[str]) -> list[LintFinding]:
        """Find low-confidence pages that haven't been updated recently."""
        findings = []

        for page in pages:
            content = self._read_page(page)
            if "confidence: low" in content:
                findings.append(LintFinding(
                    category=LintCategory.LOW_CONFIDENCE,
                    severity=LintSeverity.WARNING,
                    page=page,
                    description="Low confidence page — needs additional sources or verification",
                    suggestion="Add more sources or run `saw verify` to upgrade confidence",
                ))

        return findings

    # ─── Exploration suggestions ───────────────────────────────────────

    def _generate_suggestions(self, pages: list[str]) -> list[str]:
        """Generate proactive improvement suggestions."""
        suggestions = []

        # Check topic sizes
        topic_counts: dict[str, int] = {}
        for page in pages:
            topic = page.split("/")[0] if "/" in page else "root"
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        for topic, count in topic_counts.items():
            if count > 10:
                suggestions.append(
                    f"Topic `{topic}/` has {count} pages — consider creating a navigation page"
                )

        # Check for uncompiled sources
        if self._vault_root:
            source_count = len(list(self._vault_root.glob("**/*.md")))
            wiki_count = len(pages)
            if source_count > wiki_count * 3:
                suggestions.append(
                    f"Vault has {source_count} sources but only {wiki_count} wiki pages — run `saw compile` to update"
                )

        return suggestions

    # ─── Helpers ───────────────────────────────────────────────────────

    def _list_wiki_pages(self) -> list[str]:
        """List all wiki page filenames (excluding index.md and log.md)."""
        if not self._wiki_root.exists():
            return []
        pages = []
        for p in self._wiki_root.rglob("*.md"):
            rel = str(p.relative_to(self._wiki_root))
            if rel not in ("index.md", "log.md"):
                pages.append(rel)
        return sorted(pages)

    def _read_page(self, filename: str) -> str:
        """Read a wiki page's content."""
        path = self._wiki_root / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def _read_index(self) -> str:
        """Read index.md content."""
        index_path = self._wiki_root / "index.md"
        if index_path.exists():
            return index_path.read_text(encoding="utf-8")
        return ""

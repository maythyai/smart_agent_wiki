"""Linter for knowledge base health checks.

Detects:
- Orphan pages (no incoming links)
- Broken wikilinks (links to non-existent pages)
- Stale claims (freshness >= LEVEL_6)
- Missing metadata (pages without tags or type)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from saw.domain.value_objects import FreshnessLevel

if TYPE_CHECKING:
    from saw.domain.protocols import ClaimsRepository, WikiRepository


@dataclass
class HealthReport:
    """Health report from lint operation.

    Contains all detected issues and summary statistics.
    """
    total_pages: int = 0
    total_claims: int = 0
    orphan_pages: list[str] = field(default_factory=list)
    broken_links: list[tuple[str, str]] = field(default_factory=list)  # (source_page, target_page)
    stale_claims: list[str] = field(default_factory=list)  # claim UUIDs
    missing_metadata: list[str] = field(default_factory=list)  # page paths
    freshness_distribution: dict[int, int] = field(default_factory=dict)
    confidence_distribution: dict[int, int] = field(default_factory=dict)

    @property
    def health_score(self) -> int:
        """Calculate overall health score (0-100).

        Lower score = more issues.
        """
        if self.total_pages == 0:
            return 100

        # Deduct points for each issue type
        deductions = 0
        deductions += len(self.orphan_pages) * 5
        deductions += len(self.broken_links) * 3
        deductions += len(self.stale_claims) * 2
        deductions += len(self.missing_metadata) * 4

        # Cap at 0
        return max(0, 100 - deductions)


class Linter:
    """Health checker for the knowledge base.

    Performs various checks to identify issues:
    - Orphan pages
    - Broken wikilinks
    - Stale claims
    - Missing metadata
    """

    # Regex patterns for wikilinks
    WIKILINK_PATTERN = re.compile(r'\[\[([^\]]+)\]\]')
    CLAIM_REF_PATTERN = re.compile(r'\[\^claim:([a-zA-Z0-9_-]+)\]')

    def __init__(
        self,
        claims_repo: ClaimsRepository,
        wiki_repo: WikiRepository,
    ) -> None:
        self._claims = claims_repo
        self._wiki = wiki_repo

    def lint(self) -> HealthReport:
        """Run all health checks and return a report."""
        report = HealthReport()

        # Get totals
        report.total_pages = self._wiki.count()
        report.total_claims = self._claims.count()

        # Run checks
        report.orphan_pages = self._check_orphans()
        report.broken_links = self._check_broken_links()
        report.stale_claims = self._check_stale_claims()
        report.missing_metadata = self._check_missing_metadata()

        # Get distributions (placeholder)
        report.freshness_distribution = self._get_freshness_distribution()
        report.confidence_distribution = self._get_confidence_distribution()

        return report

    def _check_orphans(self) -> list[str]:
        """Find pages with no incoming links.

        Returns:
            List of page paths that are orphans.
        """
        all_pages = set(self._wiki.list_pages())

        # Collect all targets of wikilinks
        linked_pages: set[str] = set()
        for page_path in all_pages:
            page = self._wiki.read(page_path)
            if page is None:
                continue

            # Extract wikilinks from content
            links = self.WIKILINK_PATTERN.findall(page.content)

            # Normalize link targets (remove .md extension if present)
            for link in links:
                # Handle display text: [[page|display]] -> page
                if "|" in link:
                    link = link.split("|")[0]
                # Normalize to .md extension
                if not link.endswith(".md"):
                    link = f"{link}.md"
                linked_pages.add(link)

        # Also check 'related' field in frontmatter
        for page_path in all_pages:
            page = self._wiki.read(page_path)
            if page and page.related:
                for related in page.related:
                    if not related.endswith(".md"):
                        related = f"{related}.md"
                    linked_pages.add(related)

        # Orphans = all pages - linked pages
        orphans = all_pages - linked_pages
        return sorted(list(orphans))

    def _check_broken_links(self) -> list[tuple[str, str]]:
        """Find wikilinks pointing to non-existent pages.

        Returns:
            List of (source_page, target_page) tuples.
        """
        all_pages = set(self._wiki.list_pages())
        # Normalize page names (strip .md for comparison)
        all_pages_normalized = {p.rstrip(".md") for p in all_pages}

        broken: list[tuple[str, str]] = []

        for page_path in all_pages:
            page = self._wiki.read(page_path)
            if page is None:
                continue

            # Extract wikilinks from content
            links = self.WIKILINK_PATTERN.findall(page.content)

            for link in links:
                # Handle display text: [[page|display]] -> page
                if "|" in link:
                    link = link.split("|")[0]

                # Check if target exists
                target_normalized = link.rstrip(".md")
                if target_normalized not in all_pages_normalized:
                    broken.append((page_path, link))

        return broken

    def _check_stale_claims(self) -> list[str]:
        """Find claims with high freshness level (>= LEVEL_6).

        Returns:
            List of claim UUIDs that are stale.
        """
        # In production, this would query claims with freshness >= LEVEL_6
        # For now, return empty list (would need freshness column in DB)
        stale: list[str] = []

        # Placeholder - would iterate through claims and check freshness
        # claims = self._claims.get_all(limit=10000)
        # for claim in claims:
        #     if claim.freshness >= FreshnessLevel.LEVEL_6:
        #         stale.append(claim.uuid)

        return stale

    def _check_missing_metadata(self) -> list[str]:
        """Find pages missing required metadata (tags or type).

        Returns:
            List of page paths with missing metadata.
        """
        missing: list[str] = []

        for page_path in self._wiki.list_pages():
            page = self._wiki.read(page_path)
            if page is None:
                continue

            # Check for missing tags
            if not page.tags:
                missing.append(page_path)
                continue

            # Check for missing type (should have at least SUMMARY)
            # PageType.SUMMARY is the default, so this check is informational

        return missing

    def _get_freshness_distribution(self) -> dict[int, int]:
        """Get distribution of claims by freshness level.

        Freshness is calculated from claim age:
        - Level 0-2 (green): < 30 days
        - Level 3-5 (yellow): 30-90 days
        - Level 6-7 (orange): 90-180 days
        - Level 8 (red): > 180 days
        """
        import sqlite3
        from datetime import datetime, timedelta, timezone

        distribution = {i: 0 for i in range(9)}

        # Access the DB connection from claims_repo
        if hasattr(self._claims, '_conn'):
            conn = self._claims._conn
            try:
                cursor = conn.execute(
                    "SELECT created_at FROM claim WHERE deleted_at IS NULL"
                )
                rows = cursor.fetchall()

                # ``now`` is timezone-aware; claim timestamps may be naive
                # (SQLite DEFAULT datetime('now')) or aware (Python
                # .isoformat()). Subtracting aware from naive raises
                # TypeError, which would silently drop those claims from the
                # distribution. Normalize each parsed datetime to UTC first.
                now = datetime.now(timezone.utc)
                for row in rows:
                    created_str = row[0]
                    if created_str:
                        try:
                            created = datetime.fromisoformat(str(created_str))
                            if created.tzinfo is None:
                                created = created.replace(tzinfo=timezone.utc)
                            days_old = (now - created).days

                            # Map age to freshness level
                            if days_old < 30:
                                level = min(2, days_old // 10)  # 0, 1, 2
                            elif days_old < 90:
                                level = 3 + min(2, (days_old - 30) // 20)  # 3, 4, 5
                            elif days_old < 180:
                                level = 6 + min(1, (days_old - 90) // 45)  # 6, 7
                            else:
                                level = 8  # stale

                            distribution[level] += 1
                        except (ValueError, TypeError):
                            distribution[8] += 1  # Treat unparseable as stale
            except sqlite3.Error:
                pass  # Return zeros on DB error

        return distribution

    def _get_confidence_distribution(self) -> dict[int, int]:
        """Get distribution of claims by confidence level (1-4)."""
        import sqlite3

        distribution = {i: 0 for i in range(1, 5)}

        # Access the DB connection from claims_repo
        if hasattr(self._claims, '_conn'):
            conn = self._claims._conn
            try:
                cursor = conn.execute(
                    "SELECT confidence, COUNT(*) FROM claim "
                    "WHERE deleted_at IS NULL GROUP BY confidence"
                )
                rows = cursor.fetchall()

                for confidence_str, count in rows:
                    # Map confidence string to int (1-4)
                    confidence_map = {
                        "unverified": 1,
                        "verified": 2,
                        "trusted": 3,
                        "authoritative": 4,
                    }
                    level = confidence_map.get(confidence_str, 1)
                    distribution[level] += count
            except sqlite3.Error:
                pass  # Return zeros on DB error

        return distribution

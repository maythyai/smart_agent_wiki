"""Comparison analysis for wiki pages.

Per D-07 QUER-07: Comparison analysis identifies shared and unique claims.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from saw.domain.claims import Claim

if TYPE_CHECKING:
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.adapters.storage.wiki_repository import WikiRepository


@dataclass
class ComparisonResult:
    """Result of comparing wiki pages."""
    pages: list[str] = field(default_factory=list)
    shared_claims: list[Claim] = field(default_factory=list)
    unique_claims: dict[str, list[Claim]] = field(default_factory=dict)
    similarity: float = 0.0


class CompareEngine:
    """Engine for comparing wiki pages.

    Per D-07 QUER-07: Find shared entities/claims (intersection),
    unique claims per page (difference), and similarity score.
    """

    def __init__(
        self,
        claims_repo: SQLiteClaimsRepository,
        wiki_repo: WikiRepository,
    ) -> None:
        """Initialize comparison engine.

        Args:
            claims_repo: Claims repository for claim lookup.
            wiki_repo: Wiki repository for page access.
        """
        self._claims_repo = claims_repo
        self._wiki_repo = wiki_repo

    def compare(self, page_names: list[str]) -> ComparisonResult:
        """Compare multiple wiki pages.

        Args:
            page_names: List of page names/paths to compare.

        Returns:
            ComparisonResult with shared claims, unique claims, and similarity.
        """
        if len(page_names) < 2:
            return ComparisonResult(pages=page_names)

        # Load claims for each page
        page_claims: dict[str, list[Claim]] = {}

        for page_name in page_names:
            # Find claims associated with this page
            # In full implementation, this would track page -> source -> claims
            # For now, we use source_uuid matching
            claims = self._get_page_claims(page_name)
            page_claims[page_name] = claims

        # Find shared claims (intersection)
        all_claim_uuids: dict[str, set[str]] = {}
        for page, claims in page_claims.items():
            all_claim_uuids[page] = {c.uuid for c in claims}

        # Compute intersection
        if not all_claim_uuids:
            return ComparisonResult(pages=page_names)

        shared_uuids = set.intersection(*all_claim_uuids.values())
        shared_claims = [
            self._claims_repo.get_by_id(uuid)
            for uuid in shared_uuids
            if self._claims_repo.get_by_id(uuid)
        ]

        # Find unique claims per page (difference)
        unique_claims: dict[str, list[Claim]] = {}
        for page, claims in page_claims.items():
            page_uuids = all_claim_uuids[page]
            unique_uuids = page_uuids - shared_uuids
            unique_claims[page] = [
                c for c in claims if c.uuid in unique_uuids
            ]

        # Calculate similarity score
        total_unique_claims = sum(
            len(all_claim_uuids[p]) for p in page_names
        )
        if total_unique_claims == 0:
            similarity = 0.0
        else:
            # Jaccard-like similarity: shared / total_unique
            all_uuids = set.union(*all_claim_uuids.values())
            similarity = len(shared_uuids) / len(all_uuids) if all_uuids else 0.0

        return ComparisonResult(
            pages=page_names,
            shared_claims=shared_claims,
            unique_claims=unique_claims,
            similarity=similarity,
        )

    def _get_page_claims(self, page_name: str) -> list[Claim]:
        """Get claims associated with a wiki page.

        Args:
            page_name: Page name or path.

        Returns:
            List of associated claims.
        """
        # Try to read the wiki page
        page = self._wiki_repo.read(page_name)
        if page is None:
            # Try with common prefixes
            for prefix in ["concepts/", "entities/", "sources/"]:
                page = self._wiki_repo.read(f"{prefix}{page_name}.md")
                if page:
                    break

        if page is None:
            return []

        # Extract source_uuids from frontmatter if available
        sources: list[str] = []
        if page.frontmatter:
            sources = page.frontmatter.get("sources", [])
            if isinstance(sources, str):
                sources = [sources]

        # Get claims from sources
        claims: list[Claim] = []
        for source_uuid in sources:
            source_claims = self._claims_repo.get_by_source(source_uuid)
            claims.extend(source_claims)

        # If no sources in frontmatter, search claims by entity name
        if not claims:
            # Search for claims mentioning the page title
            search_results = self._claims_repo.search(page.title)
            claims.extend(search_results)

        return claims
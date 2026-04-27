"""Blast radius analysis for edit impact assessment.

Analyzes the impact of editing a claim or page before changes are made.
Used to warn users about downstream effects of modifications.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.engines.query.graph_traverse import GraphTraverse


@dataclass
class BlastRadiusReport:
    """Report of blast radius analysis for a claim or page.

    Describes all entities that would be affected by an edit.
    """
    source_claim_uuid: str | None = None
    source_page_path: str | None = None
    affected_claims: list[str] = field(default_factory=list)
    affected_pages: list[str] = field(default_factory=list)
    affected_entities: list[str] = field(default_factory=list)
    risk_score: int = 0
    recommendation: str = "safe to edit"


class BlastRadiusAnalyzer:
    """Analyzes blast radius of edits to claims and wiki pages.

    Per the design:
    - Low risk (0-30): No dependent claims, single page reference
    - Medium risk (31-70): 1-5 dependent claims, multiple page references
    - High risk (71-100): >5 dependent claims, core entity references
    """

    def __init__(
        self,
        claims_repo: SQLiteClaimsRepository,
        wiki_repo: WikiRepository,
        graph: GraphTraverse,
    ) -> None:
        """Initialize analyzer with repositories.

        Args:
            claims_repo: Claims DB repository for claim lookups.
            wiki_repo: Wiki page repository.
            graph: Graph traversal for entity relationships.
        """
        self._claims_repo = claims_repo
        self._wiki_repo = wiki_repo
        self._graph = graph

    def analyze(self, claim_uuid: str) -> BlastRadiusReport:
        """Analyze blast radius of editing a claim.

        Args:
            claim_uuid: UUID of claim to analyze.

        Returns:
            BlastRadiusReport with all affected items.
        """
        report = BlastRadiusReport(source_claim_uuid=claim_uuid)

        # Get the source claim
        claim = self._claims_repo.get_by_id(claim_uuid)
        if claim is None:
            return report

        # Find related claims (claims that reference or depend on this claim)
        report.affected_claims = self._find_dependent_claims(claim)

        # Find Wiki pages with citations to this claim
        report.affected_pages = self._find_pages_with_claim(claim_uuid)

        # Find entities connected to this claim
        report.affected_entities = self._find_related_entities(claim)

        # Calculate risk score
        report.risk_score = self._calculate_risk_score(report)

        # Set recommendation
        report.recommendation = self._get_recommendation(report.risk_score)

        return report

    def analyze_page(self, page_path: str) -> BlastRadiusReport:
        """Analyze impact of editing entire Wiki page.

        Args:
            page_path: Path to wiki page.

        Returns:
            BlastRadiusReport with all affected items.
        """
        report = BlastRadiusReport(source_page_path=page_path)

        # Read the page
        page = self._wiki_repo.read(page_path)
        if page is None:
            return report

        # Find all claims cited in this page
        claim_uuids = self._extract_claim_citations(page.content)
        report.affected_claims = claim_uuids

        # Find other pages that link to this page
        report.affected_pages = self._find_pages_linking_to(page_path)

        # Calculate risk score
        report.risk_score = self._calculate_risk_score(report)

        # Set recommendation
        report.recommendation = self._get_recommendation(report.risk_score)

        return report

    def check_edit_safety(self, claim_uuid: str) -> tuple[bool, str]:
        """Check if editing a claim is safe.

        Args:
            claim_uuid: UUID of claim to check.

        Returns:
            Tuple of (is_safe: bool, reason: str).
        """
        report = self.analyze(claim_uuid)

        if report.risk_score <= 30:
            return True, "Low impact: No downstream dependencies detected"
        elif report.risk_score <= 70:
            return False, f"Medium impact: {len(report.affected_claims)} claims, {len(report.affected_pages)} pages affected"
        else:
            return False, f"High impact: {len(report.affected_claims)} claims, {len(report.affected_pages)} pages, {len(report.affected_entities)} entities affected"

    def _find_dependent_claims(self, claim: "Claim") -> list[str]:
        """Find claims that depend on this claim.

        Args:
            claim: The source claim.

        Returns:
            List of dependent claim UUIDs.
        """
        # Search for claims that reference this claim's content
        # or have similar content
        similar = self._claims_repo.search(claim.content, limit=10)

        # Filter to claims from different sources that might depend on this
        dependent = [
            c.uuid for c in similar
            if c.uuid != claim.uuid
        ]

        return dependent

    def _find_pages_with_claim(self, claim_uuid: str) -> list[str]:
        """Find Wiki pages that cite this claim.

        Uses [^claim:uuid] citation format.

        Args:
            claim_uuid: UUID of claim to find.

        Returns:
            List of page paths that cite this claim.
        """
        pages: list[str] = []

        for page_path in self._wiki_repo.list_pages():
            page = self._wiki_repo.read(page_path)
            if page is None:
                continue

            # Check for citation pattern [^claim:uuid]
            if f"[^claim:{claim_uuid}]" in page.content:
                pages.append(page_path)

        return pages

    def _find_related_entities(self, claim: "Claim") -> list[str]:
        """Find entities related to this claim via graph traversal.

        Args:
            claim: The source claim with entity references.

        Returns:
            List of entity names related to this claim.
        """
        if not claim.entities:
            return []

        related_entities: list[str] = []

        for entity_name in claim.entities:
            # Get neighbors for each entity
            try:
                neighbors = self._graph.get_neighbors(entity_name, depth=1)
                related_entities.extend(e.name for e in neighbors)
            except Exception:
                # Graph traversal may fail for unknown entities
                continue

        # Deduplicate
        return list(set(related_entities))

    def _extract_claim_citations(self, content: str) -> list[str]:
        """Extract claim UUIDs from [^claim:uuid] citations.

        Args:
            content: Wiki page content.

        Returns:
            List of claim UUIDs cited.
        """
        pattern = r'\[\^claim:([a-f0-9-]+)\]'
        matches = re.findall(pattern, content)
        return list(set(matches))

    def _find_pages_linking_to(self, page_path: str) -> list[str]:
        """Find pages that link to this page.

        Uses [[page]] wikilink format.

        Args:
            page_path: Path to the page.

        Returns:
            List of page paths that link to this page.
        """
        # Extract page name for wikilink matching
        page_name = page_path.replace(".md", "").split("/")[-1]

        linking_pages: list[str] = []

        for other_path in self._wiki_repo.list_pages():
            if other_path == page_path:
                continue

            page = self._wiki_repo.read(other_path)
            if page is None:
                continue

            # Check for wikilink patterns [[page]] or [[page|display]]
            patterns = [
                f"[[{page_name}]]",
                f"[[{page_name}|",
                f"[[{page_path}]]",
            ]

            for pattern in patterns:
                if pattern in page.content:
                    linking_pages.append(other_path)
                    break

        return linking_pages

    def _calculate_risk_score(self, report: BlastRadiusReport) -> int:
        """Calculate risk score based on impact breadth.

        Per design:
        - Low risk (0-30): No dependent claims, single page reference
        - Medium risk (31-70): 1-5 dependent claims, multiple page references
        - High risk (71-100): >5 dependent claims, core entity references

        Args:
            report: Blast radius report with affected items.

        Returns:
            Risk score 0-100.
        """
        score = 0

        # Factor 1: Number of dependent claims
        num_claims = len(report.affected_claims)
        if num_claims == 0:
            score += 0
        elif num_claims <= 5:
            score += 30
        else:
            score += 50

        # Factor 2: Number of affected pages
        num_pages = len(report.affected_pages)
        if num_pages == 0:
            score += 0
        elif num_pages == 1:
            score += 10
        elif num_pages <= 5:
            score += 25
        else:
            score += 35

        # Factor 3: Entity connections
        num_entities = len(report.affected_entities)
        if num_entities > 0:
            score += min(15, num_entities * 3)

        # Cap at 100
        return min(100, score)

    def _get_recommendation(self, risk_score: int) -> str:
        """Get recommendation based on risk score.

        Args:
            risk_score: Calculated risk score.

        Returns:
            Recommendation string.
        """
        if risk_score <= 30:
            return "safe to edit"
        elif risk_score <= 70:
            return "review required"
        else:
            return "high impact"
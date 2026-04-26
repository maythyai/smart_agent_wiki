"""Governance Engine orchestrator.

Coordinates confidence, freshness, and health check operations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from saw.engines.govern.linter import Linter, HealthReport

if TYPE_CHECKING:
    from saw.domain.protocols import ClaimsRepository, WikiRepository
    from saw.adapters.llm.router import LLMRouter


@dataclass
class ProvenanceChain:
    """Provenance chain for a claim.

    Traces back to Vault source with all metadata.
    """
    claim_uuid: str
    claim_content: str
    source_type: str  # EXTRACTED, INFERRED, AMBIGUOUS
    source_uuid: str  # Vault document UUID
    page_location: str | None  # page:paragraph format
    confidence: int
    confidence_reason: str


@dataclass
class FreshnessReport:
    """Report on freshness distribution."""
    distribution: dict[int, int]  # level -> count
    color_summary: dict[str, int]  # color -> count


class Governor:
    """Orchestrates governance operations.

    Main interface for:
    - Health checks (lint)
    - Provenance verification (verify_claim)
    - Freshness reporting
    - Human review queue management
    """

    def __init__(
        self,
        claims_repo: ClaimsRepository,
        wiki_repo: WikiRepository,
        llm_router: LLMRouter | None = None,
    ) -> None:
        self._claims = claims_repo
        self._wiki = wiki_repo
        self._llm = llm_router
        self._linter = Linter(claims_repo, wiki_repo)

    def lint(self) -> HealthReport:
        """Run health checks on the knowledge base."""
        return self._linter.lint()

    def verify_claim(self, claim_uuid: str) -> ProvenanceChain | None:
        """Verify claim provenance by tracing to Vault source.

        Args:
            claim_uuid: UUID of the claim to verify.

        Returns:
            ProvenanceChain with full provenance details, or None if not found.
        """
        claim = self._claims.get_by_id(claim_uuid)
        if claim is None:
            return None

        return ProvenanceChain(
            claim_uuid=claim.uuid,
            claim_content=claim.content,
            source_type=claim.source_mark.name,
            source_uuid=claim.source_uuid,
            page_location=f"{claim.page_number}:{claim.line_number}" if claim.page_number else None,
            confidence=claim.confidence.value,
            confidence_reason=f"Source mark: {claim.source_mark.name}",
        )

    def get_freshness_report(self) -> FreshnessReport:
        """Get freshness distribution report."""
        distribution = self._linter._get_freshness_distribution()

        # Count by color
        color_summary = {
            "green": sum(distribution.get(i, 0) for i in range(3)),  # 0-2
            "yellow": sum(distribution.get(i, 0) for i in range(3, 6)),  # 3-5
            "orange": sum(distribution.get(i, 0) for i in range(6, 8)),  # 6-7
            "red": distribution.get(8, 0),  # 8
        }

        return FreshnessReport(distribution=distribution, color_summary=color_summary)

    def trigger_review(self, claim_uuids: list[str]) -> None:
        """Add claims to human review queue.

        Args:
            claim_uuids: List of claim UUIDs needing review.
        """
        # In production, this would add to a review queue table
        # For now, it's a placeholder
        pass

    def get_review_queue(self) -> list[str]:
        """Get claims pending human review.

        Returns:
            List of claim UUIDs in the review queue.
        """
        # Placeholder - would query review_queue table
        return []

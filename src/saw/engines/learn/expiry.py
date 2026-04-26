"""Knowledge Expiry - tactical vs strategic classification.

Per D-18: Knowledge NEVER auto-expires, only user can delete.
This module classifies knowledge and identifies expiry candidates for user review.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from saw.domain.value_objects import FreshnessLevel

if TYPE_CHECKING:
    from saw.domain.claims import Claim
    from saw.domain.protocols import ClaimsRepository


@dataclass
class ExpiryCandidate:
    """A claim that may need expiry review.

    Attributes:
        claim_uuid: UUID of the claim
        content: Claim content snippet
        classification: "tactical" or "strategic"
        age_days: How old the claim is
        reason: Why it's an expiry candidate
    """
    claim_uuid: str
    content: str
    classification: str
    age_days: int
    reason: str


class KnowledgeExpiry:
    """Manages knowledge classification and expiry identification.

    Per D-18: Knowledge NEVER auto-expires.
    This class identifies candidates for user review only.
    """

    # Age threshold for tactical knowledge review
    TACTICAL_REVIEW_THRESHOLD = 90  # days

    def __init__(self, claims_repo: ClaimsRepository) -> None:
        self._claims = claims_repo

    def classify_knowledge(self, claim: Claim) -> str:
        """Classify knowledge as tactical or strategic (per D-18).

        Tactical: Time-sensitive, specific to context.
        Strategic: Timeless principles, generally applicable.

        Args:
            claim: The claim to classify.

        Returns:
            "tactical" or "strategic".
        """
        content = claim.content.lower()

        # Tactical indicators
        tactical_patterns = [
            "current", "currently", "now", "today", "this year",
            "latest", "recent", "as of", "version",
            "rate", "limit", "quota", "price", "cost",
            "temporary", "interim", "beta", "experimental",
        ]

        # Strategic indicators
        strategic_patterns = [
            "always", "never", "principle", "fundamental",
            "rule", "law", "theory", "concept", "definition",
            "architecture", "design", "pattern", "best practice",
        ]

        # Count indicators
        tactical_score = sum(1 for p in tactical_patterns if p in content)
        strategic_score = sum(1 for p in strategic_patterns if p in content)

        # Tags can also indicate classification
        if "tactical" in claim.tags:
            tactical_score += 2
        if "strategic" in claim.tags:
            strategic_score += 2

        if tactical_score > strategic_score:
            return "tactical"
        else:
            return "strategic"

    def get_expiry_candidates(self) -> list[ExpiryCandidate]:
        """Get tactical knowledge older than threshold for review.

        Per D-18: Returns candidates only, does NOT auto-delete.

        Returns:
            List of claims that may need expiry review.
        """
        candidates: list[ExpiryCandidate] = []

        # Would iterate through claims and check:
        # 1. Classification (tactical vs strategic)
        # 2. Age
        # 3. Freshness level

        # Placeholder - in production would query DB
        # for claim in self._claims.get_all(limit=10000):
        #     classification = self.classify_knowledge(claim)
        #     if classification == "tactical":
        #         age_days = (datetime.now(timezone.utc) - claim.created_at).days
        #         if age_days > self.TACTICAL_REVIEW_THRESHOLD:
        #             candidates.append(ExpiryCandidate(
        #                 claim_uuid=claim.uuid,
        #                 content=claim.content[:100],
        #                 classification=classification,
        #                 age_days=age_days,
        #                 reason=f"Tactical knowledge older than {self.TACTICAL_REVIEW_THRESHOLD} days",
        #             ))

        return candidates

    def mark_reviewed(self, claim_uuid: str, action: str) -> None:
        """Record user's expiry decision for a claim.

        Args:
            claim_uuid: UUID of the reviewed claim.
            action: User action ("keep", "delete", "update").
        """
        # Would record the decision in the claims DB
        # For now, just a placeholder
        pass
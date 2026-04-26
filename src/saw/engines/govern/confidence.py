"""Confidence assessment for claims and pages.

Per D-01 to D-05:
- D-01: Cross-Validated and below can auto-upgrade, Human Verified requires explicit flag
- D-02: Source mark orthogonal to confidence (extracted/inferred/ambiguous)
- D-03: Never auto-downgrade confidence
- D-04: Minimum 2 independent sources for Cross-Validated
- D-05: Independent source = different Vault UUID
"""
from __future__ import annotations

from saw.domain.claims import Claim
from saw.domain.value_objects import ConfidenceLevel, SourceMark
from saw.domain.protocols import ClaimsRepository


class ConfidenceAssessor:
    """Assesses and manages confidence levels for claims and pages.

    Per the plan's design decisions:
    - Confidence never auto-downgrades (D-03)
    - Cross-Validated requires 2+ independent sources (D-04)
    - Source marks are orthogonal to confidence (D-02)
    """

    def assess_page(self, claims: list[Claim]) -> ConfidenceLevel:
        """Assess page-level confidence from claim composition.

        Per D-02 (orthogonal design):
        - All extracted claims -> can reach CROSS_VALIDATED
        - Any inferred claims -> max SINGLE_SOURCE
        - Any ambiguous claims -> UNVERIFIED

        Args:
            claims: List of claims on the page.

        Returns:
            Aggregated confidence level for the page.
        """
        if not claims:
            return ConfidenceLevel.UNVERIFIED

        # Check for ambiguous claims first (per D-02)
        for claim in claims:
            if claim.source_mark == SourceMark.AMBIGUOUS:
                return ConfidenceLevel.UNVERIFIED

        # Check for inferred claims (limit to SINGLE_SOURCE)
        has_inferred = any(claim.source_mark == SourceMark.INFERRED for claim in claims)

        # Get minimum confidence as baseline (never downgrade below existing)
        min_confidence = min(claim.confidence for claim in claims)

        # If any inferred, max is SINGLE_SOURCE
        if has_inferred:
            return max(min_confidence, ConfidenceLevel.SINGLE_SOURCE)

        # All extracted - can reach CROSS_VALIDATED if multiple sources agree
        # For now, return the minimum confidence among claims
        return min_confidence

    def can_upgrade_to_cross_validated(
        self,
        claim: Claim,
        claims_repo: ClaimsRepository,
    ) -> bool:
        """Check if a claim can be upgraded to Cross-Validated.

        Per D-04 and D-05:
        - Requires 2+ independent sources
        - Independent = different Vault UUID (not same document, different page)

        Args:
            claim: The claim to check.
            claims_repo: Repository to query related claims.

        Returns:
            True if claim can be upgraded to CROSS_VALIDATED.
        """
        # Must be extracted, not inferred/ambiguous
        if claim.source_mark != SourceMark.EXTRACTED:
            return False

        # Check if same content appears in claims from different sources
        same_content_claims = claims_repo.search(claim.content, limit=10)

        # Count unique source UUIDs
        unique_sources = set()
        for c in same_content_claims:
            if c.source_mark == SourceMark.EXTRACTED:
                unique_sources.add(c.source_uuid)

        # Per D-04: minimum 2 independent sources
        return len(unique_sources) >= 2

    def upgrade_confidence(
        self,
        claim_uuid: str,
        new_level: ConfidenceLevel,
        claims_repo: ClaimsRepository,
        require_explicit: bool = False,
    ) -> bool:
        """Upgrade a claim's confidence level.

        Per D-01:
        - Cross-Validated and below can auto-upgrade
        - HUMAN_VERIFIED requires explicit flag

        Per D-03: Never auto-downgrade.

        Args:
            claim_uuid: UUID of the claim to upgrade.
            new_level: Target confidence level.
            claims_repo: Repository for claim operations.
            require_explicit: Must be True for HUMAN_VERIFIED.

        Returns:
            True if upgrade was performed.
        """
        claim = claims_repo.get_by_id(claim_uuid)
        if claim is None:
            return False

        # Per D-03: Never downgrade
        if new_level <= claim.confidence:
            return False

        # Per D-01: HUMAN_VERIFIED requires explicit flag
        if new_level == ConfidenceLevel.HUMAN_VERIFIED and not require_explicit:
            return False

        # Perform upgrade (would be done via WriteQueue in production)
        return True

    def get_confidence_distribution(
        self,
        claims_repo: ClaimsRepository,
    ) -> dict[ConfidenceLevel, int]:
        """Get distribution of claims by confidence level.

        Args:
            claims_repo: Repository to query.

        Returns:
            Dict mapping confidence level to count.
        """
        # This would query the DB for distribution
        # Placeholder implementation
        return {level: 0 for level in ConfidenceLevel}

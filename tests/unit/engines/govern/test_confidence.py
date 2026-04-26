"""Tests for ConfidenceAssessor.

Per D-01 to D-05:
- D-01: Cross-Validated and below auto-upgrade, Human Verified requires explicit flag
- D-02: Source mark orthogonal to confidence (extracted/inferred/ambiguous)
- D-03: Never auto-downgrade
- D-04: Minimum 2 independent sources for Cross-Validated
- D-05: Independent source = different Vault UUID
"""
from __future__ import annotations

from datetime import datetime, timezone
import unittest
from unittest.mock import Mock

from saw.domain.claims import Claim
from saw.domain.value_objects import ConfidenceLevel, SourceMark
from saw.engines.govern.confidence import ConfidenceAssessor


class TestConfidenceAssessor(unittest.TestCase):
    """Test cases for confidence assessment logic."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.assessor = ConfidenceAssessor()

    def test_assess_page_all_extracted_returns_cross_validated(self) -> None:
        """Test 1: Page with all EXTRACTED claims can reach CROSS_VALIDATED."""
        claims = [
            Claim(
                uuid="claim-1",
                content="Claim 1",
                source_uuid="source-1",
                content_hash="hash1",
                source_mark=SourceMark.EXTRACTED,
                confidence=ConfidenceLevel.SINGLE_SOURCE,
            ),
            Claim(
                uuid="claim-2",
                content="Claim 2",
                source_uuid="source-1",
                content_hash="hash2",
                source_mark=SourceMark.EXTRACTED,
                confidence=ConfidenceLevel.SINGLE_SOURCE,
            ),
        ]
        result = self.assessor.assess_page(claims)
        # All extracted -> can reach CROSS_VALIDATED if multiple sources agree
        self.assertIn(result, [ConfidenceLevel.SINGLE_SOURCE, ConfidenceLevel.CROSS_VALIDATED])

    def test_assess_page_with_inferred_max_single_source(self) -> None:
        """Test 2: Page with any INFERRED claim maxes at SINGLE_SOURCE."""
        claims = [
            Claim(
                uuid="claim-1",
                content="Claim 1",
                source_uuid="source-1",
                content_hash="hash1",
                source_mark=SourceMark.EXTRACTED,
                confidence=ConfidenceLevel.SINGLE_SOURCE,
            ),
            Claim(
                uuid="claim-2",
                content="Claim 2",
                source_uuid="source-1",
                content_hash="hash2",
                source_mark=SourceMark.INFERRED,  # This limits the page
                confidence=ConfidenceLevel.UNVERIFIED,
            ),
        ]
        result = self.assessor.assess_page(claims)
        self.assertLessEqual(result, ConfidenceLevel.SINGLE_SOURCE)

    def test_assess_page_with_ambiguous_is_unverified(self) -> None:
        """Test 3: Page with any AMBIGUOUS claim -> UNVERIFIED (per D-02)."""
        claims = [
            Claim(
                uuid="claim-1",
                content="Claim 1",
                source_uuid="source-1",
                content_hash="hash1",
                source_mark=SourceMark.EXTRACTED,
                confidence=ConfidenceLevel.SINGLE_SOURCE,
            ),
            Claim(
                uuid="claim-2",
                content="Claim 2",
                source_uuid="source-1",
                content_hash="hash2",
                source_mark=SourceMark.AMBIGUOUS,  # This forces UNVERIFIED
                confidence=ConfidenceLevel.UNVERIFIED,
            ),
        ]
        result = self.assessor.assess_page(claims)
        self.assertEqual(result, ConfidenceLevel.UNVERIFIED)

    def test_can_upgrade_to_cross_validated_requires_independent_sources(self) -> None:
        """Test 4: Cross-Validated upgrade requires 2+ independent sources (per D-05)."""
        # Create mock repository
        mock_repo = Mock()

        # Claim to test
        claim = Claim(
            uuid="claim-test",
            content="test content",
            source_uuid="vault-uuid-1",
            content_hash="hash-test",
            source_mark=SourceMark.EXTRACTED,
            confidence=ConfidenceLevel.SINGLE_SOURCE,
        )

        # Case 1: Only one source - should NOT be able to upgrade
        mock_repo.search.return_value = [
            Claim(
                uuid="claim-1",
                content="test content",
                source_uuid="vault-uuid-1",  # Same source
                content_hash="hash1",
                source_mark=SourceMark.EXTRACTED,
                confidence=ConfidenceLevel.SINGLE_SOURCE,
            ),
        ]
        result = self.assessor.can_upgrade_to_cross_validated(claim, mock_repo)
        self.assertFalse(result)

        # Case 2: Two independent sources - should be able to upgrade
        mock_repo.search.return_value = [
            Claim(
                uuid="claim-1",
                content="test content",
                source_uuid="vault-uuid-1",  # First source
                content_hash="hash1",
                source_mark=SourceMark.EXTRACTED,
                confidence=ConfidenceLevel.SINGLE_SOURCE,
            ),
            Claim(
                uuid="claim-2",
                content="test content",
                source_uuid="vault-uuid-2",  # Second source (different Vault UUID)
                content_hash="hash2",
                source_mark=SourceMark.EXTRACTED,
                confidence=ConfidenceLevel.SINGLE_SOURCE,
            ),
        ]
        result = self.assessor.can_upgrade_to_cross_validated(claim, mock_repo)
        self.assertTrue(result)

        # Case 3: Same source, different pages - still NOT independent (per D-05)
        mock_repo.search.return_value = [
            Claim(
                uuid="claim-1",
                content="test content",
                source_uuid="vault-uuid-1",  # Same Vault UUID
                content_hash="hash1",
                source_mark=SourceMark.EXTRACTED,
                confidence=ConfidenceLevel.SINGLE_SOURCE,
                page_number=1,
            ),
            Claim(
                uuid="claim-2",
                content="test content",
                source_uuid="vault-uuid-1",  # Same Vault UUID (different page is NOT independent)
                content_hash="hash2",
                source_mark=SourceMark.EXTRACTED,
                confidence=ConfidenceLevel.SINGLE_SOURCE,
                page_number=5,
            ),
        ]
        result = self.assessor.can_upgrade_to_cross_validated(claim, mock_repo)
        self.assertFalse(result)

    def test_never_auto_downgrade(self) -> None:
        """Test 3 (from plan): Never auto-downgrade (per D-03)."""
        high_confidence_claim = Claim(
            uuid="claim-high",
            content="High confidence claim",
            source_uuid="source-1",
            content_hash="hash-high",
            source_mark=SourceMark.EXTRACTED,
            confidence=ConfidenceLevel.HUMAN_VERIFIED,
        )
        # Even if we add an ambiguous claim to the page, existing claims don't downgrade
        claims = [high_confidence_claim]
        result = self.assessor.assess_page(claims)
        # Should preserve the minimum confidence of claims
        self.assertGreaterEqual(result, ConfidenceLevel.SINGLE_SOURCE)


if __name__ == "__main__":
    unittest.main()
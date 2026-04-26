"""Tests for domain value objects."""
from saw.domain.claims import Claim
from saw.domain.value_objects import (
    CapabilityTier,
    ConfidenceLevel,
    FreshnessLevel,
    PageType,
    SourceMark,
    WriteOpStatus,
)


class TestClaimComputeHash:
    """Test Claim.compute_hash produces consistent SHA-256."""

    def test_consistent_hash(self):
        h1 = Claim.compute_hash("test content")
        h2 = Claim.compute_hash("test content")
        assert h1 == h2

    def test_hash_length(self):
        h = Claim.compute_hash("test")
        assert len(h) == 64  # SHA-256 hex digest

    def test_different_content_different_hash(self):
        h1 = Claim.compute_hash("content A")
        h2 = Claim.compute_hash("content B")
        assert h1 != h2

    def test_empty_string_hash(self):
        h = Claim.compute_hash("")
        assert len(h) == 64
        # SHA-256 of empty string is well-known
        assert h == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class TestCapabilityTier:
    """Test CapabilityTier ordering (FULL > LIGHTWEIGHT > OFFLINE)."""

    def test_ordering(self):
        assert CapabilityTier.FULL > CapabilityTier.LIGHTWEIGHT
        assert CapabilityTier.LIGHTWEIGHT > CapabilityTier.OFFLINE
        assert CapabilityTier.FULL > CapabilityTier.OFFLINE

    def test_values(self):
        assert CapabilityTier.FULL == 3
        assert CapabilityTier.LIGHTWEIGHT == 2
        assert CapabilityTier.OFFLINE == 1

    def test_sorting(self):
        tiers = [CapabilityTier.OFFLINE, CapabilityTier.FULL, CapabilityTier.LIGHTWEIGHT]
        sorted_tiers = sorted(tiers)
        assert sorted_tiers == [
            CapabilityTier.OFFLINE,
            CapabilityTier.LIGHTWEIGHT,
            CapabilityTier.FULL,
        ]


class TestConfidenceLevel:
    """Test ConfidenceLevel values match spec (1-4)."""

    def test_values(self):
        assert ConfidenceLevel.UNVERIFIED == 1
        assert ConfidenceLevel.SINGLE_SOURCE == 2
        assert ConfidenceLevel.CROSS_VALIDATED == 3
        assert ConfidenceLevel.HUMAN_VERIFIED == 4

    def test_ordering(self):
        assert ConfidenceLevel.HUMAN_VERIFIED > ConfidenceLevel.CROSS_VALIDATED
        assert ConfidenceLevel.CROSS_VALIDATED > ConfidenceLevel.SINGLE_SOURCE
        assert ConfidenceLevel.SINGLE_SOURCE > ConfidenceLevel.UNVERIFIED


class TestPageType:
    """Test PageType has exactly 5 members."""

    def test_member_count(self):
        assert len(PageType) == 5

    def test_members(self):
        members = {m.name for m in PageType}
        assert members == {"SUMMARY", "META", "SOURCE", "ALIAS", "COLLECTION"}


class TestSourceMark:
    """Test SourceMark enum."""

    def test_members(self):
        assert len(SourceMark) == 3
        members = {m.name for m in SourceMark}
        assert members == {"EXTRACTED", "INFERRED", "AMBIGUOUS"}


class TestFreshnessLevel:
    """Test FreshnessLevel enum."""

    def test_nine_levels(self):
        assert len(FreshnessLevel) == 9

    def test_freshest_vs_stalest(self):
        # Per D-10: Levels 0-8 (0=freshest, 8=stalest)
        assert FreshnessLevel.LEVEL_0 == 0
        assert FreshnessLevel.LEVEL_8 == 8


class TestWriteOpStatus:
    """Test WriteOpStatus enum."""

    def test_members(self):
        assert len(WriteOpStatus) == 4
        members = {m.name for m in WriteOpStatus}
        assert members == {"PENDING", "PROCESSING", "DONE", "FAILED"}

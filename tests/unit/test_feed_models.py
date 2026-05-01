"""Unit tests for feed domain models.

Phase 9: RSS Subscription — Tests for domain layer.
"""
from __future__ import annotations

import pytest

from saw.domain.feed import (
    DeduplicationKey,
    DeduplicationResult,
    DeduplicationService,
    EntryHash,
    EntryStatus,
    FeedConfig,
    normalize_url,
    title_similarity,
)


class TestEntryHash:
    """Test EntryHash computation."""

    def test_compute_sha256_hash(self) -> None:
        """Test 1: EntryHash computes SHA256 of normalized content."""
        content = "<p>Hello  World!</p>"
        result = EntryHash.compute(content)

        # Should be SHA256 hash (64 hex chars)
        assert len(result) == 64
        assert all(c in '0123456789abcdef' for c in result)

    def test_normalize_html_tags(self) -> None:
        """HTML tags should be stripped before hashing."""
        content1 = "<p>Hello World</p>"
        content2 = "Hello World"

        assert EntryHash.compute(content1) == EntryHash.compute(content2)

    def test_normalize_whitespace(self) -> None:
        """Whitespace should be collapsed before hashing."""
        content1 = "Hello   World"
        content2 = "Hello World"

        assert EntryHash.compute(content1) == EntryHash.compute(content2)

    def test_normalize_case(self) -> None:
        """Content should be lowercased before hashing."""
        content1 = "Hello World"
        content2 = "HELLO WORLD"

        assert EntryHash.compute(content1) == EntryHash.compute(content2)


class TestDeduplicationKey:
    """Test DeduplicationKey generation."""

    def test_combine_guid_title_content(self) -> None:
        """Test 2: DeduplicationKey combines GUID + title_hash + content_hash."""
        key = DeduplicationKey(
            guid="test-guid-123",
            title_hash="abcd1234",
            content_hash="efgh5678",
        )

        result = key.compute_id()
        assert result == "test-guid-123:abcd1234:efgh5678"

    def test_from_entry(self) -> None:
        """DeduplicationKey.from_entry should compute hashes."""
        key = DeduplicationKey.from_entry(
            guid="entry-1",
            title="Test Title",
            content="Test Content",
        )

        assert key.guid == "entry-1"
        assert len(key.title_hash) == 8
        assert len(key.content_hash) == 8


class TestFeedConfig:
    """Test FeedConfig validation."""

    def test_valid_url_and_interval(self) -> None:
        """Valid configuration should work."""
        config = FeedConfig(
            url="https://example.com/feed.xml",
            category="tech",
            poll_interval=3600,
        )

        assert config.url == "https://example.com/feed.xml"
        assert config.category == "tech"
        assert config.poll_interval == 3600

    def test_validate_poll_interval_min(self) -> None:
        """Test 3: FeedConfig validates poll_interval min bound."""
        with pytest.raises(ValueError, match="poll_interval must be between"):
            FeedConfig(url="https://example.com/feed.xml", poll_interval=100)

    def test_validate_poll_interval_max(self) -> None:
        """FeedConfig validates poll_interval max bound."""
        with pytest.raises(ValueError, match="poll_interval must be between"):
            FeedConfig(url="https://example.com/feed.xml", poll_interval=100000)

    def test_validate_url_scheme(self) -> None:
        """FeedConfig validates URL scheme (http/https only)."""
        with pytest.raises(ValueError, match="URL must start with"):
            FeedConfig(url="ftp://example.com/feed.xml")

    def test_poll_interval_min_boundary(self) -> None:
        """Minimum poll interval (900) should be accepted."""
        config = FeedConfig(url="https://example.com/feed.xml", poll_interval=900)
        assert config.poll_interval == 900

    def test_poll_interval_max_boundary(self) -> None:
        """Maximum poll interval (86400) should be accepted."""
        config = FeedConfig(url="https://example.com/feed.xml", poll_interval=86400)
        assert config.poll_interval == 86400


class TestEntryStatus:
    """Test EntryStatus enum."""

    def test_status_values(self) -> None:
        """Test 4: EntryStatus enum has values: new, updated, historical."""
        assert EntryStatus.NEW.value == "new"
        assert EntryStatus.UPDATED.value == "updated"
        assert EntryStatus.HISTORICAL.value == "historical"


class TestURLNormalization:
    """Test URL normalization for deduplication."""

    def test_remove_utm_params(self) -> None:
        """Test 13: URL normalization removes tracking parameters."""
        url = "https://example.com/article?utm_source=twitter&id=123"
        result = normalize_url(url)

        assert "utm_source" not in result
        assert "id=123" in result

    def test_remove_ref_param(self) -> None:
        """ref parameter should be removed."""
        url = "https://example.com/article?ref=newsletter&id=456"
        result = normalize_url(url)

        assert "ref" not in result
        assert "id=456" in result

    def test_remove_fragment(self) -> None:
        """URL fragment should be removed."""
        url = "https://example.com/article#section"
        result = normalize_url(url)

        assert "#" not in result
        assert "section" not in result

    def test_preserve_valid_params(self) -> None:
        """Valid parameters should be preserved."""
        url = "https://example.com/article?page=2&sort=date"
        result = normalize_url(url)

        assert "page=2" in result
        assert "sort=date" in result


class TestTitleSimilarity:
    """Test title similarity computation."""

    def test_identical_titles(self) -> None:
        """Identical titles should have similarity 1.0."""
        assert title_similarity("Hello World", "Hello World") == 1.0

    def test_similar_titles(self) -> None:
        """Similar titles should have high similarity."""
        similarity = title_similarity("Hello World", "Hello World!")

        assert similarity > 0.9

    def test_different_titles(self) -> None:
        """Different titles should have low similarity."""
        similarity = title_similarity("Hello World", "Goodbye Moon")

        assert similarity < 0.5

    def test_case_insensitive(self) -> None:
        """Similarity should be case-insensitive."""
        similarity = title_similarity("Hello World", "HELLO WORLD")

        assert similarity == 1.0


class MockFeedEntry:
    """Mock FeedEntry for testing."""

    def __init__(
        self,
        id: str,
        guid: str,
        title: str,
        content_hash: str | None = None,
    ) -> None:
        self.id = id
        self.guid = guid
        self.title = title
        self.content_hash = content_hash


class TestDeduplicationService:
    """Test DeduplicationService."""

    def test_same_guid_detected(self) -> None:
        """Test 10: Same GUID + different title -> detected as updated."""
        service = DeduplicationService()
        existing = MockFeedEntry(
            id="entry-1",
            guid="guid-123",
            title="Old Title",
            content_hash=None,
        )

        result = service.check_duplicate(
            guid="guid-123",
            title="New Title",
            content="New content",
            existing_entries=[existing],
        )

        assert result.is_duplicate is True
        assert result.match_type == "exact_guid"
        assert result.entry_id == "entry-1"

    def test_different_guid_same_title(self) -> None:
        """Test 11: Different GUID + same title -> detected as duplicate."""
        service = DeduplicationService()
        existing = MockFeedEntry(
            id="entry-1",
            guid="old-guid",
            title="Same Title Here",
            content_hash=None,
        )

        result = service.check_duplicate(
            guid="new-guid",
            title="Same Title Here",
            content="Different content",
            existing_entries=[existing],
        )

        # Should match on title similarity
        assert result.is_duplicate is True
        assert result.match_type == "fuzzy_title"
        assert result.entry_id == "entry-1"

    def test_similar_titles_detected(self) -> None:
        """Test 12: Similar titles (edit distance < 3) -> detected as potential duplicate."""
        service = DeduplicationService()
        existing = MockFeedEntry(
            id="entry-1",
            guid="guid-1",
            title="Hello World Article",
            content_hash=None,
        )

        result = service.check_duplicate(
            guid="guid-2",
            title="Hello World Article!",  # Minor difference
            content="Different content",
            existing_entries=[existing],
        )

        assert result.is_duplicate is True
        assert result.match_type == "fuzzy_title"
        assert result.similarity_score > 0.9

    def test_content_hash_match(self) -> None:
        """Content hash match should be detected."""
        service = DeduplicationService()
        from saw.domain.feed import EntryHash

        content = "Same content here"
        content_hash = EntryHash.compute(content)

        existing = MockFeedEntry(
            id="entry-1",
            guid="old-guid",
            title="Old Title",
            content_hash=content_hash,
        )

        result = service.check_duplicate(
            guid="new-guid",
            title="New Title",
            content=content,
            existing_entries=[existing],
        )

        assert result.is_duplicate is True
        assert result.match_type == "content_hash"

    def test_no_match(self) -> None:
        """No match should return non-duplicate result."""
        service = DeduplicationService()
        existing = MockFeedEntry(
            id="entry-1",
            guid="guid-1",
            title="Completely Different Title",
            content_hash="abc123",
        )

        result = service.check_duplicate(
            guid="guid-2",
            title="Another Different Title",
            content="Different content",
            existing_entries=[existing],
        )

        assert result.is_duplicate is False
        assert result.match_type == "none"
        assert result.entry_id is None

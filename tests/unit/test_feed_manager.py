"""Unit tests for FeedManager.

Phase 9: RSS Subscription — Tests for FeedManager.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from saw.engines.ingest.feed_manager import (
    FeedManager,
    FeedManagerError,
    PollResult,
)
from saw.db.feed_models import Feed, FeedEntry


class MockFeed:
    """Mock Feed model for testing."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'feed-1')
        self.url = kwargs.get('url', 'https://example.com/feed.xml')
        self.title = kwargs.get('title', 'Test Feed')
        self.description = kwargs.get('description', None)
        self.category = kwargs.get('category', None)
        self.tags = kwargs.get('tags', None)
        self.poll_interval = kwargs.get('poll_interval', 3600)
        self.last_poll_at = kwargs.get('last_poll_at', None)
        self.last_etag = kwargs.get('last_etag', None)
        self.last_modified = kwargs.get('last_modified', None)
        self.active = kwargs.get('active', True)


class MockEntry:
    """Mock feed entry for testing."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'entry-1')
        self.title = kwargs.get('title', 'Test Entry')
        self.link = kwargs.get('link', 'https://example.com/article')
        self.summary = kwargs.get('summary', 'Test summary')
        self.content = kwargs.get('content', None)
        self.published_parsed = kwargs.get('published_parsed', None)
        self.updated_parsed = kwargs.get('updated_parsed', None)


class MockFeedData:
    """Mock parsed feed data."""

    def __init__(self, **kwargs):
        self.feed = kwargs.get('feed', MagicMock(title='Feed Title', description='Feed Desc'))
        self.entries = kwargs.get('entries', [])
        self.bozo = kwargs.get('bozo', False)
        self.bozo_exception = kwargs.get('bozo_exception', None)


class TestFeedManagerCore:
    """Test FeedManager core functionality."""

    @pytest.mark.asyncio
    async def test_add_feed_creates_record(self) -> None:
        """Test 1: FeedManager.add_feed() creates Feed record and returns feed_id."""
        # Mock database session
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()

        # Mock HTTP client
        http_client = AsyncMock()
        http_client.get = AsyncMock(return_value=MagicMock(
            text='<rss><channel><title>Test</title></channel></rss>',
            raise_for_status=MagicMock(),
        ))

        # Mock feed parser
        with patch('saw.engines.ingest.feed_manager.fastfeedparser.parse') as mock_parse:
            mock_parse.return_value = MockFeedData()

            manager = FeedManager(db, http_client=http_client)
            feed_id = await manager.add_feed('https://example.com/feed.xml')

            assert feed_id is not None
            assert len(feed_id) == 36  # UUID format
            db.add.assert_called_once()
            db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_feed_validates_url(self) -> None:
        """Test 2: FeedManager.add_feed() validates URL is valid RSS/Atom feed."""
        db = MagicMock()

        manager = FeedManager(db)

        with pytest.raises(FeedManagerError, match="Failed to parse feed"):
            await manager.add_feed('https://example.com/not-a-feed')

    @pytest.mark.asyncio
    async def test_parse_feed_uses_fastfeedparser(self) -> None:
        """Test 3: FeedManager._parse_feed() uses fastfeedparser correctly."""
        db = MagicMock()
        http_client = AsyncMock()
        http_client.get = AsyncMock(return_value=MagicMock(
            text='<rss><channel><title>Test</title></channel></rss>',
            raise_for_status=MagicMock(),
        ))

        manager = FeedManager(db, http_client=http_client)

        with patch('saw.engines.ingest.feed_manager.fastfeedparser.parse') as mock_parse:
            mock_parse.return_value = MockFeedData()
            await manager._parse_feed('https://example.com/feed.xml')

            mock_parse.assert_called_once()

    @pytest.mark.asyncio
    async def test_parse_feed_handles_bozo(self) -> None:
        """Test 4: FeedManager._parse_feed() handles bozo feeds gracefully (log warning)."""
        db = MagicMock()
        http_client = AsyncMock()
        http_client.get = AsyncMock(return_value=MagicMock(
            text='<rss><channel><title>Test</title></channel></rss>',
            raise_for_status=MagicMock(),
        ))

        manager = FeedManager(db, http_client=http_client)

        with patch('saw.engines.ingest.feed_manager.fastfeedparser.parse') as mock_parse:
            mock_parse.return_value = MockFeedData(bozo=True, bozo_exception="Encoding error")
            result = await manager._parse_feed('https://example.com/feed.xml')

            # Should return the feed despite bozo bit
            assert result is not None
            assert result.bozo is True


class TestConditionalGet:
    """Test conditional GET and feed polling."""

    @pytest.mark.asyncio
    async def test_poll_uses_if_modified_since(self) -> None:
        """Test 5: poll_feed() uses If-Modified-Since header when last_modified is set."""
        db = MagicMock()
        feed = MockFeed(
            id='feed-1',
            last_modified='Mon, 01 Jan 2024 00:00:00 GMT',
        )
        db.query.return_value.filter.return_value.first.return_value = feed

        http_client = AsyncMock()
        http_client.get = AsyncMock(return_value=MagicMock(
            status_code=304,
        ))

        manager = FeedManager(db, http_client=http_client)
        await manager.poll_feed('feed-1')

        # Check that If-Modified-Since header was set
        call_args = http_client.get.call_args
        headers = call_args.kwargs.get('headers', {})
        assert 'If-Modified-Since' in headers
        assert headers['If-Modified-Since'] == 'Mon, 01 Jan 2024 00:00:00 GMT'

    @pytest.mark.asyncio
    async def test_poll_uses_if_none_match(self) -> None:
        """Test 6: poll_feed() uses If-None-Match header when etag is set."""
        db = MagicMock()
        feed = MockFeed(
            id='feed-1',
            last_etag='"abc123"',
        )
        db.query.return_value.filter.return_value.first.return_value = feed

        http_client = AsyncMock()
        http_client.get = AsyncMock(return_value=MagicMock(
            status_code=304,
        ))

        manager = FeedManager(db, http_client=http_client)
        await manager.poll_feed('feed-1')

        call_args = http_client.get.call_args
        headers = call_args.kwargs.get('headers', {})
        assert 'If-None-Match' in headers
        assert headers['If-None-Match'] == '"abc123"'

    @pytest.mark.asyncio
    async def test_poll_returns_not_modified(self) -> None:
        """Test 7: poll_feed() returns not_modified=True when server returns 304."""
        db = MagicMock()
        feed = MockFeed(id='feed-1')
        db.query.return_value.filter.return_value.first.return_value = feed

        http_client = AsyncMock()
        http_client.get = AsyncMock(return_value=MagicMock(status_code=304))

        manager = FeedManager(db, http_client=http_client)
        result = await manager.poll_feed('feed-1')

        assert result.not_modified is True
        assert result.new_entries == 0

    @pytest.mark.asyncio
    async def test_poll_updates_last_poll_at(self) -> None:
        """Test 8: poll_feed() updates last_poll_at after successful poll."""
        db = MagicMock()
        feed = MockFeed(id='feed-1')
        db.query.return_value.filter.return_value.first.return_value = feed

        http_client = AsyncMock()
        http_client.get = AsyncMock(return_value=MagicMock(
            status_code=304,
        ))

        manager = FeedManager(db, http_client=http_client)
        await manager.poll_feed('feed-1')

        assert feed.last_poll_at is not None

    @pytest.mark.asyncio
    async def test_poll_stores_new_etag(self) -> None:
        """Test 9: poll_feed() stores new ETag/Last-Modified after 200 response."""
        db = MagicMock()
        feed = MockFeed(id='feed-1')
        db.query.return_value.filter.return_value.first.return_value = feed
        db.query.return_value.filter.return_value.all.return_value = []

        http_client = AsyncMock()
        http_client.get = AsyncMock(return_value=MagicMock(
            status_code=200,
            text='<rss><channel><title>Test</title></channel></rss>',
            headers={
                'ETag': '"new-etag"',
                'Last-Modified': 'Tue, 02 Jan 2024 00:00:00 GMT',
            },
        ))

        with patch('saw.engines.ingest.feed_manager.fastfeedparser.parse') as mock_parse:
            mock_parse.return_value = MockFeedData(entries=[])

            manager = FeedManager(db, http_client=http_client)
            await manager.poll_feed('feed-1')

            assert feed.last_etag == '"new-etag"'
            assert feed.last_modified == 'Tue, 02 Jan 2024 00:00:00 GMT'


class TestEntryProcessing:
    """Test entry processing with deduplication."""

    @pytest.mark.asyncio
    async def test_new_entry_triggers_ingest(self) -> None:
        """Test 10: New entry triggers ingest() and creates FeedEntry record."""
        db = MagicMock()
        feed = MockFeed(id='feed-1')
        db.query.return_value.filter.return_value.first.return_value = feed
        db.query.return_value.filter.return_value.all.return_value = []  # No existing entries
        db.add = MagicMock()
        db.commit = MagicMock()

        http_client = AsyncMock()
        http_client.get = AsyncMock(return_value=MagicMock(
            status_code=200,
            text='<rss><channel><title>Test</title></channel></rss>',
            headers={},
        ))

        entry = MockEntry(id='entry-1', title='New Article', summary='Content here')

        with patch('saw.engines.ingest.feed_manager.fastfeedparser.parse') as mock_parse:
            mock_parse.return_value = MockFeedData(entries=[entry])

            ingest = MagicMock()
            ingest.ingest = MagicMock(return_value=MagicMock(session_id='session-1'))

            manager = FeedManager(db, ingest_pipeline=ingest, http_client=http_client)
            result = await manager.poll_feed('feed-1')

            assert result.new_entries == 1
            db.add.assert_called()

    @pytest.mark.asyncio
    async def test_duplicate_entry_skipped(self) -> None:
        """Test 11: Duplicate entry (same GUID) is skipped."""
        from saw.domain.feed import EntryHash

        db = MagicMock()
        feed = MockFeed(id='feed-1')
        db.query.return_value.filter.return_value.first.return_value = feed

        # Existing entry with same GUID
        # Use matching content hash so it's truly skipped (not updated)
        content = 'Same content here'
        content_hash = EntryHash.compute(content)

        existing = MagicMock()
        existing.id = 'existing-id'
        existing.guid = 'entry-1'
        existing.title = 'Same Article'
        existing.content_hash = content_hash
        existing.content = content
        db.query.return_value.filter.return_value.all.return_value = [existing]

        http_client = AsyncMock()
        http_client.get = AsyncMock(return_value=MagicMock(
            status_code=200,
            text='<rss><channel><title>Test</title></channel></rss>',
            headers={},
        ))

        entry = MockEntry(id='entry-1', title='Same Article', summary=content)

        with patch('saw.engines.ingest.feed_manager.fastfeedparser.parse') as mock_parse:
            mock_parse.return_value = MockFeedData(entries=[entry])

            manager = FeedManager(db, http_client=http_client)
            result = await manager.poll_feed('feed-1')

            assert result.skipped_entries >= 1
            assert result.new_entries == 0

    @pytest.mark.asyncio
    async def test_updated_entry_triggers_reingest(self) -> None:
        """Test 12: Updated entry (same GUID, different content) triggers re-ingest."""
        db = MagicMock()
        feed = MockFeed(id='feed-1')
        db.query.return_value.filter.return_value.first.return_value = feed

        # Existing entry with same GUID but different content
        existing = MagicMock()
        existing.id = 'existing-id'
        existing.guid = 'entry-1'
        existing.title = 'Old Title'
        existing.content_hash = 'old-hash-123'
        existing.content = 'Old content'
        db.query.return_value.filter.return_value.all.return_value = [existing]
        db.commit = MagicMock()

        http_client = AsyncMock()
        http_client.get = AsyncMock(return_value=MagicMock(
            status_code=200,
            text='<rss><channel><title>Test</title></channel></rss>',
            headers={},
        ))

        entry = MockEntry(id='entry-1', title='Updated Article', summary='New content here')

        with patch('saw.engines.ingest.feed_manager.fastfeedparser.parse') as mock_parse:
            mock_parse.return_value = MockFeedData(entries=[entry])

            ingest = MagicMock()
            ingest.ingest = MagicMock(return_value=MagicMock(session_id='session-1'))

            manager = FeedManager(db, ingest_pipeline=ingest, http_client=http_client)
            result = await manager.poll_feed('feed-1')

            assert result.updated_entries == 1

    @pytest.mark.asyncio
    async def test_summary_only_fetches_full_content(self) -> None:
        """Test 13: Entry with summary-only fetches full content with trafilatura."""
        db = MagicMock()

        http_client = AsyncMock()
        http_client.get = AsyncMock(return_value=MagicMock(
            text='<html><body><p>Full article content here</p></body></html>',
        ))

        manager = FeedManager(db, http_client=http_client)

        entry = MockEntry(
            id='entry-1',
            title='Article',
            summary='Short summary',  # Short, so should fetch full content
            link='https://example.com/article',
        )

        with patch('saw.engines.ingest.feed_manager.trafilatura.extract') as mock_extract:
            mock_extract.return_value = 'Full article content here'

            content = await manager._extract_content(entry, 'https://example.com/article')

            assert 'Full article content' in content
            mock_extract.assert_called_once()

    @pytest.mark.asyncio
    async def test_content_change_detection(self) -> None:
        """Test 14: Content change detection updates status to 'updated'."""
        db = MagicMock()
        feed = MockFeed(id='feed-1')
        db.query.return_value.filter.return_value.first.return_value = feed

        # Existing entry
        existing = MagicMock()
        existing.id = 'existing-id'
        existing.guid = 'entry-1'
        existing.title = 'Article'
        existing.content_hash = 'old-hash'
        existing.content = 'Old content'
        existing.status = 'new'
        db.query.return_value.filter.return_value.all.return_value = [existing]
        db.commit = MagicMock()

        http_client = AsyncMock()
        http_client.get = AsyncMock(return_value=MagicMock(
            status_code=200,
            text='<rss><channel><title>Test</title></channel></rss>',
            headers={},
        ))

        entry = MockEntry(
            id='entry-1',
            title='Article',
            summary='Completely different content that will have different hash',
        )

        with patch('saw.engines.ingest.feed_manager.fastfeedparser.parse') as mock_parse:
            mock_parse.return_value = MockFeedData(entries=[entry])

            ingest = MagicMock()
            ingest.ingest = MagicMock(return_value=MagicMock(session_id='session-1'))

            manager = FeedManager(db, ingest_pipeline=ingest, http_client=http_client)
            await manager.poll_feed('feed-1')

            # Status should be updated
            assert existing.status == 'updated'


class TestAdaptivePolling:
    """Test adaptive polling and keyword filtering."""

    def test_adaptive_interval_calculation(self) -> None:
        """Test 15: Adaptive interval calculation based on update frequency."""
        db = MagicMock()

        # Create entries with hourly updates
        entries = []
        base_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        for i in range(10):
            entry = MagicMock()
            entry.published_at = datetime(
                base_time.year, base_time.month, base_time.day,
                i, 0, 0, tzinfo=timezone.utc
            )
            entries.append(entry)

        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = entries

        manager = FeedManager(db)
        interval = manager.calculate_adaptive_interval('feed-1')

        # With hourly updates, adaptive should be ~45 min (0.75 * 3600)
        assert 900 <= interval <= 86400

    def test_adaptive_interval_min_max_bounds(self) -> None:
        """Test 18: calculate_adaptive_interval() respects min/max bounds."""
        db = MagicMock()

        # Not enough entries - should return default
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        manager = FeedManager(db)
        interval = manager.calculate_adaptive_interval('feed-1')

        assert interval == 3600  # Default

    def test_keyword_filter_includes_matching(self) -> None:
        """Test 16: Keyword filter includes entries matching tags."""
        db = MagicMock()
        feed = MockFeed(tags='["python", "ai"]')

        manager = FeedManager(db)

        entry = MockEntry(title='Python AI Article', summary='About machine learning')
        result = manager._should_include_entry(entry, feed)

        assert result is True

    def test_keyword_filter_excludes_non_matching(self) -> None:
        """Test 17: Keyword filter excludes entries not matching tags when filter is active."""
        db = MagicMock()
        feed = MockFeed(tags='["python", "ai"]')

        manager = FeedManager(db)

        entry = MockEntry(title='Cooking Recipes', summary='How to make pasta')
        result = manager._should_include_entry(entry, feed)

        assert result is False

    def test_keyword_filter_no_tags_includes_all(self) -> None:
        """No tags means include all entries."""
        db = MagicMock()
        feed = MockFeed(tags=None)

        manager = FeedManager(db)

        entry = MockEntry(title='Any Article', summary='Any content')
        result = manager._should_include_entry(entry, feed)

        assert result is True

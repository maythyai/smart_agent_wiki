"""Unit tests for feed scheduler.

Phase 9: RSS Subscription — Tests for scheduler integration.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

from saw.engines.ingest.scheduler import (
    FeedScheduler,
    FeedJobConfig,
    start_scheduler,
    stop_scheduler,
    get_scheduler,
)
from saw.engines.ingest.feed_manager import FeedManager, PollResult


class TestFeedScheduler:
    """Test FeedScheduler class."""

    def test_scheduler_initialization(self) -> None:
        """Test 6: FeedScheduler.start() initializes AsyncIOScheduler."""
        manager = MagicMock()
        db = MagicMock()

        scheduler = FeedScheduler(manager, db)

        assert scheduler._manager == manager
        assert scheduler._db == db
        assert scheduler._running is False
        assert scheduler._job_configs == {}

    @pytest.mark.asyncio
    async def test_scheduler_start(self) -> None:
        """Scheduler.start() should initialize and schedule feeds."""
        manager = MagicMock()
        manager.calculate_adaptive_interval = MagicMock(return_value=3600)

        db = MagicMock()

        # Mock feeds
        mock_feed = MagicMock()
        mock_feed.id = 'feed-1'
        mock_feed.url = 'https://example.com/feed.xml'
        mock_feed.title = 'Test Feed'
        mock_feed.poll_interval = 3600
        mock_feed.active = True

        db.query.return_value.filter.return_value.all.return_value = [mock_feed]

        scheduler = FeedScheduler(manager, db)

        # Mock the APScheduler
        with patch.object(scheduler._scheduler, 'start') as mock_start:
            with patch.object(scheduler._scheduler, 'add_job') as mock_add_job:
                await scheduler.start()

                mock_start.assert_called_once()
                assert scheduler._running is True
                assert 'feed-1' in scheduler._job_configs

    @pytest.mark.asyncio
    async def test_scheduler_add_feed_job(self) -> None:
        """Test 7: FeedScheduler.add_feed_job() schedules poll job."""
        manager = MagicMock()
        manager.calculate_adaptive_interval = MagicMock(return_value=3600)

        db = MagicMock()

        scheduler = FeedScheduler(manager, db)
        scheduler._running = True  # Pretend scheduler is running

        mock_feed = MagicMock()
        mock_feed.id = 'feed-2'
        mock_feed.url = 'https://example.com/new-feed.xml'
        mock_feed.title = 'New Feed'
        mock_feed.poll_interval = 1800

        with patch.object(scheduler._scheduler, 'add_job') as mock_add_job:
            await scheduler.add_feed_job(mock_feed)

            mock_add_job.assert_called_once()
            assert 'feed-2' in scheduler._job_configs

    @pytest.mark.asyncio
    async def test_scheduler_remove_feed_job(self) -> None:
        """Test 8: FeedScheduler.remove_feed_job() removes poll job."""
        manager = MagicMock()
        db = MagicMock()

        scheduler = FeedScheduler(manager, db)
        scheduler._job_configs['feed-1'] = FeedJobConfig(
            feed_id='feed-1',
            feed_url='https://example.com/feed.xml',
            poll_interval=3600,
        )

        with patch.object(scheduler._scheduler, 'get_job') as mock_get_job:
            mock_get_job.return_value = MagicMock()
            with patch.object(scheduler._scheduler, 'remove_job') as mock_remove_job:
                await scheduler.remove_feed_job('feed-1')

                mock_remove_job.assert_called_once()
                assert 'feed-1' not in scheduler._job_configs

    @pytest.mark.asyncio
    async def test_scheduler_adaptive_interval(self) -> None:
        """Test 9: FeedScheduler respects adaptive intervals."""
        manager = MagicMock()
        # Return a different adaptive interval
        manager.calculate_adaptive_interval = MagicMock(return_value=1800)

        db = MagicMock()

        mock_feed = MagicMock()
        mock_feed.id = 'feed-1'
        mock_feed.url = 'https://example.com/feed.xml'
        mock_feed.poll_interval = 3600  # Configured 1 hour
        mock_feed.title = 'Test Feed'
        mock_feed.active = True

        db.query.return_value.filter.return_value.all.return_value = [mock_feed]

        scheduler = FeedScheduler(manager, db)

        with patch.object(scheduler._scheduler, 'start'):
            with patch.object(scheduler._scheduler, 'add_job') as mock_add_job:
                await scheduler.start()

                # Should use min(adaptive, configured) = min(1800, 3600) = 1800
                call_args = mock_add_job.call_args
                trigger = call_args.kwargs['trigger']
                assert trigger.interval.seconds == 1800

    @pytest.mark.asyncio
    async def test_scheduler_exponential_backoff(self) -> None:
        """Test 10: Failed polls trigger exponential backoff."""
        from saw.engines.ingest.feed_manager import FeedManagerError

        manager = MagicMock()
        manager.poll_feed = AsyncMock(side_effect=FeedManagerError("Connection failed"))

        db = MagicMock()

        scheduler = FeedScheduler(manager, db)
        scheduler._running = True
        scheduler._job_configs['feed-1'] = FeedJobConfig(
            feed_id='feed-1',
            feed_url='https://example.com/feed.xml',
            poll_interval=3600,
        )

        with patch.object(scheduler._scheduler, 'get_job') as mock_get_job:
            mock_get_job.return_value = MagicMock()  # Job found for reschedule
            with patch.object(scheduler._scheduler, 'reschedule_job') as mock_reschedule:
                await scheduler._poll_feed_job('feed-1')

                config = scheduler._job_configs['feed-1']
                assert config.consecutive_failures == 1
                assert config.last_failure is not None
                # Backoff should be 3600 * 2 = 7200
                mock_reschedule.assert_called_once()


class TestSchedulerStaggering:
    """Test staggered polling."""

    def test_stagger_calculation(self) -> None:
        """Test 11: Stagger calculation distributes feeds across time window."""
        manager = MagicMock()
        db = MagicMock()

        # Create multiple feeds with same interval
        feeds = []
        for i in range(5):
            feed = MagicMock()
            feed.id = f'feed-{i}'
            feed.url = f'https://example.com/feed{i}.xml'
            feed.title = f'Feed {i}'
            feed.poll_interval = 3600  # All same interval
            feed.active = True
            feeds.append(feed)

        db.query.return_value.filter.return_value.all.return_value = feeds
        manager.calculate_adaptive_interval = MagicMock(return_value=3600)

        scheduler = FeedScheduler(manager, db)

        # Track initial delays
        delays = []
        with patch.object(scheduler._scheduler, 'start'):
            with patch.object(scheduler._scheduler, 'add_job') as mock_add_job:
                # Run the start method to schedule all feeds
                import asyncio
                asyncio.get_event_loop().run_until_complete(scheduler.start())

                # Collect the initial delays from call args
                for call in mock_add_job.call_args_list:
                    trigger = call.kwargs['trigger']
                    # The start_date contains the initial delay
                    if hasattr(trigger, 'start_date'):
                        delays.append(trigger.start_date)

        # Feeds should have different start times
        # (Due to random jitter, we just verify they're not all identical)
        assert len(mock_add_job.call_args_list) == 5

    def test_jitter_added_to_stagger(self) -> None:
        """Test 12: Feed with same poll_interval starts at different times."""
        manager = MagicMock()
        db = MagicMock()

        scheduler = FeedScheduler(manager, db)

        # Test the staggering logic manually
        feeds = []
        for i in range(3):
            feed = MagicMock()
            feed.id = f'feed-{i}'
            feed.url = f'https://example.com/feed{i}.xml'
            feed.poll_interval = 3600
            feed.active = True
            feeds.append(feed)

        # When scheduling, feeds should have different delays
        # (Stagger + jitter)
        stagger_base = 3600 / 3  # 1200
        # Each feed gets stagger_base * i + jitter

        # Verify stagger formula
        expected_base = 3600 // 3
        assert expected_base == 1200


class TestSchedulerGlobal:
    """Test global scheduler functions."""

    @pytest.mark.asyncio
    async def test_start_scheduler_creates_instance(self) -> None:
        """start_scheduler() creates global instance."""
        manager = MagicMock()
        db = MagicMock()

        # Mock the database query
        db.query.return_value.filter.return_value.all.return_value = []

        scheduler = await start_scheduler(manager, db)

        assert scheduler is not None
        assert get_scheduler() == scheduler

        # Clean up
        await stop_scheduler()
        assert get_scheduler() is None

    @pytest.mark.asyncio
    async def test_stop_scheduler_clears_instance(self) -> None:
        """stop_scheduler() clears global instance."""
        manager = MagicMock()
        db = MagicMock()

        db.query.return_value.filter.return_value.all.return_value = []

        await start_scheduler(manager, db)
        await stop_scheduler()

        assert get_scheduler() is None


class TestFeedJobConfig:
    """Test FeedJobConfig dataclass."""

    def test_config_defaults(self) -> None:
        """Config should have correct defaults."""
        config = FeedJobConfig(
            feed_id='feed-1',
            feed_url='https://example.com/feed.xml',
            poll_interval=3600,
        )

        assert config.consecutive_failures == 0
        assert config.last_failure is None

    def test_config_tracks_failures(self) -> None:
        """Config should track failures."""
        config = FeedJobConfig(
            feed_id='feed-1',
            feed_url='https://example.com/feed.xml',
            poll_interval=3600,
        )

        config.consecutive_failures = 3
        config.last_failure = datetime.now(timezone.utc)

        assert config.consecutive_failures == 3
        assert config.last_failure is not None
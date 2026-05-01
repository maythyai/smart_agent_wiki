"""APScheduler-based feed polling scheduler.

Phase 9: RSS Subscription — Scheduler integration.
Per Pitfall 27: Implements adaptive intervals and exponential backoff.
"""
from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore

from saw.db.feed_models import Feed
from saw.engines.ingest.feed_manager import FeedManager, FeedManagerError

logger = logging.getLogger(__name__)


@dataclass
class FeedJobConfig:
    """Configuration for a feed polling job."""
    feed_id: str
    feed_url: str
    poll_interval: int
    consecutive_failures: int = 0
    last_failure: Optional[datetime] = None


class FeedScheduler:
    """APScheduler-based feed polling scheduler.

    Per Pitfall 27: Implements adaptive intervals, conditional GET,
    and exponential backoff for failing feeds.
    """

    def __init__(
        self,
        feed_manager: FeedManager,
        db_session: Any,
        on_poll_complete: Optional[Callable[[str, Any], None]] = None,
    ) -> None:
        """Initialize the scheduler.

        Args:
            feed_manager: FeedManager instance for polling.
            db_session: SQLAlchemy database session.
            on_poll_complete: Optional callback for poll completion events.
        """
        self._manager = feed_manager
        self._db = db_session
        self._on_poll_complete = on_poll_complete

        self._scheduler = AsyncIOScheduler(
            jobstores={"default": MemoryJobStore()},
            # Use UTC timezone
            timezone="UTC",
        )
        self._job_configs: dict[str, FeedJobConfig] = {}
        self._running = False

    async def start(self) -> None:
        """Start the scheduler and load all active feeds.

        Per Pitfall 27: Staggers polling across time windows.
        """
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._scheduler.start()
        self._running = True

        # Load all active feeds from database
        feeds = self._db.query(Feed).filter(Feed.active == True).all()

        if not feeds:
            logger.info("No active feeds to schedule")
            return

        # Group feeds by poll_interval for staggering
        interval_groups: dict[int, list[Feed]] = {}
        for feed in feeds:
            if feed.poll_interval not in interval_groups:
                interval_groups[feed.poll_interval] = []
            interval_groups[feed.poll_interval].append(feed)

        # Stagger feeds within each interval group
        for interval, group_feeds in interval_groups.items():
            stagger_delay = interval / max(len(group_feeds), 1)

            for i, feed in enumerate(group_feeds):
                # Calculate initial delay (staggered start)
                initial_delay = int(stagger_delay * i)
                # Add small random jitter to avoid exact alignment
                jitter = random.randint(0, min(60, max(1, stagger_delay // 2)))

                await self._add_staggered_feed_job(
                    feed,
                    initial_delay=initial_delay + jitter,
                )

        logger.info(f"Scheduler started with {len(feeds)} feeds (staggered)")

    async def stop(self) -> None:
        """Stop the scheduler gracefully."""
        if not self._running:
            return

        self._scheduler.shutdown(wait=True)
        self._running = False
        logger.info("Scheduler stopped")

    async def _add_staggered_feed_job(
        self,
        feed: Feed,
        initial_delay: int = 0,
    ) -> None:
        """Add a feed job with staggered start time.

        Args:
            feed: Feed model instance.
            initial_delay: Seconds before first poll.
        """
        job_id = f"feed_poll_{feed.id}"

        # Calculate adaptive interval
        adaptive_interval = self._manager.calculate_adaptive_interval(feed.id)

        # Use the lower of adaptive or configured interval
        interval = min(adaptive_interval, feed.poll_interval)

        config = FeedJobConfig(
            feed_id=feed.id,
            feed_url=feed.url,
            poll_interval=interval,
        )
        self._job_configs[feed.id] = config

        # Calculate next run time
        next_run = datetime.now(timezone.utc) + timedelta(seconds=initial_delay)

        self._scheduler.add_job(
            self._poll_feed_job,
            trigger=IntervalTrigger(
                seconds=interval,
                start_date=next_run,
            ),
            id=job_id,
            args=[feed.id],
            name=f"Poll {feed.title or feed.url}",
            next_run_time=next_run,
            misfire_grace_time=300,  # 5 minute grace period
            max_instances=1,  # Only one instance per feed at a time
        )

        logger.debug(
            f"Scheduled feed {feed.id} with interval {interval}s, "
            f"first poll in {initial_delay}s"
        )

    async def add_feed_job(self, feed: Feed) -> None:
        """Add a new feed to the scheduler.

        Args:
            feed: Feed model instance.
        """
        # Use a small random delay to avoid immediate burst
        initial_delay = random.randint(5, 30)
        await self._add_staggered_feed_job(feed, initial_delay=initial_delay)

    async def remove_feed_job(self, feed_id: str) -> None:
        """Remove a feed's polling job.

        Args:
            feed_id: Feed ID to remove.
        """
        job_id = f"feed_poll_{feed_id}"

        job = self._scheduler.get_job(job_id)
        if job:
            self._scheduler.remove_job(job_id)
            logger.info(f"Removed job for feed {feed_id}")

        if feed_id in self._job_configs:
            del self._job_configs[feed_id]

    async def update_feed_interval(self, feed_id: str, new_interval: int) -> None:
        """Update a feed's polling interval.

        Args:
            feed_id: Feed ID to update.
            new_interval: New poll interval in seconds.
        """
        job_id = f"feed_poll_{feed_id}"

        job = self._scheduler.get_job(job_id)
        if not job:
            logger.warning(f"Job not found for feed {feed_id}")
            return

        # Reschedule with new interval
        self._scheduler.reschedule_job(
            job_id,
            trigger=IntervalTrigger(seconds=new_interval),
        )

        if feed_id in self._job_configs:
            self._job_configs[feed_id].poll_interval = new_interval

        logger.info(f"Updated interval for feed {feed_id} to {new_interval}s")

    async def trigger_immediate_poll(self, feed_id: str) -> None:
        """Trigger an immediate poll for a feed.

        Args:
            feed_id: Feed ID to poll.
        """
        job_id = f"feed_poll_{feed_id}"
        job = self._scheduler.get_job(job_id)

        if job:
            # Modify next run time to now
            job.modify(next_run_time=datetime.utcnow())
            logger.info(f"Triggered immediate poll for feed {feed_id}")

    async def _poll_feed_job(self, feed_id: str) -> None:
        """Execute a feed poll job.

        Per Pitfall 27: Implements exponential backoff for failures.

        Args:
            feed_id: Feed ID to poll.
        """
        config = self._job_configs.get(feed_id)
        if not config:
            logger.warning(f"No config for feed {feed_id}")
            return

        try:
            result = await self._manager.poll_feed(feed_id)

            # Reset failure count on success
            if not result.errors or "HTTP" in result.errors[0] if result.errors else False:
                # HTTP errors still count as failures
                if result.status_code == 200 or result.status_code == 304:
                    config.consecutive_failures = 0
            else:
                config.consecutive_failures = 0

            logger.info(
                f"Poll complete for {feed_id}: "
                f"{result.new_entries} new, {result.updated_entries} updated"
            )

            # Call completion callback if set
            if self._on_poll_complete:
                self._on_poll_complete(feed_id, result)

        except FeedManagerError as e:
            logger.error(f"Poll failed for {feed_id}: {e}")

            # Exponential backoff
            config.consecutive_failures += 1
            config.last_failure = datetime.now(timezone.utc)

            backoff_interval = min(
                config.poll_interval * (2 ** config.consecutive_failures),
                86400,  # Max 24 hours
            )

            # Reschedule with backoff
            await self.update_feed_interval(feed_id, backoff_interval)

            logger.warning(
                f"Backing off feed {feed_id}: "
                f"{config.consecutive_failures} failures, "
                f"next poll in {backoff_interval}s"
            )

        except Exception as e:
            logger.exception(f"Unexpected error polling {feed_id}: {e}")

    def get_scheduler_stats(self) -> dict[str, Any]:
        """Get scheduler statistics.

        Returns:
            Dictionary with scheduler stats.
        """
        jobs = self._scheduler.get_jobs()
        return {
            "running": self._running,
            "total_jobs": len(jobs),
            "feeds": len(self._job_configs),
            "failing_feeds": sum(
                1 for c in self._job_configs.values()
                if c.consecutive_failures > 0
            ),
        }


# Module-level scheduler instance (for web app integration)
_scheduler_instance: Optional[FeedScheduler] = None


async def start_scheduler(
    feed_manager: FeedManager,
    db_session: Any,
    on_poll_complete: Optional[Callable[[str, Any], None]] = None,
) -> FeedScheduler:
    """Start the global feed scheduler.

    Args:
        feed_manager: FeedManager instance.
        db_session: Database session.
        on_poll_complete: Optional callback for poll events.

    Returns:
        FeedScheduler instance.
    """
    global _scheduler_instance

    if _scheduler_instance is not None:
        return _scheduler_instance

    _scheduler_instance = FeedScheduler(
        feed_manager,
        db_session,
        on_poll_complete=on_poll_complete,
    )
    await _scheduler_instance.start()
    return _scheduler_instance


async def stop_scheduler() -> None:
    """Stop the global feed scheduler."""
    global _scheduler_instance

    if _scheduler_instance is not None:
        await _scheduler_instance.stop()
        _scheduler_instance = None


def get_scheduler() -> Optional[FeedScheduler]:
    """Get the global scheduler instance.

    Returns:
        FeedScheduler instance or None.
    """
    return _scheduler_instance

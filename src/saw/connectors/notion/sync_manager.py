"""Notion sync orchestration and polling.

Plan 12-03: Bidirectional sync and polling.
Per NOTI-05: User can edit wiki page in SAW and sync changes back to Notion.
Per NOTI-08: System polls Notion for changes at configurable intervals.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from saw.connectors.protocol import SyncDirection
from saw.connectors.models import SyncResult
from saw.connectors.sync_engine import SyncEngine, SyncOptions, SyncMode
from saw.connectors.conflict_resolver import ConflictStrategy
from saw.connectors.notion.conflict_handler import NotionConflictHandler
from saw.connectors.notion.connector import NotionConnector


logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


@dataclass
class NotionSyncConfig:
    """Configuration for Notion sync.

    Per NOTI-08: Configurable polling interval (default: 1 hour).

    Attributes:
        poll_interval_seconds: Polling interval (default: 3600).
        batch_size: Items per batch.
        skip_large_pages: Skip content fetch for large pages.
        large_page_threshold: Block count threshold for skipping.
        enable_push: Enable push sync.
        conflict_strategy: Conflict resolution strategy.
    """

    poll_interval_seconds: int = 3600  # 1 hour per NOTI-08
    batch_size: int = 100
    skip_large_pages: bool = True
    large_page_threshold: int = 100
    enable_push: bool = True
    conflict_strategy: ConflictStrategy = ConflictStrategy.LAST_MODIFIED_WINS


class NotionSyncManager:
    """Orchestrates bidirectional sync between SAW and Notion.

    Per NOTI-05: Bidirectional sync with conflict detection.
    Per NOTI-08: Scheduled polling for changes.
    """

    MIN_POLL_INTERVAL = 60  # Minimum 60 seconds

    def __init__(
        self,
        config: NotionSyncConfig,
        connector: NotionConnector,
        sync_engine: SyncEngine,
        scheduler: Any,  # APScheduler
        session: AsyncSession,
    ) -> None:
        """Initialize sync manager.

        Args:
            config: Sync configuration.
            connector: Notion connector instance.
            sync_engine: Sync engine for orchestration.
            scheduler: APScheduler instance.
            session: SQLAlchemy async session.
        """
        self._config = config
        self._connector = connector
        self._sync_engine = sync_engine
        self._scheduler = scheduler
        self._session = session
        self._conflict_handler = NotionConflictHandler(session, config.conflict_strategy)
        self._job_id: Optional[str] = None
        self._is_syncing: bool = False

    def start_polling(self) -> None:
        """Start scheduled polling for Notion changes.

        Per NOTI-08: Poll at configured interval.
        """
        if self._job_id:
            logger.warning("Polling already started")
            return

        interval = max(self._config.poll_interval_seconds, self.MIN_POLL_INTERVAL)

        self._job_id = f"notion-sync-{self._connector._config.id}"

        self._scheduler.add_job(
            self._run_scheduled_sync,
            trigger="interval",
            seconds=interval,
            id=self._job_id,
            replace_existing=True,
        )

        logger.info(f"Started Notion polling with {interval}s interval")

    def stop_polling(self) -> None:
        """Stop scheduled polling."""
        if self._job_id:
            try:
                self._scheduler.remove_job(self._job_id)
                logger.info("Stopped Notion polling")
            except Exception as e:
                logger.warning(f"Failed to remove job: {e}")
            self._job_id = None

    async def _run_scheduled_sync(self) -> None:
        """Run scheduled sync (called by scheduler)."""
        try:
            await self.run_sync(direction=SyncDirection.BIDIRECTIONAL)
        except Exception as e:
            logger.error(f"Scheduled sync failed: {e}")

    async def run_sync(
        self,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
        force: bool = False,
    ) -> SyncResult:
        """Run sync operation.

        Args:
            direction: Sync direction.
            force: Force full sync (ignore last_sync_at).

        Returns:
            SyncResult with operation summary.
        """
        if self._is_syncing:
            logger.warning("Sync already in progress")
            return SyncResult(
                connector_id=self._connector._config.id,
                direction=direction,
                errors=["Sync already in progress"],
            )

        self._is_syncing = True
        try:
            options = SyncOptions(
                direction=direction,
                mode=SyncMode.FULL if force else SyncMode.INCREMENTAL,
                force=force,
            )

            result = await self._sync_engine.sync(
                self._connector._config.id,
                self._connector,
                options,
            )

            return result

        finally:
            self._is_syncing = False

    async def sync_pull(self, force: bool = False) -> SyncResult:
        """Pull pages from Notion and create Claims.

        Per NOTI-05: Fetch pages from selected databases.

        Args:
            force: Force full pull.

        Returns:
            SyncResult with pull summary.
        """
        return await self.run_sync(direction=SyncDirection.PULL, force=force)

    async def sync_push(self) -> SyncResult:
        """Push modified Claims to Notion.

        Per NOTI-05: Send SAW changes back to Notion.

        Returns:
            SyncResult with push summary.
        """
        if not self._config.enable_push:
            return SyncResult(
                connector_id=self._connector._config.id,
                direction=SyncDirection.PUSH,
                errors=["Push disabled in configuration"],
            )

        return await self.run_sync(direction=SyncDirection.PUSH)

    async def trigger_manual_sync(
        self,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
        force: bool = False,
    ) -> SyncResult:
        """Trigger manual sync (from API or CLI).

        Args:
            direction: Sync direction.
            force: Force full sync.

        Returns:
            SyncResult with operation summary.
        """
        logger.info(f"Manual sync triggered: direction={direction.value}, force={force}")
        return await self.run_sync(direction=direction, force=force)

    async def check_for_conflicts(
        self,
        pages: list,
    ) -> list:
        """Check pages for conflicts with SAW Claims.

        Args:
            pages: List of Notion pages.

        Returns:
            List of (page, claim, conflict_info) tuples.
        """
        conflicts = []

        for page in pages:
            # Would need to query SAW Claim by source_id
            # This is a placeholder for the full implementation
            pass

        return conflicts

    async def resolve_and_log_conflicts(
        self,
        conflicts: list,
    ) -> dict:
        """Resolve detected conflicts.

        Args:
            conflicts: List of conflict tuples.

        Returns:
            Dict mapping page_id to resolution.
        """
        resolutions = {}

        for page, claim, conflict_info in conflicts:
            resolution = self._conflict_handler.resolve(conflict_info)
            await self._conflict_handler.log_conflict(
                conflict_info,
                resolution,
                self._connector._config.id,
            )
            resolutions[conflict_info.page_id] = resolution

        return resolutions

    def get_poll_status(self) -> dict:
        """Get current polling status.

        Returns:
            Dict with polling status info.
        """
        return {
            "polling_enabled": self._job_id is not None,
            "poll_interval_seconds": self._config.poll_interval_seconds,
            "is_syncing": self._is_syncing,
        }

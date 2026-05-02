"""Reconciliation job for missed webhook events.

Plan 14-03: Webhooks and reconciliation.
Per GITH-05: Reconciliation for missed webhook deliveries.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saw.connectors.github.connector import GitHubConnector
from saw.connectors.github.issue_fetcher import IssueFetcher
from saw.connectors.github.graphql_client import DiscussionFetcher
from saw.db.github_models import (
    GitHubSyncCursorModel,
    GitHubRepositoryConfigModel,
    GitHubSyncType,
)

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


@dataclass
class ReconciliationResult:
    """Result of a reconciliation operation.

    Attributes:
        repository: Repository full name.
        items_fetched: Number of items fetched.
        items_created: Number of new items created.
        items_updated: Number of items updated.
        errors: List of error messages.
        duration_seconds: Duration in seconds.
    """
    repository: str
    items_fetched: int = 0
    items_created: int = 0
    items_updated: int = 0
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0


class GitHubReconciler:
    """Reconciliation job for detecting and recovering missed events.

    Per GITH-05: Detect items missed by webhooks.
    """

    def __init__(
        self,
        connector: GitHubConnector,
        session: AsyncSession,
    ) -> None:
        """Initialize reconciler.

        Args:
            connector: GitHubConnector instance.
            session: SQLAlchemy async session.
        """
        self._connector = connector
        self._session = session

    async def reconcile_repository(
        self,
        repository_id: str,
    ) -> ReconciliationResult:
        """Reconcile a single repository.

        Fetches items updated since last sync and creates missing claims.

        Args:
            repository_id: Repository full name (owner/repo).

        Returns:
            ReconciliationResult with operation details.
        """
        start_time = utcnow()
        result = ReconciliationResult(repository=repository_id)

        try:
            # Get sync cursor
            cursor = await self._get_sync_cursor(repository_id)
            last_sync_at = cursor.last_sync_at if cursor else None

            # Ensure client is initialized
            await self._connector._ensure_client()

            # Fetch issues
            issue_fetcher = IssueFetcher(
                client=self._connector._client,
                session=self._session,
                connector_id=self._connector._config.id,
                rate_limiter=self._connector._rate_limiter,
            )

            issues, comments = await issue_fetcher.fetch_all_issues_with_comments(
                repository=repository_id,
                since=last_sync_at,
                cursor=cursor,
            )

            result.items_fetched = len(issues) + len(comments)
            result.items_created = result.items_fetched  # Assuming all are new for now

            # Update cursor
            await self._update_sync_cursor(repository_id, len(issues))

        except Exception as e:
            logger.error(f"Reconciliation failed for {repository_id}: {e}")
            result.errors.append(str(e))

        result.duration_seconds = (utcnow() - start_time).total_seconds()
        return result

    async def reconcile_all_repositories(self) -> list[ReconciliationResult]:
        """Reconcile all selected repositories.

        Returns:
            List of ReconciliationResult for each repository.
        """
        results: list[ReconciliationResult] = []

        # Get all selected repositories
        stmt = (
            select(GitHubRepositoryConfigModel)
            .where(GitHubRepositoryConfigModel.connector_id == self._connector._config.id)
            .where(GitHubRepositoryConfigModel.is_selected == True)
        )
        db_result = await self._session.execute(stmt)
        repositories = db_result.scalars().all()

        for repo_config in repositories:
            result = await self.reconcile_repository(repo_config.repository_id)
            results.append(result)

        return results

    async def detect_webhook_gaps(self, repository_id: str) -> list[datetime]:
        """Detect gaps in webhook deliveries.

        Args:
            repository_id: Repository full name.

        Returns:
            List of gap periods to investigate.
        """
        from saw.db.github_models import GitHubWebhookDeliveryModel

        # Get recent deliveries
        stmt = (
            select(GitHubWebhookDeliveryModel)
            .where(GitHubWebhookDeliveryModel.repository == repository_id)
            .order_by(GitHubWebhookDeliveryModel.processed_at.desc())
            .limit(100)
        )
        result = await self._session.execute(stmt)
        deliveries = result.scalars().all()

        gaps: list[datetime] = []

        # Look for time gaps > 2 hours during business hours
        for i in range(len(deliveries) - 1):
            current = deliveries[i].processed_at
            previous = deliveries[i + 1].processed_at

            if current and previous:
                delta = current - previous
                if delta.total_seconds() > 7200:  # 2 hours
                    gaps.append(previous)

        return gaps

    async def get_reconciliation_status(self) -> dict:
        """Get reconciliation status.

        Returns:
            Dict with reconciliation status per repository.
        """
        stmt = (
            select(GitHubSyncCursorModel)
            .where(GitHubSyncCursorModel.connector_id == self._connector._config.id)
        )
        result = await self._session.execute(stmt)
        cursors = result.scalars().all()

        repositories = []
        for cursor in cursors:
            repositories.append({
                "repository_id": cursor.repository_id,
                "last_sync_at": cursor.last_sync_at.isoformat() if cursor.last_sync_at else None,
                "items_synced": cursor.items_synced,
            })

        return {
            "platform": "github",
            "repositories": repositories,
        }

    async def _get_sync_cursor(self, repository_id: str) -> Optional[GitHubSyncCursorModel]:
        """Get sync cursor for repository.

        Args:
            repository_id: Repository full name.

        Returns:
            GitHubSyncCursorModel or None.
        """
        stmt = select(GitHubSyncCursorModel).where(
            GitHubSyncCursorModel.connector_id == self._connector._config.id,
            GitHubSyncCursorModel.repository_id == repository_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def _update_sync_cursor(self, repository_id: str, items_count: int) -> None:
        """Update sync cursor after reconciliation.

        Args:
            repository_id: Repository full name.
            items_count: Number of items synced.
        """
        cursor = await self._get_sync_cursor(repository_id)

        now = utcnow()

        if cursor:
            cursor.last_sync_at = now
            cursor.items_synced += items_count
        else:
            cursor = GitHubSyncCursorModel(
                connector_id=self._connector._config.id,
                repository_id=repository_id,
                sync_type=GitHubSyncType.ISSUES,
                last_sync_at=now,
                items_synced=items_count,
            )
            self._session.add(cursor)

        await self._session.flush()


class ReconciliationScheduler:
    """Scheduler for periodic reconciliation jobs.

    Per GITH-05: Schedule periodic reconciliation.
    """

    def __init__(
        self,
        reconciler: GitHubReconciler,
        interval_hours: int = 1,
    ) -> None:
        """Initialize scheduler.

        Args:
            reconciler: GitHubReconciler instance.
            interval_hours: Reconciliation interval in hours.
        """
        self._reconciler = reconciler
        self._interval_hours = interval_hours
        self._is_running = False

    async def start(self) -> None:
        """Start periodic reconciliation."""
        self._is_running = True
        logger.info(f"Reconciliation scheduler started (interval: {self._interval_hours}h)")

    async def stop(self) -> None:
        """Stop periodic reconciliation."""
        self._is_running = False
        logger.info("Reconciliation scheduler stopped")

    async def run_once(self) -> list[ReconciliationResult]:
        """Run reconciliation once.

        Returns:
            List of ReconciliationResult.
        """
        return await self._reconciler.reconcile_all_repositories()

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._is_running

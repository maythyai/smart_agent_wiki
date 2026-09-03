"""Audit logging for sync operations.

Plan 11-01: Sync engine core with conflict detection.
Per SYNC-03: All sync operations logged with timestamp, direction, item count.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saw.db.sync_models import SyncLogModel
from saw.domain.utils import utcnow  # noqa: F401


@dataclass
class SyncLogEntry:
    """In-memory representation of a sync log entry.

    Attributes:
        connector_id: Connector identifier.
        platform: Platform name.
        direction: Sync direction.
        status: Sync outcome.
        items: Item counts (pulled, pushed, skipped).
        started_at: When sync started.
        completed_at: When sync completed.
        error_message: Error details if any.
        metadata: Additional metadata.
    """

    connector_id: str
    platform: str
    direction: str
    status: str
    items: dict[str, int] = field(default_factory=dict)
    started_at: datetime = field(default_factory=utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SyncLogger:
    """Audit logger for sync operations.

    Per SYNC-03: All sync operations logged with timestamp, direction, item count.
    Per ERRO-04: Error details preserved for data integrity tracking.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize sync logger.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self._session = session

    async def log_sync(
        self,
        connector_id: str,
        platform: str,
        direction: str,
        status: str,
        items: dict[str, int],
        error_message: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> SyncLogModel:
        """Log a sync operation.

        Per SYNC-03: Creates SyncLogModel with timestamp, direction, platform.

        Args:
            connector_id: Connector identifier.
            platform: Platform name.
            direction: Sync direction (pull, push, bidirectional).
            status: Sync outcome (success, partial, failed).
            items: Dict with items_pulled, items_pushed, items_skipped counts.
            error_message: Error details if status is failed/partial.
            metadata: Additional JSON metadata.
            started_at: When sync started (defaults to now).
            completed_at: When sync completed (defaults to now).

        Returns:
            Created SyncLogModel instance.
        """
        log = SyncLogModel(
            connector_id=connector_id,
            platform=platform,
            direction=direction,
            status=status,
            items_pulled=items.get("pulled", 0),
            items_pushed=items.get("pushed", 0),
            items_skipped=items.get("skipped", 0),
            started_at=started_at or utcnow(),
            completed_at=completed_at or utcnow(),
            error_message=error_message,
            extra_data=metadata or {},
        )
        self._session.add(log)
        await self._session.flush()
        return log

    async def log_error(
        self,
        connector_id: str,
        platform: str,
        error: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> SyncLogModel:
        """Log a sync error.

        Per ERRO-04: Records error details with ERROR status.

        Args:
            connector_id: Connector identifier.
            platform: Platform name.
            error: Error message.
            metadata: Additional error metadata.

        Returns:
            Created SyncLogModel instance.
        """
        return await self.log_sync(
            connector_id=connector_id,
            platform=platform,
            direction="unknown",
            status="failed",
            items={},
            error_message=error,
            metadata=metadata or {},
        )

    async def get_recent_logs(
        self,
        platform: Optional[str] = None,
        connector_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[SyncLogModel]:
        """Get recent sync logs, optionally filtered.

        Args:
            platform: Filter by platform (optional).
            connector_id: Filter by connector (optional).
            limit: Maximum number of logs to return.

        Returns:
            List of SyncLogModel instances, newest first.
        """
        stmt = select(SyncLogModel).order_by(SyncLogModel.started_at.desc())

        if platform:
            stmt = stmt.where(SyncLogModel.platform == platform)
        if connector_id:
            stmt = stmt.where(SyncLogModel.connector_id == connector_id)

        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_sync_summary(
        self,
        connector_id: str,
        hours: int = 24,
    ) -> dict[str, Any]:
        """Get sync summary for a connector.

        Args:
            connector_id: Connector identifier.
            hours: Time window in hours.

        Returns:
            Dict with items_synced, error_count, last_sync_at, etc.
        """
        from datetime import timedelta

        cutoff = utcnow() - timedelta(hours=hours)

        stmt = (
            select(SyncLogModel)
            .where(SyncLogModel.connector_id == connector_id)
            .where(SyncLogModel.started_at >= cutoff)
            .order_by(SyncLogModel.started_at.desc())
        )
        result = await self._session.execute(stmt)
        logs = list(result.scalars().all())

        total_pulled = sum(log.items_pulled for log in logs)
        total_pushed = sum(log.items_pushed for log in logs)
        error_count = sum(1 for log in logs if log.status == "failed")

        last_sync_at = None
        for log in logs:
            if log.status in ("success", "partial") and log.completed_at:
                last_sync_at = log.completed_at
                break

        return {
            "connector_id": connector_id,
            "items_synced": total_pulled + total_pushed,
            "items_pulled": total_pulled,
            "items_pushed": total_pushed,
            "error_count": error_count,
            "total_operations": len(logs),
            "last_sync_at": last_sync_at,
            "hours": hours,
        }

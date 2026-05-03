"""Sync status tracking per connector.

Plan 11-01: Sync engine core with conflict detection.
Per SYNC-01: Unified sync status dashboard foundation.
Per SYNC-02: Track last_sync_at per connector for conflict detection.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saw.db.sync_models import SyncStateModel
from saw.connectors.models import SyncResult


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class SyncState(enum.Enum):
    """Sync state for a connector.

    Used to prevent concurrent syncs and track status.
    """
    IDLE = "idle"
    SYNCING = "syncing"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class SyncStatus:
    """Current sync status for a connector.

    Attributes:
        connector_id: Unique connector identifier.
        platform: Platform name (slack, notion, github, etc.).
        state: Current sync state.
        last_sync_at: Last successful sync timestamp.
        last_success_at: Last sync that completed without errors.
        last_error: Last error message.
        items_pending: Items pending in write queue (backpressure).
        items_synced: Items synced in current/last sync operation.
        items_total: Total items to sync (if known).
        completion_percent: Progress percentage (0-100).
        sync_cursor: Pagination cursor for incremental sync.
    """

    connector_id: str
    platform: str
    state: SyncState = SyncState.IDLE
    last_sync_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error: Optional[str] = None
    items_pending: int = 0
    items_synced: int = 0
    items_total: int = 0
    completion_percent: float = 0.0
    sync_cursor: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "connector_id": self.connector_id,
            "platform": self.platform,
            "state": self.state.value,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_error": self.last_error,
            "items_pending": self.items_pending,
            "items_synced": self.items_synced,
            "items_total": self.items_total,
            "completion_percent": self.completion_percent,
            "sync_cursor": self.sync_cursor,
        }


class SyncStatusTracker:
    """Tracks sync status per connector.

    Per SYNC-02: Track last_sync_at per connector for conflict detection.
    Per SYNC-01: Foundation for unified sync status dashboard.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize status tracker.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self._session = session
        self._in_memory_status: dict[str, SyncStatus] = {}

    async def get_status(self, connector_id: str) -> SyncStatus:
        """Get sync status for a connector.

        Args:
            connector_id: Connector identifier.

        Returns:
            SyncStatus for the connector.
        """
        # Check in-memory cache first
        if connector_id in self._in_memory_status:
            return self._in_memory_status[connector_id]

        # Check database
        stmt = select(SyncStateModel).where(SyncStateModel.connector_id == connector_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            status = SyncStatus(
                connector_id=model.connector_id,
                platform=model.platform,
                state=SyncState.ERROR if model.last_error else SyncState.IDLE,
                last_sync_at=model.last_sync_at,
                last_success_at=model.last_sync_at,  # Same as last_sync for now
                last_error=model.last_error,
                sync_cursor=model.last_sync_cursor,
            )
        else:
            # No record yet - return default status
            status = SyncStatus(
                connector_id=connector_id,
                platform="unknown",
                state=SyncState.IDLE,
            )

        self._in_memory_status[connector_id] = status
        return status

    async def get_all_statuses(self) -> list[SyncStatus]:
        """Get sync status for all connectors.

        Returns:
            List of SyncStatus for all connectors.
        """
        stmt = select(SyncStateModel)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        statuses = []
        for model in models:
            status = SyncStatus(
                connector_id=model.connector_id,
                platform=model.platform,
                state=SyncState.ERROR if model.last_error else SyncState.IDLE,
                last_sync_at=model.last_sync_at,
                last_success_at=model.last_sync_at,
                last_error=model.last_error,
                sync_cursor=model.last_sync_cursor,
            )
            statuses.append(status)
            self._in_memory_status[model.connector_id] = status

        return statuses

    async def mark_sync_started(self, connector_id: str, platform: str = "unknown") -> None:
        """Mark a sync as started.

        Updates state to SYNCING and clears any previous error.

        Args:
            connector_id: Connector identifier.
            platform: Platform name (for new records).
        """
        stmt = select(SyncStateModel).where(SyncStateModel.connector_id == connector_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.sync_in_progress = True
            model.updated_at = utcnow()
        else:
            model = SyncStateModel(
                connector_id=connector_id,
                platform=platform,
                sync_in_progress=True,
            )
            self._session.add(model)

        # Update in-memory status
        if connector_id in self._in_memory_status:
            self._in_memory_status[connector_id].state = SyncState.SYNCING
        else:
            self._in_memory_status[connector_id] = SyncStatus(
                connector_id=connector_id,
                platform=platform,
                state=SyncState.SYNCING,
            )

        await self._session.flush()

    async def mark_sync_completed(
        self,
        connector_id: str,
        result: SyncResult,
        cursor: Optional[str] = None,
    ) -> None:
        """Mark a sync as completed.

        Updates last_sync_at and item counts.

        Args:
            connector_id: Connector identifier.
            result: SyncResult from the sync operation.
            cursor: Pagination cursor for incremental sync.
        """
        stmt = select(SyncStateModel).where(SyncStateModel.connector_id == connector_id)
        db_result = await self._session.execute(stmt)
        model = db_result.scalar_one_or_none()

        now = utcnow()

        if model:
            model.sync_in_progress = False
            model.last_sync_at = now
            model.last_sync_cursor = cursor
            model.items_synced_total += result.pulled_count + result.pushed_count
            model.updated_at = now

            if not result.success:
                model.last_error = "; ".join(result.errors) if result.errors else "Unknown error"
                model.last_error_at = now
            else:
                model.last_error = None
                model.last_error_at = None
        else:
            model = SyncStateModel(
                connector_id=connector_id,
                platform="unknown",
                sync_in_progress=False,
                last_sync_at=now,
                last_sync_cursor=cursor,
            )
            self._session.add(model)

        # Update in-memory status
        if connector_id in self._in_memory_status:
            status = self._in_memory_status[connector_id]
            status.state = SyncState.IDLE if result.success else SyncState.ERROR
            status.last_sync_at = now
            status.last_success_at = now if result.success else status.last_success_at
            status.sync_cursor = cursor
            if not result.success and result.errors:
                status.last_error = "; ".join(result.errors)

        await self._session.flush()

    async def mark_error(self, connector_id: str, error: str) -> None:
        """Mark a connector as having an error.

        Args:
            connector_id: Connector identifier.
            error: Error message.
        """
        stmt = select(SyncStateModel).where(SyncStateModel.connector_id == connector_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        now = utcnow()

        if model:
            model.sync_in_progress = False
            model.last_error = error
            model.last_error_at = now
            model.updated_at = now
        else:
            model = SyncStateModel(
                connector_id=connector_id,
                platform="unknown",
                sync_in_progress=False,
                last_error=error,
                last_error_at=now,
            )
            self._session.add(model)

        # Update in-memory status
        if connector_id in self._in_memory_status:
            self._in_memory_status[connector_id].state = SyncState.ERROR
            self._in_memory_status[connector_id].last_error = error
        else:
            self._in_memory_status[connector_id] = SyncStatus(
                connector_id=connector_id,
                platform="unknown",
                state=SyncState.ERROR,
                last_error=error,
            )

        await self._session.flush()

    async def set_cursor(self, connector_id: str, cursor: str) -> None:
        """Set the sync cursor for incremental sync.

        Args:
            connector_id: Connector identifier.
            cursor: Pagination cursor.
        """
        stmt = select(SyncStateModel).where(SyncStateModel.connector_id == connector_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.last_sync_cursor = cursor
            model.updated_at = utcnow()

        # Update in-memory status
        if connector_id in self._in_memory_status:
            self._in_memory_status[connector_id].sync_cursor = cursor

        await self._session.flush()

    async def set_items_pending(self, connector_id: str, count: int) -> None:
        """Set the pending items count (for backpressure monitoring).

        Args:
            connector_id: Connector identifier.
            count: Number of pending items in write queue.
        """
        if connector_id in self._in_memory_status:
            self._in_memory_status[connector_id].items_pending = count

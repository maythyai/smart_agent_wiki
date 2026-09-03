"""Conflict detection and resolution for bidirectional sync.

Plan 11-01: Sync engine core with conflict detection.
Per SYNC-02: Detect sync loops via source metadata tracking.
Per ERRO-04: Record conflicts for data integrity.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saw.connectors.protocol import ConnectorItem
from saw.db.sync_models import ConflictRecordModel
from saw.domain.utils import utcnow  # noqa: F401


class ConflictStrategy(enum.Enum):
    """Strategy for resolving sync conflicts.

    - LAST_MODIFIED_WINS: Compare timestamps, newer wins
    - PLATFORM_WINS: Always prefer platform version
    - SAW_WINS: Always prefer SAW version
    - MANUAL: Record conflict for human resolution
    """
    LAST_MODIFIED_WINS = "last_modified_wins"
    PLATFORM_WINS = "platform_wins"
    SAW_WINS = "saw_wins"
    MANUAL = "manual"


@dataclass
class ConflictInfo:
    """Information about a detected conflict.

    Attributes:
        platform_item_id: Platform's item identifier.
        saw_claim_id: SAW's claim identifier.
        platform_modified_at: When platform item was last modified.
        saw_modified_at: When SAW claim was last modified.
        resolution: Strategy used to resolve (or None if manual).
    """

    platform_item_id: str
    saw_claim_id: str
    platform_modified_at: datetime
    saw_modified_at: datetime
    resolution: Optional[ConflictStrategy] = None


@dataclass
class ConflictResult:
    """Result of conflict detection.

    Attributes:
        has_conflict: Whether a conflict was detected.
        winner: Which side won ("platform" or "saw").
        conflict_info: Detailed conflict information if detected.
    """

    has_conflict: bool = False
    winner: str = ""
    conflict_info: Optional[ConflictInfo] = None


class ConflictResolver:
    """Detects and resolves sync conflicts.

    Per SYNC-02: Detect conflicts when both sides modified after last_sync_at.
    Per ERRO-04: Record conflicts for data integrity tracking.
    """

    def __init__(
        self,
        session: AsyncSession,
        strategy: ConflictStrategy = ConflictStrategy.LAST_MODIFIED_WINS,
    ) -> None:
        """Initialize conflict resolver.

        Args:
            session: SQLAlchemy async session for database operations.
            strategy: Default resolution strategy.
        """
        self._session = session
        self._strategy = strategy

    def detect_conflict(
        self,
        platform_item: ConnectorItem,
        saw_claim: dict,
        last_sync_at: Optional[datetime],
    ) -> ConflictResult:
        """Detect if there's a conflict between platform and SAW versions.

        Per SYNC-02: Conflict when both modified after last_sync_at.

        Args:
            platform_item: Item from the platform.
            saw_claim: SAW claim dict (from Claim model or database).
            last_sync_at: Timestamp of last successful sync.
                If None (first sync), no conflict possible.

        Returns:
            ConflictResult indicating if conflict exists and who wins.
        """
        if last_sync_at is None:
            # First sync - no conflict possible
            return ConflictResult(has_conflict=False, winner="platform")

        platform_modified = platform_item.updated_at
        saw_modified = saw_claim.get("updated_at") or saw_claim.get("created_at")

        if saw_modified is None:
            # SAW item has no timestamp - platform wins
            return ConflictResult(has_conflict=False, winner="platform")

        # Check if both modified after last sync
        platform_changed = platform_modified and platform_modified > last_sync_at
        saw_changed = saw_modified > last_sync_at

        if platform_changed and saw_changed:
            # Both sides modified - conflict!
            conflict_info = ConflictInfo(
                platform_item_id=platform_item.id,
                saw_claim_id=saw_claim.get("id") or saw_claim.get("uuid", ""),
                platform_modified_at=platform_modified,
                saw_modified_at=saw_modified,
            )
            return ConflictResult(has_conflict=True, conflict_info=conflict_info)

        # No conflict - whoever changed wins
        if platform_changed:
            return ConflictResult(has_conflict=False, winner="platform")
        elif saw_changed:
            return ConflictResult(has_conflict=False, winner="saw")
        else:
            # Neither changed after last sync
            # Prefer platform to avoid unnecessary writes
            return ConflictResult(has_conflict=False, winner="platform")

    def resolve(self, conflict: ConflictInfo) -> str:
        """Resolve a conflict using the configured strategy.

        Args:
            conflict: Conflict information.

        Returns:
            "platform" or "saw" indicating the winner.
        """
        if self._strategy == ConflictStrategy.PLATFORM_WINS:
            return "platform"
        elif self._strategy == ConflictStrategy.SAW_WINS:
            return "saw"
        elif self._strategy == ConflictStrategy.MANUAL:
            return "manual"
        else:
            # LAST_MODIFIED_WINS - compare timestamps
            if conflict.platform_modified_at >= conflict.saw_modified_at:
                return "platform"
            else:
                return "saw"

    async def record_conflict(
        self,
        conflict: ConflictInfo,
        resolution: str,
        connector_id: str,
    ) -> ConflictRecordModel:
        """Record a conflict in the database.

        Per ERRO-04: Record conflicts for data integrity tracking.

        Args:
            conflict: Conflict information.
            resolution: How it was resolved (platform_wins, saw_wins, manual).
            connector_id: Connector that detected the conflict.

        Returns:
            Created ConflictRecordModel instance.
        """
        record = ConflictRecordModel(
            connector_id=connector_id,
            platform_item_id=conflict.platform_item_id,
            saw_claim_id=conflict.saw_claim_id,
            platform_modified_at=conflict.platform_modified_at,
            saw_modified_at=conflict.saw_modified_at,
            resolution=resolution,
            resolved_at=utcnow() if resolution != "manual" else None,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_unresolved_conflicts(
        self,
        connector_id: Optional[str] = None,
    ) -> list[ConflictRecordModel]:
        """Get unresolved (manual) conflicts.

        Args:
            connector_id: Filter by connector (optional).

        Returns:
            List of unresolved ConflictRecordModel instances.
        """
        stmt = (
            select(ConflictRecordModel)
            .where(ConflictRecordModel.resolution == "manual")
            .where(ConflictRecordModel.resolved_at.is_(None))
            .order_by(ConflictRecordModel.created_at.desc())
        )

        if connector_id:
            stmt = stmt.where(ConflictRecordModel.connector_id == connector_id)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def resolve_manual_conflict(
        self,
        conflict_id: int,
        resolution: str,
    ) -> ConflictRecordModel:
        """Manually resolve a conflict.

        Args:
            conflict_id: Conflict record ID.
            resolution: Resolution choice (platform_wins, saw_wins).

        Returns:
            Updated ConflictRecordModel instance.

        Raises:
            ValueError: If conflict not found or already resolved.
        """
        stmt = select(ConflictRecordModel).where(ConflictRecordModel.id == conflict_id)
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            raise ValueError(f"Conflict {conflict_id} not found")
        if record.resolved_at is not None:
            raise ValueError(f"Conflict {conflict_id} already resolved")

        record.resolution = resolution
        record.resolved_at = utcnow()

        await self._session.flush()
        return record

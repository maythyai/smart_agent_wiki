"""Per-connector health status tracking with alerting.

Plan 11-02: Backpressure, retry, and health status.
Per ERRO-02: Persistent failures trigger alerts (connector_unhealthy event).
Per ERRO-03: Per-connector health status visible via API.
Per IM-07: Graceful degradation when platforms unavailable.
"""
from __future__ import annotations

import asyncio
import enum
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saw.db.sync_models import SyncStateModel


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


logger = logging.getLogger(__name__)


class HealthStatus(enum.Enum):
    """Three-tier health status for connectors.

    - HEALTHY: All syncs successful
    - DEGRADED: Some failures but operational
    - UNHEALTHY: Persistent failures, sync paused
    """
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthThresholds:
    """Thresholds for health status transitions.

    Attributes:
        degraded_after_failures: Failures before degraded status.
        unhealthy_after_failures: Failures before unhealthy status.
        healthy_after_successes: Consecutive successes to recover to healthy.
    """

    degraded_after_failures: int = 2
    unhealthy_after_failures: int = 5
    healthy_after_successes: int = 3


@dataclass
class ConnectorHealth:
    """Health status for a single connector.

    Attributes:
        connector_id: Connector identifier.
        platform: Platform name.
        status: Current health status.
        last_success_at: Last successful sync timestamp.
        last_failure_at: Last failure timestamp.
        consecutive_failures: Current failure streak.
        consecutive_successes: Current success streak.
        last_error: Last error message.
        total_syncs: Total sync operations.
        total_failures: Total failed operations.
    """

    connector_id: str
    platform: str
    status: HealthStatus = HealthStatus.HEALTHY
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_error: Optional[str] = None
    total_syncs: int = 0
    total_failures: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "connector_id": self.connector_id,
            "platform": self.platform,
            "status": self.status.value,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "last_error": self.last_error,
            "total_syncs": self.total_syncs,
            "total_failures": self.total_failures,
        }


@dataclass
class HealthEvent:
    """Event for health status changes.

    Attributes:
        connector_id: Connector identifier.
        event_type: Type of event (status_change, failure, recovery).
        old_status: Previous health status.
        new_status: New health status.
        timestamp: When event occurred.
        details: Additional event details.
    """

    connector_id: str
    event_type: str  # status_change, failure, recovery
    old_status: Optional[HealthStatus] = None
    new_status: HealthStatus = HealthStatus.HEALTHY
    timestamp: datetime = field(default_factory=utcnow)
    details: dict = field(default_factory=dict)


class HealthMonitor:
    """Tracks per-connector health status with alerting.

    Per ERRO-02: Persistent failures trigger alerts.
    Per ERRO-03: Per-connector health status visible.
    Per IM-07: Graceful degradation when platforms unavailable.
    """

    def __init__(
        self,
        session: AsyncSession,
        thresholds: Optional[HealthThresholds] = None,
    ) -> None:
        """Initialize health monitor.

        Args:
            session: SQLAlchemy async session.
            thresholds: Health transition thresholds.
        """
        self._session = session
        self._thresholds = thresholds or HealthThresholds()
        self._health_cache: dict[str, ConnectorHealth] = {}

    async def record_success(
        self,
        connector_id: str,
        platform: str,
    ) -> ConnectorHealth:
        """Record a successful sync operation.

        Updates health status, possibly recovering from degraded/unhealthy.

        Args:
            connector_id: Connector identifier.
            platform: Platform name.

        Returns:
            Updated ConnectorHealth.
        """
        health = await self._get_or_create_health(connector_id, platform)
        now = utcnow()

        # Update counters
        health.consecutive_failures = 0
        health.consecutive_successes += 1
        health.total_syncs += 1
        health.last_success_at = now

        # Check for status transition (recovery)
        old_status = health.status
        if health.status != HealthStatus.HEALTHY:
            if health.consecutive_successes >= self._thresholds.healthy_after_successes:
                health.status = HealthStatus.HEALTHY
                await self._emit_event(HealthEvent(
                    connector_id=connector_id,
                    event_type="recovery",
                    old_status=old_status,
                    new_status=HealthStatus.HEALTHY,
                    details={"consecutive_successes": health.consecutive_successes},
                ), health)

        self._health_cache[connector_id] = health
        return health

    async def record_failure(
        self,
        connector_id: str,
        platform: str,
        error: str,
    ) -> ConnectorHealth:
        """Record a failed sync operation.

        Updates health status, possibly degrading to unhealthy.

        Per ERRO-02: Emits connector_unhealthy event when status changes to UNHEALTHY.

        Args:
            connector_id: Connector identifier.
            platform: Platform name.
            error: Error message.

        Returns:
            Updated ConnectorHealth.
        """
        health = await self._get_or_create_health(connector_id, platform)
        now = utcnow()

        # Update counters
        health.consecutive_successes = 0
        health.consecutive_failures += 1
        health.total_syncs += 1
        health.total_failures += 1
        health.last_failure_at = now
        health.last_error = error

        # Check for status transition (degradation)
        old_status = health.status
        new_status = self._should_transition(health, success=False)

        if new_status != old_status:
            health.status = new_status
            await self._emit_event(HealthEvent(
                connector_id=connector_id,
                event_type="status_change",
                old_status=old_status,
                new_status=new_status,
                details={"error": error, "consecutive_failures": health.consecutive_failures},
            ), health)

            if new_status == HealthStatus.UNHEALTHY:
                logger.error(
                    f"connector_unhealthy: {connector_id} ({platform}) - {error}"
                )

        self._health_cache[connector_id] = health
        return health

    async def get_health(self, connector_id: str) -> ConnectorHealth:
        """Get health status for a connector.

        Args:
            connector_id: Connector identifier.

        Returns:
            ConnectorHealth instance.
        """
        if connector_id in self._health_cache:
            return self._health_cache[connector_id]

        # Check database
        stmt = select(SyncStateModel).where(SyncStateModel.connector_id == connector_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            health = ConnectorHealth(
                connector_id=model.connector_id,
                platform=model.platform,
                status=HealthStatus.UNHEALTHY if model.last_error else HealthStatus.HEALTHY,
                last_error=model.last_error,
            )
        else:
            health = ConnectorHealth(
                connector_id=connector_id,
                platform="unknown",
            )

        self._health_cache[connector_id] = health
        return health

    async def get_all_health(self) -> list[ConnectorHealth]:
        """Get health status for all connectors.

        Returns:
            List of ConnectorHealth instances.
        """
        stmt = select(SyncStateModel)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        for model in models:
            if model.connector_id not in self._health_cache:
                health = ConnectorHealth(
                    connector_id=model.connector_id,
                    platform=model.platform,
                    status=HealthStatus.UNHEALTHY if model.last_error else HealthStatus.HEALTHY,
                    last_error=model.last_error,
                )
                self._health_cache[model.connector_id] = health

        return list(self._health_cache.values())

    async def get_system_health(self) -> dict[str, Any]:
        """Get overall system health.

        Returns:
            Dict with overall status and connector breakdown.
        """
        all_health = await self.get_all_health()

        if not all_health:
            return {
                "status": "healthy",
                "connectors": [],
                "healthy_count": 0,
                "degraded_count": 0,
                "unhealthy_count": 0,
            }

        counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 0,
            HealthStatus.UNHEALTHY: 0,
        }

        for h in all_health:
            counts[h.status] += 1

        # Determine overall status
        if counts[HealthStatus.UNHEALTHY] > 0:
            overall = "unhealthy"
        elif counts[HealthStatus.DEGRADED] > 0:
            overall = "degraded"
        else:
            overall = "healthy"

        return {
            "status": overall,
            "connectors": [h.to_dict() for h in all_health],
            "healthy_count": counts[HealthStatus.HEALTHY],
            "degraded_count": counts[HealthStatus.DEGRADED],
            "unhealthy_count": counts[HealthStatus.UNHEALTHY],
        }

    def _should_transition(
        self,
        health: ConnectorHealth,
        success: bool,
    ) -> HealthStatus:
        """Determine if status should transition.

        Args:
            health: Current health state.
            success: Whether last operation was success.

        Returns:
            New HealthStatus.
        """
        if success:
            # Recovery logic handled in record_success
            return health.status

        # Failure - check thresholds
        if health.consecutive_failures >= self._thresholds.unhealthy_after_failures:
            return HealthStatus.UNHEALTHY
        elif health.consecutive_failures >= self._thresholds.degraded_after_failures:
            return HealthStatus.DEGRADED

        return health.status

    async def _get_or_create_health(
        self,
        connector_id: str,
        platform: str,
    ) -> ConnectorHealth:
        """Get or create health record.

        Args:
            connector_id: Connector identifier.
            platform: Platform name.

        Returns:
            ConnectorHealth instance.
        """
        if connector_id in self._health_cache:
            return self._health_cache[connector_id]

        health = ConnectorHealth(
            connector_id=connector_id,
            platform=platform,
        )
        self._health_cache[connector_id] = health
        return health

    async def _emit_event(self, event: HealthEvent, health: Optional[ConnectorHealth] = None) -> None:
        """Emit health event for external alerting.

        Args:
            event: Health event to emit.
            health: Optional ConnectorHealth for WebSocket broadcast.
        """
        logger.info(
            f"health_event: {event.event_type} for {event.connector_id} - "
            f"{event.old_status.value if event.old_status else 'none'} -> {event.new_status.value}"
        )

        # Broadcast health change via WebSocket (per DASH-02)
        if health is not None and event.event_type in ("status_change", "recovery"):
            try:
                from saw.api.integrations_ws import broadcast_health_change
                await broadcast_health_change(health.platform, health)
            except Exception as e:
                logger.warning(f"Failed to broadcast health change: {e}")

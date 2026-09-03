"""Health status API endpoints.

Plan 11-02: Backpressure, retry, and health status.
Per ERRO-03: Per-connector health status visible via API.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from saw.connectors.health_monitor import HealthMonitor


router = APIRouter(prefix="/api/v1/health", tags=["health"])


# Pydantic models for API

class HealthStatusResponse(BaseModel):
    """Health status for a single connector."""
    connector_id: str
    platform: str
    status: str
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_error: Optional[str] = None
    total_syncs: int = 0
    total_failures: int = 0


class SystemHealthResponse(BaseModel):
    """Overall system health."""
    status: str
    connectors: list[HealthStatusResponse]
    healthy_count: int
    degraded_count: int
    unhealthy_count: int


class BriefHealthResponse(BaseModel):
    """Brief health status for monitoring."""
    status: str
    healthy_count: int
    degraded_count: int
    unhealthy_count: int


# Dependency to get health monitor

async def get_health_monitor():
    """Yield a HealthMonitor backed by the shared async session.

    Uses ``saw.db.session.get_session`` so the schema is bootstrapped on
    first use (the ``sync_state`` / connector tables are created if missing)
    and the session stays open for the duration of the request. Previously
    this constructed the monitor inside an ``async with`` that closed the
    session before the handler could query it.
    """
    try:
        from saw.db.session import get_session

        async with get_session() as session:
            yield HealthMonitor(session)
    except (ImportError, ModuleNotFoundError):
        raise HTTPException(
            status_code=503,
            detail="Health monitor unavailable (aiosqlite not installed)",
        )
    except Exception as e:  # pragma: no cover — degrade to 503, never 500-crash
        raise HTTPException(
            status_code=503,
            detail=f"Health monitor unavailable: {e}",
        )


# API Endpoints

@router.get("", response_model=SystemHealthResponse)
async def get_system_health(
    monitor: HealthMonitor = Depends(get_health_monitor),
) -> dict[str, Any]:
    """Get overall system health.

    Returns health status for all connectors and overall system status.
    """
    return await monitor.get_system_health()


@router.get("/status", response_model=BriefHealthResponse)
async def get_brief_status(
    monitor: HealthMonitor = Depends(get_health_monitor),
) -> dict[str, Any]:
    """Get brief health status for monitoring.

    Returns counts only, suitable for dashboards.
    """
    system_health = await monitor.get_system_health()
    return {
        "status": system_health["status"],
        "healthy_count": system_health["healthy_count"],
        "degraded_count": system_health["degraded_count"],
        "unhealthy_count": system_health["unhealthy_count"],
    }


@router.get("/{connector_id}", response_model=HealthStatusResponse)
async def get_connector_health(
    connector_id: str,
    monitor: HealthMonitor = Depends(get_health_monitor),
) -> dict[str, Any]:
    """Get health status for a specific connector.

    Args:
        connector_id: Connector identifier.

    Returns:
        Health status for the connector.

    Raises:
        HTTPException: If connector not found.
    """
    health = await monitor.get_health(connector_id)
    return health.to_dict()

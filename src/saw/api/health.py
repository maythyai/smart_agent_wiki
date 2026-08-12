"""Health status API endpoints.

Plan 11-02: Backpressure, retry, and health status.
Per ERRO-03: Per-connector health status visible via API.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from saw.db.config import get_session_factory
from saw.connectors.health_monitor import HealthMonitor, HealthStatus


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

async def get_health_monitor() -> HealthMonitor:
    """Get HealthMonitor instance.

    Note: In production, this would use dependency injection.
    For now, creates a new instance with session.
    """
    try:
        from saw.db.config import get_async_engine
        from sqlalchemy.ext.asyncio import async_sessionmaker

        engine = get_async_engine()
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with async_session() as session:
            return HealthMonitor(session)
    except (ImportError, ModuleNotFoundError):
        raise HTTPException(
            status_code=503,
            detail="Health monitor unavailable (aiosqlite not installed)",
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

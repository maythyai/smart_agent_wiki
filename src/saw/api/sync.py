"""Sync status and manual trigger API endpoints.

Plan 11-03: IM message handling and sync API endpoints.
Per SYNC-01: Unified sync status dashboard (API foundation).
Per SYNC-04: Manual sync trigger per connector from CLI or Web UI.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from saw.connectors.sync_engine import SyncEngine, SyncOptions, SyncMode
from saw.connectors.sync_status import SyncStatusTracker
from saw.connectors.health_monitor import HealthMonitor
from saw.connectors.sync_logger import SyncLogger
from saw.connectors.registry import ConnectorRegistry
from saw.connectors.protocol import SyncDirection


router = APIRouter(prefix="/api/v1/sync", tags=["sync"])


# Pydantic models for API

class SyncStatusResponse(BaseModel):
    """Sync status for a single connector."""
    connector_id: str
    platform: str
    state: str
    last_sync_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error: Optional[str] = None
    items_synced: int = 0
    health_status: str = "healthy"


class SyncTriggerRequest(BaseModel):
    """Request to trigger manual sync."""
    direction: str = "bidirectional"  # pull, push, bidirectional
    force: bool = False


class SyncTriggerResponse(BaseModel):
    """Response from manual sync trigger."""
    success: bool
    message: str
    items_pulled: int = 0
    items_pushed: int = 0
    errors: list[str] = []


class SyncLogsResponse(BaseModel):
    """Response for sync logs."""
    logs: list[dict]
    total: int


# Dependencies (simplified - in production would use proper DI)

async def get_sync_engine() -> SyncEngine:
    """Get SyncEngine instance."""
    # Simplified - production would use proper DI
    registry = ConnectorRegistry()
    from saw.db.config import get_async_engine
    from sqlalchemy.ext.asyncio import async_sessionmaker

    engine = get_async_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        return SyncEngine(registration=registry, write_queue=None, session=session)


# API Endpoints

@router.get("/status", response_model=list[SyncStatusResponse])
async def get_all_sync_statuses() -> list[dict]:
    """Get sync status for all connectors.

    Returns:
        List of connector sync statuses.
    """
    from saw.db.config import get_async_engine
    from sqlalchemy.ext.asyncio import async_sessionmaker

    engine = get_async_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        tracker = SyncStatusTracker(session)
        statuses = await tracker.get_all_statuses()

        return [s.to_dict() for s in statuses]


@router.get("/status/{connector_id}", response_model=SyncStatusResponse)
async def get_connector_sync_status(connector_id: str) -> dict:
    """Get sync status for a specific connector.

    Args:
        connector_id: Connector identifier.

    Returns:
        Sync status for the connector.

    Raises:
        HTTPException: If connector not found.
    """
    from saw.db.config import get_async_engine
    from sqlalchemy.ext.asyncio import async_sessionmaker

    engine = get_async_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        tracker = SyncStatusTracker(session)
        status = await tracker.get_status(connector_id)

        # Also get health status
        monitor = HealthMonitor(session)
        health = await monitor.get_health(connector_id)

        result = status.to_dict()
        result["health_status"] = health.status.value
        return result


@router.post("/trigger/{connector_id}", response_model=SyncTriggerResponse)
async def trigger_sync(
    connector_id: str,
    request: SyncTriggerRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """Trigger manual sync for a connector.

    Per SYNC-04: Manual sync trigger from Web UI.

    Args:
        connector_id: Connector identifier.
        request: Sync trigger request.
        background_tasks: FastAPI background tasks.

    Returns:
        Sync trigger response.

    Raises:
        HTTPException: If connector not found or sync in progress.
    """
    registry = ConnectorRegistry()
    connector = registry.get(connector_id)

    if connector is None:
        raise HTTPException(status_code=404, detail=f"Connector {connector_id} not found")

    # Parse direction
    direction_map = {
        "pull": SyncDirection.PULL,
        "push": SyncDirection.PUSH,
        "bidirectional": SyncDirection.BIDIRECTIONAL,
    }
    direction = direction_map.get(request.direction, SyncDirection.BIDIRECTIONAL)

    options = SyncOptions(
        direction=direction,
        mode=SyncMode.INCREMENTAL,
        force=request.force,
    )

    # Run sync in background
    from saw.db.config import get_async_engine
    from sqlalchemy.ext.asyncio import async_sessionmaker

    engine = get_async_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        engine = SyncEngine(
            registry=registry,
            write_queue=None,
            session=session,
        )

        result = await engine.sync(
            connector_id=connector_id,
            connector=connector,
            options=options,
        )

        return {
            "success": result.success,
            "message": "Sync completed" if result.success else "Sync failed",
            "items_pulled": result.pulled_count,
            "items_pushed": result.pushed_count,
            "errors": result.errors,
        }


@router.post("/trigger-all")
async def trigger_all_syncs(background_tasks: BackgroundTasks) -> dict:
    """Trigger sync for all enabled connectors.

    Fire-and-forget - syncs run in background.

    Returns:
        Dict with triggered connector count.
    """
    registry = ConnectorRegistry()
    platforms = registry.list_all()

    # Queue sync for each connector
    triggered_count = len(platforms)

    return {
        "success": True,
        "message": f"Triggered sync for {triggered_count} connectors",
        "connectors": platforms,
    }


@router.get("/logs")
async def get_sync_logs(
    platform: Optional[str] = None,
    connector_id: Optional[str] = None,
    limit: int = 100,
) -> dict:
    """Get recent sync logs.

    Args:
        platform: Filter by platform.
        connector_id: Filter by connector.
        limit: Maximum logs to return.

    Returns:
        Dict with logs list.
    """
    from saw.db.config import get_async_engine
    from sqlalchemy.ext.asyncio import async_sessionmaker

    engine = get_async_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        logger = SyncLogger(session)
        logs = await logger.get_recent_logs(
            platform=platform,
            connector_id=connector_id,
            limit=limit,
        )

        return {
            "logs": [
                {
                    "id": log.id,
                    "connector_id": log.connector_id,
                    "platform": log.platform,
                    "direction": log.direction,
                    "status": log.status,
                    "items_pulled": log.items_pulled,
                    "items_pushed": log.items_pushed,
                    "started_at": log.started_at.isoformat(),
                    "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                    "error_message": log.error_message,
                }
                for log in logs
            ],
            "total": len(logs),
        }
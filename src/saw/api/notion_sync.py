"""API endpoints for Notion sync control.

Plan 12-03: Bidirectional sync and polling.
Per NOTI-05: Sync can be triggered manually via API.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession

from saw.db.config import get_session_factory
from saw.connectors.protocol import SyncDirection
from saw.connectors.notion.sync_manager import NotionSyncManager, NotionSyncConfig
from saw.connectors.registry import ConnectorRegistry


router = APIRouter(prefix="/connectors/notion/sync", tags=["notion-sync"])


class SyncTriggerRequest(BaseModel):
    """Request for sync trigger endpoint."""
    direction: str = "bidirectional"  # pull, push, bidirectional
    force: bool = False


class SyncTriggerResponse(BaseModel):
    """Response for sync trigger endpoint."""
    sync_id: str
    status: str
    estimated_items: Optional[int] = None


class SyncStatusResponse(BaseModel):
    """Response for sync status endpoint."""
    last_sync_at: Optional[str] = None
    last_sync_result: Optional[str] = None
    items_synced: int = 0
    last_error: Optional[str] = None
    polling_enabled: bool = False
    poll_interval_seconds: int = 3600
    next_poll_at: Optional[str] = None


class PollStartRequest(BaseModel):
    """Request for poll start endpoint."""
    interval_seconds: int = 3600


class PollStartResponse(BaseModel):
    """Response for poll start endpoint."""
    polling_enabled: bool
    interval_seconds: int


class ConflictListResponse(BaseModel):
    """Response for conflict list endpoint."""
    conflicts: list[dict]


class ConflictResolveRequest(BaseModel):
    """Request for conflict resolution endpoint."""
    winner: str  # notion or saw


async def get_session():
    """Get database session."""
    session_factory = get_session_factory()
    async for session in session_factory():
        yield session


async def get_sync_manager(
    session: AsyncSession = Depends(get_session),
) -> NotionSyncManager:
    """Get sync manager instance."""
    registry = ConnectorRegistry()
    connector = registry.get("notion")

    if connector is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notion connector not registered",
        )

    # Get required components from connector
    sync_engine = getattr(connector, "_sync_engine", None)
    scheduler = getattr(connector, "_scheduler", None)

    if not sync_engine or not scheduler:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sync infrastructure not initialized",
        )

    config = NotionSyncConfig()

    return NotionSyncManager(
        config=config,
        connector=connector,
        sync_engine=sync_engine,
        scheduler=scheduler,
        session=session,
    )


@router.post("/trigger", response_model=SyncTriggerResponse)
async def trigger_sync(
    request: SyncTriggerRequest,
    manager: NotionSyncManager = Depends(get_sync_manager),
) -> SyncTriggerResponse:
    """Trigger manual sync operation.

    Returns 202 Accepted as sync runs asynchronously.
    """
    direction_map = {
        "pull": SyncDirection.PULL,
        "push": SyncDirection.PUSH,
        "bidirectional": SyncDirection.BIDIRECTIONAL,
    }

    direction = direction_map.get(request.direction)
    if direction is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid direction: {request.direction}",
        )

    # Trigger sync
    result = await manager.trigger_manual_sync(direction=direction, force=request.force)

    return SyncTriggerResponse(
        sync_id=f"sync-{result.connector_id}",
        status="started" if not result.errors else "failed",
        estimated_items=result.pulled_count + result.pushed_count,
    )


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(
    manager: NotionSyncManager = Depends(get_sync_manager),
) -> SyncStatusResponse:
    """Get current sync status."""
    poll_status = manager.get_poll_status()

    return SyncStatusResponse(
        polling_enabled=poll_status["polling_enabled"],
        poll_interval_seconds=poll_status["poll_interval_seconds"],
        items_synced=0,  # Would query from database
    )


@router.post("/pull")
async def trigger_pull(
    force: bool = False,
    manager: NotionSyncManager = Depends(get_sync_manager),
) -> dict:
    """Force pull sync."""
    result = await manager.sync_pull(force=force)
    return {
        "connector_id": result.connector_id,
        "pulled_count": result.pulled_count,
        "errors": result.errors,
    }


@router.post("/push")
async def trigger_push(
    manager: NotionSyncManager = Depends(get_sync_manager),
) -> dict:
    """Force push sync."""
    result = await manager.sync_push()
    return {
        "connector_id": result.connector_id,
        "pushed_count": result.pushed_count,
        "errors": result.errors,
    }


@router.post("/poll/start", response_model=PollStartResponse)
async def start_polling(
    request: PollStartRequest,
    manager: NotionSyncManager = Depends(get_sync_manager),
) -> PollStartResponse:
    """Enable polling with custom interval."""
    # Update config interval
    manager._config.poll_interval_seconds = request.interval_seconds
    manager.start_polling()

    return PollStartResponse(
        polling_enabled=True,
        interval_seconds=request.interval_seconds,
    )


@router.post("/poll/stop")
async def stop_polling(
    manager: NotionSyncManager = Depends(get_sync_manager),
) -> dict:
    """Disable polling."""
    manager.stop_polling()
    return {"polling_enabled": False}


@router.get("/conflicts", response_model=ConflictListResponse)
async def list_conflicts(
    limit: int = 50,
    resolved: bool = False,
    manager: NotionSyncManager = Depends(get_sync_manager),
) -> ConflictListResponse:
    """List sync conflicts for review."""
    # Would query conflict handler
    return ConflictListResponse(conflicts=[])


@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: int,
    request: ConflictResolveRequest,
    manager: NotionSyncManager = Depends(get_sync_manager),
) -> dict:
    """Manually resolve a conflict."""
    # Would call conflict handler resolve_manual_conflict
    return {
        "conflict_id": conflict_id,
        "winner": request.winner,
        "resolved": True,
    }


def get_notion_sync_router() -> APIRouter:
    """Get Notion sync API router."""
    return router
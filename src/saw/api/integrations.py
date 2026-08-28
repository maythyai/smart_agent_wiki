"""Integration Dashboard API endpoints.

Plan 15-01: Dashboard API and UI components.
Provides unified visibility into all connector health and management controls.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import status as http_status
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from saw.connectors.registry import ConnectorRegistry
from saw.connectors.health_monitor import HealthMonitor, HealthStatus
from saw.connectors.sync_status import SyncStatusTracker, SyncState
from saw.connectors.sync_engine import SyncEngine, SyncOptions, SyncMode
from saw.connectors.protocol import SyncDirection
from saw.db.connector_models import ConnectorConfigModel
from saw.db.sync_models import SyncStateModel, SyncLogModel


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


# Pydantic models for API responses

class DashboardConnector(BaseModel):
    """Connector status for dashboard display."""
    platform: str = Field(..., description="Platform identifier (notion, slack, github, etc.)")
    health_status: str = Field(..., description="Health status: healthy, degraded, unhealthy")
    last_sync_at: Optional[str] = Field(None, description="Last successful sync timestamp (ISO 8601)")
    items_synced: int = Field(0, description="Total items synced")
    error_count: int = Field(0, description="Recent error count")
    is_connected: bool = Field(False, description="Whether connector is connected")
    sync_direction: str = Field("pull", description="Sync direction: pull, push, bidirectional")
    sync_state: str = Field("idle", description="Current sync state: idle, syncing, paused, error")
    last_error: Optional[str] = Field(None, description="Most recent error message")


class DashboardResponse(BaseModel):
    """Dashboard API response."""
    connectors: list[DashboardConnector] = Field(default_factory=list, description="All connector statuses")
    system_health: dict[str, Any] = Field(default_factory=dict, description="Overall system health summary")


class ConnectorError(BaseModel):
    """Single connector error."""
    timestamp: str = Field(..., description="Error timestamp (ISO 8601)")
    error_message: str = Field(..., description="Error message")
    error_type: Optional[str] = Field(None, description="Error type/classification")


class SyncTriggerResponse(BaseModel):
    """Response for sync trigger."""
    platform: str
    sync_started: bool
    message: str


class ReauthResponse(BaseModel):
    """Response for re-authorization."""
    platform: str
    authorize_url: str
    state: str


async def get_db_session() -> AsyncSession:
    """Get database session dependency."""
    from saw.db.session import get_session
    async with get_session() as session:
        yield session


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    session: AsyncSession = Depends(get_db_session),
) -> DashboardResponse:
    """Get unified dashboard showing all connector status.

    Returns aggregated status from:
    - HealthMonitor: health_status, last_success_at, last_failure_at, last_error
    - SyncStatusTracker: sync_state, last_sync_at, items_synced
    - ConnectorRegistry: registered platforms
    - ConnectorConfigModel: is_connected status
    """
    registry = ConnectorRegistry()
    health_monitor = HealthMonitor(session)
    sync_tracker = SyncStatusTracker(session)

    # Get all registered platforms
    registered_platforms = registry.list_all()

    # Get all health statuses
    all_health = await health_monitor.get_all_health()
    health_by_platform = {h.platform: h for h in all_health}

    # Get all sync statuses
    all_sync = await sync_tracker.get_all_statuses()
    sync_by_platform = {s.platform: s for s in all_sync}

    # Get all connector configs
    stmt = select(ConnectorConfigModel)
    result = await session.execute(stmt)
    configs = result.scalars().all()
    config_by_platform = {c.platform: c for c in configs}

    # Build connector statuses
    connectors: list[DashboardConnector] = []

    # Include all registered platforms plus any with configs
    all_platforms = set(registered_platforms) | set(config_by_platform.keys())

    for platform in all_platforms:
        health = health_by_platform.get(platform)
        sync = sync_by_platform.get(platform)
        config = config_by_platform.get(platform)

        # Determine health status
        if health:
            health_status = health.status.value
            last_error = health.last_error
            error_count = health.total_failures
        else:
            health_status = "healthy"
            last_error = None
            error_count = 0

        # Determine sync status
        if sync:
            sync_state = sync.state.value
            last_sync_at = sync.last_sync_at.isoformat() if sync.last_sync_at else None
            items_synced = 0  # Would need to query SyncStateModel for actual count
        else:
            sync_state = "idle"
            last_sync_at = None
            items_synced = 0

        # Get items_synced from SyncStateModel
        stmt_items = select(SyncStateModel).where(SyncStateModel.platform == platform)
        result_items = await session.execute(stmt_items)
        sync_model = result_items.scalar_one_or_none()
        if sync_model:
            items_synced = sync_model.items_synced_total or 0

        # Determine connection status
        is_connected = config.is_connected if config else bool(registry.get(platform))

        # Determine sync direction (platform-specific)
        sync_direction = _get_sync_direction(platform)

        connectors.append(DashboardConnector(
            platform=platform,
            health_status=health_status,
            last_sync_at=last_sync_at,
            items_synced=items_synced,
            error_count=error_count,
            is_connected=is_connected,
            sync_direction=sync_direction,
            sync_state=sync_state,
            last_error=last_error,
        ))

    # Get system health summary
    system_health = await health_monitor.get_system_health()

    return DashboardResponse(
        connectors=connectors,
        system_health={
            "status": system_health.get("status", "healthy"),
            "healthy_count": system_health.get("healthy_count", 0),
            "degraded_count": system_health.get("degraded_count", 0),
            "unhealthy_count": system_health.get("unhealthy_count", 0),
        },
    )


@router.delete("/{platform}", status_code=http_status.HTTP_204_NO_CONTENT)
async def disconnect_platform(
    platform: str,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Disconnect a platform connector.

    - Unregisters connector from registry
    - Deletes connector config from database
    - Does NOT delete synced data (preserves knowledge base)
    """
    registry = ConnectorRegistry()

    # Unregister from registry
    unregistered = registry.unregister(platform)

    # Delete config from database
    stmt = select(ConnectorConfigModel).where(ConnectorConfigModel.platform == platform)
    result = await session.execute(stmt)
    config = result.scalar_one_or_none()

    if config:
        await session.delete(config)
        await session.commit()

    if not unregistered and not config:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform}' not found"
        )

    logger.info(f"Disconnected platform: {platform}")


@router.post("/{platform}/sync", response_model=SyncTriggerResponse)
async def trigger_sync(
    platform: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> SyncTriggerResponse:
    """Trigger manual sync for a platform.

    Runs the :class:`SyncEngine` for the registered connector and returns a
    summary of pulled/pushed items and any errors. The sync executes inline
    within the request so the session lifecycle stays valid; for long
    running connectors a background task queue should replace this (TODO).
    """
    registry = ConnectorRegistry()
    connector = registry.get(platform)

    if not connector:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform}' not registered"
        )

    # Check if already syncing
    sync_tracker = SyncStatusTracker(session)
    sync_status = await sync_tracker.get_status(f"{platform}-main")

    if sync_status.state == SyncState.SYNCING:
        return SyncTriggerResponse(
            platform=platform,
            sync_started=False,
            message="Sync already in progress"
        )

    # Construct SyncEngine with the correct (registry, write_queue, session)
    # signature and actually run the sync. The write queue is injected via
    # app.state so pulled items are persisted through the normal outbox.
    write_queue = getattr(request.app.state, "write_queue", None)
    sync_engine = SyncEngine(registry, write_queue, session)

    bidirectional = _get_sync_direction(platform) == "bidirectional"
    options = SyncOptions(
        direction=SyncDirection.BIDIRECTIONAL if bidirectional else SyncDirection.PULL,
        mode=SyncMode.FULL,
        force=True,
    )

    try:
        result = await sync_engine.sync(f"{platform}-main", connector, options)
    except Exception as e:
        logger.error(f"Sync failed for platform {platform}: {e}", exc_info=True)
        return SyncTriggerResponse(
            platform=platform,
            sync_started=False,
            message=f"Sync failed: {e}",
        )

    if result.success:
        message = (
            f"Synced {result.pulled_count} pulled, {result.pushed_count} pushed"
        )
    else:
        message = f"Sync completed with errors: {'; '.join(result.errors)}"

    logger.info(f"Sync finished for {platform}: {message}")

    return SyncTriggerResponse(
        platform=platform,
        sync_started=True,
        message=message
    )


@router.get("/{platform}/errors", response_model=list[ConnectorError])
async def get_connector_errors(
    platform: str,
    session: AsyncSession = Depends(get_db_session),
) -> list[ConnectorError]:
    """Get recent errors for a connector.

    Returns last 3 errors with timestamps.
    """
    # Query SyncLogModel for errors
    stmt = (
        select(SyncLogModel)
        .where(SyncLogModel.platform == platform)
        .where(SyncLogModel.status == "failed")
        .order_by(desc(SyncLogModel.started_at))
        .limit(3)
    )
    result = await session.execute(stmt)
    logs = result.scalars().all()

    errors = []
    for log in logs:
        errors.append(ConnectorError(
            timestamp=log.started_at.isoformat() if log.started_at else utcnow().isoformat(),
            error_message=log.error_message or "Unknown error",
            error_type=log.status if log.status else "unknown",
        ))

    return errors


@router.get("/{platform}/reauth", response_model=ReauthResponse)
async def get_reauth_url(
    platform: str,
    session: AsyncSession = Depends(get_db_session),
) -> ReauthResponse:
    """Get re-authorization URL for expired OAuth.

    Only applicable for OAuth-based connectors.
    """
    registry = ConnectorRegistry()
    connector = registry.get(platform)

    if not connector:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform}' not registered"
        )

    # Check if platform supports OAuth
    if not hasattr(connector, 'oauth_handler') or not connector.oauth_handler:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Platform '{platform}' does not use OAuth"
        )

    # Generate authorization URL
    try:
        # F-CONN-03: OAuthHandler.get_authorization_url is a SYNC method that
        # requires user_id. Awaiting it raised TypeError (500) and calling
        # without user_id raised TypeError too. Call it synchronously with an
        # explicit user_id. TODO(team-mode): resolve the authenticated
        # user_id from the request rather than the local default.
        auth_url, state = connector.oauth_handler.get_authorization_url(user_id="local")

        return ReauthResponse(
            platform=platform,
            authorize_url=auth_url,
            state=state,
        )
    except Exception as e:
        logger.error(f"Failed to get reauth URL for {platform}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )


def _get_sync_direction(platform: str) -> str:
    """Get sync direction for a platform.

    Derived from the connector's ``supports_push`` capability rather than a
    hardcoded platform allowlist, so newly push-capable connectors (the IM
    connectors that now implement ``put_item``) are reflected automatically
    instead of being silently forced to pull-only. A connector that cannot
    be resolved (e.g. its optional SDK is not installed) defaults to pull.
    """
    try:
        connector = ConnectorRegistry().get(platform)
    except Exception:
        connector = None
    if connector is not None and getattr(connector, "supports_push", False):
        return "bidirectional"
    return "pull"

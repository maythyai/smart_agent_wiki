"""Connector Settings API endpoints.

Plan 18-01: Settings API for per-connector configuration.
Per D-04: GET /api/v1/connectors/{platform}/settings
Per D-05: PUT /api/v1/connectors/{platform}/settings
Per D-06: POST /api/v1/connectors/{platform}/reauth
Per D-07: Sync interval validation (5min, 15min, 1hr, 6hr, manual)
Per D-09-D-11: Sync direction validation (inbound_only, outbound_only, bidirectional)
Per CONF-05: Rate limit bounds (1-100)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saw.db.connector_settings import (
    ConnectorSettingsModel,
    DEFAULT_SYNC_INTERVAL,
    DEFAULT_SYNC_DIRECTIONS,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/connectors", tags=["connector-settings"])


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


# Valid values per D-07, D-09-D-11
VALID_SYNC_INTERVALS = {"5min", "15min", "1hr", "6hr", "manual"}
VALID_SYNC_DIRECTIONS = {"inbound_only", "outbound_only", "bidirectional"}


# Pydantic models

class SettingsResponse(BaseModel):
    """Response model for connector settings."""
    platform: str = Field(..., description="Platform identifier")
    sync_interval: str = Field(..., description="Sync interval mode")
    sync_directions: str = Field(..., description="Sync direction mode")
    property_mappings: dict[str, str] = Field(
        default_factory=dict,
        description="Property mappings (SAW field -> platform property)"
    )
    rate_limit_override: Optional[int] = Field(
        None,
        description="Rate limit override (1-100)"
    )
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")


class SettingsUpdateRequest(BaseModel):
    """Request model for updating connector settings."""
    sync_interval: Optional[str] = Field(
        None,
        description="Sync interval: 5min, 15min, 1hr, 6hr, manual"
    )
    sync_directions: Optional[str] = Field(
        None,
        description="Sync direction: inbound_only, outbound_only, bidirectional"
    )
    property_mappings: Optional[dict[str, str]] = Field(
        None,
        description="Property mappings (SAW field -> platform property)"
    )
    rate_limit_override: Optional[int] = Field(
        None,
        description="Rate limit override (1-100), null to remove override"
    )

    @field_validator("sync_interval")
    @classmethod
    def validate_sync_interval(cls, v: Optional[str]) -> Optional[str]:
        """Validate sync_interval against allowed values."""
        if v is not None and v not in VALID_SYNC_INTERVALS:
            raise ValueError(
                f"Invalid sync_interval. Must be one of: {', '.join(sorted(VALID_SYNC_INTERVALS))}"
            )
        return v

    @field_validator("sync_directions")
    @classmethod
    def validate_sync_directions(cls, v: Optional[str]) -> Optional[str]:
        """Validate sync_directions against allowed values."""
        if v is not None and v not in VALID_SYNC_DIRECTIONS:
            raise ValueError(
                f"Invalid sync_directions. Must be one of: {', '.join(sorted(VALID_SYNC_DIRECTIONS))}"
            )
        return v

    @field_validator("rate_limit_override")
    @classmethod
    def validate_rate_limit(cls, v: Optional[int]) -> Optional[int]:
        """Validate rate_limit_override is within bounds (1-100)."""
        if v is not None and (v < 1 or v > 100):
            raise ValueError("rate_limit_override must be between 1 and 100")
        return v


class ReauthResponse(BaseModel):
    """Response model for re-authorization."""
    platform: str = Field(..., description="Platform identifier")
    authorize_url: str = Field(..., description="OAuth authorization URL")
    state: str = Field(..., description="OAuth state parameter for CSRF protection")


# Database session dependency

async def get_db_session() -> AsyncSession:
    """Get database session dependency."""
    from saw.db.session import get_session
    async with get_session() as session:
        yield session


# API endpoints

@router.get("/{platform}/settings", response_model=SettingsResponse)
async def get_settings(
    platform: str,
    session: AsyncSession = Depends(get_db_session),
) -> SettingsResponse:
    """Get settings for a connector.

    Per D-04: Returns current settings for the platform.
    Returns default values if no settings exist yet.
    """
    stmt = select(ConnectorSettingsModel).where(
        ConnectorSettingsModel.platform == platform
    )
    result = await session.execute(stmt)
    settings = result.scalar_one_or_none()

    if settings:
        # Parse property_mappings JSON
        mappings = {}
        if settings.property_mappings:
            try:
                mappings = json.loads(settings.property_mappings)
            except json.JSONDecodeError:
                logger.warning(
                    f"Invalid property_mappings JSON for {platform}: {settings.property_mappings}"
                )
                mappings = {}

        return SettingsResponse(
            platform=settings.platform,
            sync_interval=settings.sync_interval,
            sync_directions=settings.sync_directions,
            property_mappings=mappings,
            rate_limit_override=settings.rate_limit_override,
            updated_at=settings.updated_at.isoformat() if settings.updated_at else utcnow().isoformat(),
        )
    else:
        # Return defaults for new connector
        return SettingsResponse(
            platform=platform,
            sync_interval=DEFAULT_SYNC_INTERVAL,
            sync_directions=DEFAULT_SYNC_DIRECTIONS,
            property_mappings={},
            rate_limit_override=None,
            updated_at=utcnow().isoformat(),
        )


@router.put("/{platform}/settings", response_model=SettingsResponse)
async def update_settings(
    platform: str,
    update: SettingsUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> SettingsResponse:
    """Update settings for a connector.

    Per D-05: Updates settings for the platform.
    Validates sync_interval, sync_directions, and rate_limit_override.
    Returns updated settings confirming the save.
    """
    stmt = select(ConnectorSettingsModel).where(
        ConnectorSettingsModel.platform == platform
    )
    result = await session.execute(stmt)
    settings = result.scalar_one_or_none()

    if not settings:
        # Create new settings row
        settings = ConnectorSettingsModel(
            platform=platform,
            sync_interval=DEFAULT_SYNC_INTERVAL,
            sync_directions=DEFAULT_SYNC_DIRECTIONS,
        )
        session.add(settings)

    # Update fields if provided
    if update.sync_interval is not None:
        settings.sync_interval = update.sync_interval

    if update.sync_directions is not None:
        settings.sync_directions = update.sync_directions

    if update.property_mappings is not None:
        settings.property_mappings = json.dumps(update.property_mappings)

    if update.rate_limit_override is not None:
        settings.rate_limit_override = update.rate_limit_override
    elif update.rate_limit_override is None and "rate_limit_override" in update.model_fields_set:
        # Explicitly set to null - remove override
        settings.rate_limit_override = None

    settings.updated_at = utcnow()

    await session.commit()
    await session.refresh(settings)

    logger.info(f"Updated settings for {platform}")

    # Parse property_mappings for response
    mappings = {}
    if settings.property_mappings:
        try:
            mappings = json.loads(settings.property_mappings)
        except json.JSONDecodeError:
            pass

    return SettingsResponse(
        platform=settings.platform,
        sync_interval=settings.sync_interval,
        sync_directions=settings.sync_directions,
        property_mappings=mappings,
        rate_limit_override=settings.rate_limit_override,
        updated_at=settings.updated_at.isoformat(),
    )


@router.post("/{platform}/reauth", response_model=ReauthResponse)
async def reauthorize_platform(
    platform: str,
    session: AsyncSession = Depends(get_db_session),
) -> ReauthResponse:
    """Get re-authorization URL for expired OAuth.

    Per D-06: Returns OAuth re-authorization URL.
    Delegates to existing OAuth handler in connector.
    """
    from saw.connectors.registry import ConnectorRegistry

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
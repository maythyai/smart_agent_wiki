"""FastAPI endpoints for OAuth callback handling.

Plan 10-02: OAuth Handler and Token Encryption.
Per AUTH-01: Unified OAuth flow for all OAuth platforms.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from saw.connectors.oauth_handler import OAuthHandler, OAuthConfig, OAuthError
from saw.connectors.token_encryption import TokenEncryption
from saw.connectors.models import TokenMasker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/oauth", tags=["oauth"])


class AuthorizeResponse(BaseModel):
    """Response for OAuth authorization start."""
    authorization_url: str
    state: str


class CallbackResponse(BaseModel):
    """Response for OAuth callback."""
    status: str
    platform: str
    connector_id: str
    masked_token: str


class PlatformInfo(BaseModel):
    """Platform information for OAuth."""
    name: str
    display_name: str
    supports_oauth: bool


def get_oauth_config(platform: str, request: Request) -> OAuthConfig:
    """Get OAuth configuration for platform.

    Args:
        platform: Platform identifier.
        request: FastAPI request.

    Returns:
        OAuthConfig for the platform.

    Raises:
        HTTPException: If platform not supported.
    """
    # In production, load from settings/environment
    settings = getattr(request.app.state, "settings", None)

    configs = {
        "notion": OAuthConfig.notion(
            client_id=getattr(settings, "NOTION_CLIENT_ID", ""),
            client_secret=getattr(settings, "NOTION_CLIENT_SECRET", ""),
            redirect_uri=f"{getattr(settings, 'OAUTH_REDIRECT_URI', '')}/notion/callback",
        ),
        "slack": OAuthConfig.slack(
            client_id=getattr(settings, "SLACK_CLIENT_ID", ""),
            client_secret=getattr(settings, "SLACK_CLIENT_SECRET", ""),
            redirect_uri=f"{getattr(settings, 'OAUTH_REDIRECT_URI', '')}/slack/callback",
        ),
        "github": OAuthConfig.github(
            client_id=getattr(settings, "GITHUB_CLIENT_ID", ""),
            client_secret=getattr(settings, "GITHUB_CLIENT_SECRET", ""),
            redirect_uri=f"{getattr(settings, 'OAUTH_REDIRECT_URI', '')}/github/callback",
        ),
        "feishu": OAuthConfig.feishu(
            client_id=getattr(settings, "FEISHU_CLIENT_ID", ""),
            client_secret=getattr(settings, "FEISHU_CLIENT_SECRET", ""),
            redirect_uri=f"{getattr(settings, 'OAUTH_REDIRECT_URI', '')}/feishu/callback",
        ),
    }
    if platform not in configs:
        raise HTTPException(400, f"Unsupported platform: {platform}")
    return configs[platform]


@router.get("/platforms", response_model=list[PlatformInfo])
async def list_platforms():
    """List supported OAuth platforms.

    Per AUTH-01: Unified OAuth flow for all OAuth platforms.

    Returns:
        List of supported platforms with OAuth support.
    """
    return [
        PlatformInfo(name="notion", display_name="Notion", supports_oauth=True),
        PlatformInfo(name="slack", display_name="Slack", supports_oauth=True),
        PlatformInfo(name="github", display_name="GitHub", supports_oauth=True),
        PlatformInfo(name="feishu", display_name="Feishu", supports_oauth=True),
    ]


@router.get("/{platform}/authorize", response_model=AuthorizeResponse)
async def start_oauth_flow(
    platform: str,
    request: Request,
    redirect_to: Optional[str] = None,
):
    """Start OAuth flow for platform.

    Per AUTH-01: Unified OAuth flow for all OAuth platforms.

    Args:
        platform: Platform identifier (notion, slack, github, feishu).
        request: FastAPI request.
        redirect_to: URL to redirect after completion.

    Returns:
        Authorization URL and state for OAuth flow.
    """
    # Get user from auth middleware
    user_id = getattr(request.state, "user_id", "anonymous")

    config = get_oauth_config(platform, request)
    encryption = TokenEncryption.from_env()
    redis = getattr(request.app.state, "redis", None)

    handler = OAuthHandler(
        config=config,
        platform=platform,
        encryption=encryption,
        redis_client=redis,
    )

    auth_url, state = handler.get_authorization_url(user_id, redirect_to)

    logger.info(f"OAuth flow started: platform={platform}, user={user_id}")

    return AuthorizeResponse(
        authorization_url=auth_url,
        state=state,
    )


@router.get("/{platform}/callback", response_model=CallbackResponse)
async def oauth_callback(
    platform: str,
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    """Handle OAuth callback from platform.

    Per AUTH-02: System stores OAuth tokens encrypted at rest.
    Per AUTH-04: Tokens masked in API responses.

    Args:
        platform: Platform identifier.
        request: FastAPI request.
        code: Authorization code from OAuth provider.
        state: State string from OAuth provider.
        error: OAuth error code (set when the user denies authorization).
        error_description: Human-readable OAuth error description.

    Returns:
        Connection status with masked token.

    Raises:
        HTTPException: If OAuth flow fails.
    """
    # F-CONN-07: handle user-denied authorization. Providers redirect back
    # with error=access_denied (and no code) when the user cancels; the
    # previous signature required 'code' -> 422 on a denial.
    if error or not code:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth authorization failed: "
            f"{error_description or error or 'cancelled by user'}",
        )

    config = get_oauth_config(platform, request)
    encryption = TokenEncryption.from_env()
    redis = getattr(request.app.state, "redis", None)

    handler = OAuthHandler(
        config=config,
        platform=platform,
        encryption=encryption,
        redis_client=redis,
    )

    try:
        encrypted_tokens, user_id = await handler.exchange_code(code, state)
    except OAuthError as e:
        logger.warning(f"OAuth callback failed: {e}")
        raise HTTPException(400, str(e))

    # Store in database
    from saw.db.connector_models import ConnectorConfigModel
    db = getattr(request.state, "db", None)

    if db:
        connector = ConnectorConfigModel(
            user_id=user_id,
            platform=platform,
            name=f"{platform.capitalize()} Connection",
            credentials_encrypted=encrypted_tokens,
            sync_direction="bidirectional",
            is_active=True,
        )
        db.add(connector)
        db.commit()
        db.refresh(connector)
        connector_id = connector.id
    else:
        # For testing without DB
        connector_id = "test-connector-id"

    # Get masked token for response
    token_data = encryption.decrypt_token_set(encrypted_tokens)
    masked_token = TokenMasker.mask_token(token_data["access_token"])

    logger.info(f"OAuth callback success: platform={platform}, user={user_id}")

    return CallbackResponse(
        status="connected",
        platform=platform,
        connector_id=connector_id,
        masked_token=masked_token,
    )

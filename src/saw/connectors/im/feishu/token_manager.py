"""Feishu multi-tenant token manager.

Plan 13-04 Task 2: Handle app_token and tenant_token.
Per FEIS-03: Handle multi-tenant token management.
"""
from __future__ import annotations

import httpx
import logging
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TenantToken:
    """Cached tenant token.

    Attributes:
        value: Token value.
        expires_at: Expiration timestamp.
    """

    value: str
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) >= self.expires_at


class FeishuTokenManager:
    """Manage Feishu multi-tenant tokens.

    Per FEIS-03: Handle app_token and tenant_token for multi-tenant.
    """

    FEISHU_API_BASE = "https://open.feishu.cn/open-apis"

    def __init__(self, app_id: str, app_secret: str) -> None:
        """Initialize token manager.

        Args:
            app_id: Feishu app ID.
            app_secret: Feishu app secret.
        """
        self._app_id = app_id
        self._app_secret = app_secret
        self._tenant_tokens: dict[str, TenantToken] = {}
        self._app_token: Optional[TenantToken] = None

    async def get_tenant_token(self, tenant_key: str | None = None) -> str:
        """Get tenant access token.

        Args:
            tenant_key: Optional tenant key for multi-tenant.

        Returns:
            Tenant access token.
        """
        cache_key = tenant_key or "default"

        # Check cached token
        if cache_key in self._tenant_tokens:
            token = self._tenant_tokens[cache_key]
            if not token.is_expired:
                return token.value

        # Fetch new tenant token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.FEISHU_API_BASE}/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": self._app_id,
                    "app_secret": self._app_secret,
                },
            )
            data = response.json()

        if data.get("code") != 0:
            logger.error(f"Failed to get tenant token: {data}")
            raise ValueError(f"Feishu auth failed: {data.get('msg')}")

        tenant_access_token = data["tenant_access_token"]
        expire_seconds = data.get("expire", 7200)

        # Cache token with expiry buffer
        self._tenant_tokens[cache_key] = TenantToken(
            value=tenant_access_token,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=expire_seconds - 60),
        )

        return tenant_access_token

    async def get_app_token(self) -> str:
        """Get app access token (for app-level operations).

        Returns:
            App access token.
        """
        # Check cached token
        if self._app_token and not self._app_token.is_expired:
            return self._app_token.value

        # Fetch new app token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.FEISHU_API_BASE}/auth/v3/app_access_token/internal",
                json={
                    "app_id": self._app_id,
                    "app_secret": self._app_secret,
                },
            )
            data = response.json()

        if data.get("code") != 0:
            logger.error(f"Failed to get app token: {data}")
            raise ValueError(f"Feishu auth failed: {data.get('msg')}")

        app_access_token = data["app_access_token"]
        expire_seconds = data.get("expire", 7200)

        self._app_token = TenantToken(
            value=app_access_token,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=expire_seconds - 60),
        )

        return app_access_token

    def clear_cache(self) -> None:
        """Clear cached tokens."""
        self._tenant_tokens.clear()
        self._app_token = None
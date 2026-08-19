"""Feishu connector implementation.

Plan 13-04 Task 1: FeishuConnector core.
Per FEIS-01~05: Full Feishu connector implementation.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import lark_oapi as lark

from saw.connectors.protocol import (
    UnifiedConnectorInterface,
    AuthResult,
    ConnectorItem,
)
from saw.connectors.base_connector import BaseConnector
from saw.connectors.im.feishu.models import FeishuMessage
from saw.connectors.im.feishu.token_manager import FeishuTokenManager

logger = logging.getLogger(__name__)


class FeishuConnector(BaseConnector):
    """Feishu connector for message ingestion.

    Per FEIS-01: Install Feishu app via OAuth 2.0.
    Per FEIS-02: Receive messages via Feishu webhook events.
    Per FEIS-03: Handle multi-tenant token.
    Per FEIS-05: Handle Chinese content encoding.
    """

    platform_name = "feishu"
    supports_push = True  # App can send IM messages (im:message scope)

    def __init__(self) -> None:
        """Initialize Feishu connector."""
        super().__init__()
        self._app_id: Optional[str] = None
        self._app_secret: Optional[str] = None
        self._client: Optional[lark.Client] = None
        self._token_manager: Optional[FeishuTokenManager] = None

    @property
    def platform_name(self) -> str:
        """Platform identifier."""
        return "feishu"

    @property
    def supports_push(self) -> bool:
        """Feishu app can send IM messages."""
        return True

    async def authenticate(self, credentials: dict) -> AuthResult:
        """Complete Feishu authentication.

        Per FEIS-01: OAuth via app_id/app_secret.

        Args:
            credentials: Must contain 'app_id' and 'app_secret'.

        Returns:
            AuthResult with token info.
        """
        app_id = credentials.get("app_id")
        app_secret = credentials.get("app_secret")

        if not app_id or not app_secret:
            return AuthResult(
                access_token="",
                raw_response={"error": "app_id and app_secret required"},
            )

        self._app_id = app_id
        self._app_secret = app_secret

        # Initialize lark client
        self._client = lark.Client.builder() \
            .app_id(app_id) \
            .app_secret(app_secret) \
            .build()

        # Initialize token manager
        self._token_manager = FeishuTokenManager(app_id, app_secret)

        # Verify credentials by getting tenant token
        try:
            tenant_token = await self._token_manager.get_tenant_token()
            return AuthResult(
                access_token=tenant_token,
                raw_response={
                    "app_id": app_id,
                    "token_type": "tenant_access_token",
                },
            )
        except Exception as e:
            logger.error(f"Feishu auth failed: {e}")
            return AuthResult(
                access_token="",
                raw_response={"error": str(e)},
            )

    async def _do_get_items(
        self,
        since: datetime | None,
        filters: dict | None,
    ) -> list[ConnectorItem]:
        """Pull items from Feishu (for historical fetch).

        Note: Primary ingestion is via webhook push.
        """
        if not self._client:
            return []

        items: list[ConnectorItem] = []
        # Would need to implement historical message fetch
        return items

    async def put_item(self, item: ConnectorItem) -> str:
        """Send a text message to a Feishu chat.

        Requires ``item.metadata['chat_id']``. Returns the Feishu ``message_id``
        on success.
        """
        if not self._token_manager:
            raise RuntimeError("Feishu connector not authenticated")

        chat_id = item.metadata.get("chat_id") or item.metadata.get("receive_id")
        if not chat_id:
            raise ValueError("chat_id is required in item.metadata to push to Feishu")

        import httpx
        import json

        token = await self._token_manager.get_tenant_token()
        body = {
            "receive_id": chat_id,
            "msg_type": "text",
            "content": json.dumps({"text": item.content or item.title}),
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://open.feishu.cn/open-apis/im/v1/messages",
                params={"receive_id_type": "chat_id"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"Feishu push failed: {data.get('msg')}")

        return data.get("data", {}).get("message_id", "")

    async def delete_item(self, item_id: str) -> bool:
        """Delete a previously posted Feishu message by message_id."""
        if not self._token_manager:
            return False
        try:
            import httpx

            token = await self._token_manager.get_tenant_token()
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.delete(
                    f"https://open.feishu.cn/open-apis/im/v1/messages/{item_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )
                data = resp.json()
            return data.get("code") == 0
        except Exception as e:
            logger.warning("Feishu delete failed for %s: %s", item_id, e)
            return False

    def transform_to_claim(self, item: ConnectorItem) -> dict:
        """Convert Feishu message to SAW Claim dict."""
        metadata = item.metadata.copy()

        return {
            "id": item.id,
            "title": item.title,
            "content": item.content,  # Chinese content preserved
            "url": item.url,
            "author": item.author,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            "metadata": {
                "source_platform": "feishu",
                "source_id": item.id.replace("feishu-", ""),
                "chat_id": metadata.get("chat_id"),
                "author_id": metadata.get("author", {}).get("user_id"),
                "author_name": metadata.get("author", {}).get("name"),
                "message_type": metadata.get("message_type"),
            },
        }

    def transform_from_claim(self, claim: dict) -> ConnectorItem:
        """Convert a SAW Claim into a Feishu ConnectorItem for pushing."""
        meta = claim.get("metadata", {}) or {}
        return ConnectorItem(
            id=str(claim.get("source_id") or claim.get("id") or ""),
            title=str(claim.get("title", "")),
            content=str(claim.get("content", "")),
            url=claim.get("source_url"),
            author=claim.get("author"),
            metadata={
                "chat_id": meta.get("chat_id"),
                "platform": "feishu",
                "source_platform": "saw",
            },
        )

    async def get_tenant_token(self) -> str:
        """Get tenant access token.

        Per FEIS-03: Multi-tenant token management.
        """
        if not self._token_manager:
            raise ValueError("Connector not authenticated")
        return await self._token_manager.get_tenant_token()
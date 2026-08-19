"""WeCom connector implementation.

Plan 13-04 Task 4: WeComConnector core.
Per WECO-01~04: Full WeCom connector implementation.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
import xmltodict

from saw.connectors.protocol import (
    UnifiedConnectorInterface,
    AuthResult,
    ConnectorItem,
)
from saw.connectors.base_connector import BaseConnector
from saw.connectors.im.wecom.models import WeComMessage
from saw.connectors.im.wecom.crypto import WeComCrypto

logger = logging.getLogger(__name__)


class WeComConnector(BaseConnector):
    """WeCom connector for webhook message ingestion.

    Per WECO-01: Configure WeCom bot webhook URL.
    Per WECO-02: Receive messages via WeCom webhook.
    Per WECO-03: Handle AES-256-CBC encryption.
    Per WECO-04: Respect API rate limits.
    """

    platform_name = "wecom"
    supports_push = True  # Bot webhook can post text messages to its bound chat

    def __init__(self) -> None:
        """Initialize WeCom connector."""
        super().__init__()
        self._webhook_url: Optional[str] = None
        self._encoding_aes_key: Optional[str] = None
        self._token: Optional[str] = None
        self._corp_id: Optional[str] = None
        self._crypto: Optional[WeComCrypto] = None

    @property
    def platform_name(self) -> str:
        """Platform identifier."""
        return "wecom"

    @property
    def supports_push(self) -> bool:
        """WeCom bot webhook can post messages to its bound chat."""
        return True

    async def authenticate(self, credentials: dict) -> AuthResult:
        """Complete WeCom authentication.

        Per WECO-01: Webhook URL configuration.

        Args:
            credentials: Must contain 'webhook_url', optionally encryption keys.

        Returns:
            AuthResult with config info.
        """
        webhook_url = credentials.get("webhook_url")
        if not webhook_url:
            return AuthResult(
                access_token="",
                raw_response={"error": "webhook_url required"},
            )

        self._webhook_url = webhook_url
        self._encoding_aes_key = credentials.get("encoding_aes_key")
        self._token = credentials.get("token")
        self._corp_id = credentials.get("corp_id")

        # Initialize crypto if encryption keys provided
        if self._encoding_aes_key and self._token and self._corp_id:
            self._crypto = WeComCrypto(
                self._encoding_aes_key,
                self._token,
                self._corp_id,
            )

        return AuthResult(
            access_token="webhook",
            raw_response={
                "webhook_url": webhook_url,
                "encryption_enabled": self._crypto is not None,
            },
        )

    async def _do_get_items(
        self,
        since: datetime | None,
        filters: dict | None,
    ) -> list[ConnectorItem]:
        """Pull items from WeCom (not used for webhooks)."""
        return []

    async def put_item(self, item: ConnectorItem) -> str:
        """Post a text message to the configured WeCom bot webhook.

        WeCom bot webhooks can only send to the chat they are bound to, so no
        channel selection is needed. Returns the WeCom ``msgid`` (may be empty
        for some webhook types) on success.
        """
        if not self._webhook_url:
            raise RuntimeError("WeCom webhook URL not configured")

        import httpx

        text = item.content or item.title
        if not text:
            raise ValueError("Cannot push an empty WeCom message")

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                self._webhook_url,
                json={"msgtype": "text", "text": {"content": text}},
            )
            data = resp.json()

        if data.get("errcode") != 0:
            raise RuntimeError(f"WeCom push failed: {data.get('errmsg')}")

        return data.get("msgid", "") or ""

    async def delete_item(self, item_id: str) -> bool:
        """Delete is not supported by WeCom bot webhooks."""
        logger.warning("WeCom bot webhooks do not support message deletion")
        return False

    def transform_to_claim(self, item: ConnectorItem) -> dict:
        """Convert WeCom message to SAW Claim dict."""
        metadata = item.metadata.copy()

        return {
            "id": item.id,
            "title": item.title,
            "content": item.content,
            "url": item.url,
            "author": item.author,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            "metadata": {
                "source_platform": "wecom",
                "source_id": item.id.replace("wecom-", ""),
                "from_user": metadata.get("from_user"),
                "chat_id": metadata.get("chat_id"),
            },
        }

    def transform_from_claim(self, claim: dict) -> ConnectorItem:
        """Convert a SAW Claim into a WeCom ConnectorItem for pushing."""
        meta = claim.get("metadata", {}) or {}
        return ConnectorItem(
            id=str(claim.get("source_id") or claim.get("id") or ""),
            title=str(claim.get("title", "")),
            content=str(claim.get("content", "")),
            url=claim.get("source_url"),
            author=claim.get("author"),
            metadata={
                "chat_id": meta.get("chat_id"),
                "platform": "wecom",
                "source_platform": "saw",
            },
        )

    async def process_webhook(
        self,
        body: bytes,
        signature: str,
        timestamp: str,
        nonce: str,
    ) -> list[ConnectorItem]:
        """Process incoming webhook message.

        Per WECO-02: Receive messages via webhook.
        Per WECO-03: Decrypt if encrypted.

        Args:
            body: Raw request body.
            signature: Message signature.
            timestamp: Request timestamp.
            nonce: Request nonce.

        Returns:
            List of ConnectorItems from the message.
        """
        # Parse XML
        event_data = xmltodict.parse(body)
        xml_msg = event_data.get("xml", event_data)

        encrypted = xml_msg.get("Encrypt", "")

        # Verify signature and decrypt if crypto is configured
        if self._crypto and encrypted:
            if not self._crypto.verify_signature(signature, timestamp, nonce, encrypted):
                logger.warning("WeCom signature verification failed")
                return []

            try:
                decrypted = self._crypto.decrypt(encrypted)
                event_data = xmltodict.parse(decrypted)
            except Exception as e:
                logger.error(f"WeCom decryption failed: {e}")
                return []

        # Parse message
        message = WeComMessage.from_xml(event_data)

        # Create ConnectorItem
        item = ConnectorItem(
            id=f"wecom-{message.message_id}",
            title=f"WeCom message from {message.from_user}",
            content=message.content,
            url=None,
            author=message.from_user,
            created_at=message.timestamp,
            metadata={
                "platform": "wecom",
                "message_type": message.message_type,
                "from_user": message.from_user,
                "to_user": message.to_user,
                "chat_id": message.chat_id,
            },
        )

        return [item]
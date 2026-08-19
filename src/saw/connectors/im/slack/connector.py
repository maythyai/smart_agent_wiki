"""Slack connector implementation.

Plan 13-02 Task 1: SlackConnector core.
Per SLAK-01~06: Full Slack connector implementation.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from slack_sdk.web.async_client import AsyncWebClient

from saw.connectors.protocol import (
    UnifiedConnectorInterface,
    AuthResult,
    ConnectorItem,
    SyncDirection,
)
from saw.connectors.base_connector import BaseConnector
from saw.connectors.rate_limiter import RateLimitManager

logger = logging.getLogger(__name__)


class SlackConnector(BaseConnector):
    """Slack connector for message ingestion.

    Per SLAK-01: Install Slack app via OAuth 2.0.
    Per SLAK-02: Receive events via Slack Events API.
    Per SLAK-06: Respect tier-based rate limits.
    """

    platform_name = "slack"
    supports_push = True  # Bot can post messages via chat.postMessage (chat:write scope)

    def __init__(self) -> None:
        """Initialize Slack connector."""
        super().__init__()
        self._client: Optional[AsyncWebClient] = None
        self._team_id: Optional[str] = None
        self._bot_token: Optional[str] = None

    @property
    def platform_name(self) -> str:
        """Platform identifier."""
        return "slack"

    @property
    def supports_push(self) -> bool:
        """Slack bot can post messages (chat:write scope required)."""
        return True

    async def authenticate(self, credentials: dict) -> AuthResult:
        """Complete Slack authentication.

        Per SLAK-01: OAuth flow handled by SlackOAuthHandler.

        Args:
            credentials: Must contain 'bot_token' and optionally 'team_id'.

        Returns:
            AuthResult with token info.
        """
        bot_token = credentials.get("bot_token")
        if not bot_token:
            return AuthResult(
                access_token="",
                raw_response={"error": "bot_token required"},
            )

        self._bot_token = bot_token
        self._team_id = credentials.get("team_id")

        # Initialize Slack client
        self._client = AsyncWebClient(token=bot_token)

        # Verify token
        try:
            auth_test = await self._client.auth_test()
            self._team_id = auth_test.get("team_id")
            return AuthResult(
                access_token=bot_token,
                scopes=auth_test.get("scopes", []),
                raw_response={
                    "team_id": self._team_id,
                    "team_name": auth_test.get("team"),
                    "user_id": auth_test.get("user_id"),
                },
            )
        except Exception as e:
            logger.error(f"Slack auth failed: {e}")
            return AuthResult(
                access_token="",
                raw_response={"error": str(e)},
            )

    async def _do_get_items(
        self,
        since: datetime | None,
        filters: dict | None,
    ) -> list[ConnectorItem]:
        """Pull items from Slack (for historical fetch).

        Note: Primary ingestion is via Events API push.
        This method is for fetching historical messages if needed.
        """
        if not self._client:
            return []

        items: list[ConnectorItem] = []
        channels = filters.get("channels", []) if filters else []

        # If no channels specified, list all channels
        if not channels:
            try:
                result = await self._client.conversations_list(
                    types="public_channel,private_channel"
                )
                channels = [ch["id"] for ch in result.get("channels", [])]
            except Exception as e:
                logger.warning(f"Failed to list channels: {e}")
                return []

        # Fetch messages from each channel
        for channel_id in channels:
            try:
                result = await self._client.conversations_history(
                    channel=channel_id,
                    oldest=since.timestamp() if since else None,
                    limit=100,  # Per SLAK-06: respect rate limits
                )
                for msg in result.get("messages", []):
                    item = self._message_to_item(msg, channel_id)
                    if item:
                        items.append(item)
            except Exception as e:
                logger.warning(f"Failed to fetch history for {channel_id}: {e}")

        return items

    async def put_item(self, item: ConnectorItem) -> str:
        """Post a message to a Slack channel.

        Requires ``item.metadata['channel_id']``. Returns the message ``ts``
        (platform item id) on success.
        """
        if not self._client:
            raise RuntimeError("Slack connector not authenticated")

        channel_id = item.metadata.get("channel_id")
        if not channel_id:
            raise ValueError("channel_id is required in item.metadata to push to Slack")

        text = item.content or item.title
        if not text:
            raise ValueError("Cannot push an empty Slack message")

        response = await self._client.chat_postMessage(channel=channel_id, text=text)
        # SlackResponse behaves like a dict; ts identifies the posted message.
        ts = ""
        try:
            ts = response["ts"]  # type: ignore[index]
        except Exception:
            ts = response.get("ts", "") if hasattr(response, "get") else ""
        return f"slack-{channel_id}-{ts}" if ts else ""

    async def delete_item(self, item_id: str) -> bool:
        """Delete a previously posted Slack message.

        ``item_id`` must be the ``slack-{channel_id}-{ts}`` form returned by
        ``put_item``.
        """
        if not self._client:
            return False

        parts = item_id.split("-", 2)
        if len(parts) < 3 or parts[0] != "slack":
            logger.warning("Slack delete requires 'slack-{channel}-{ts}' id, got %s", item_id)
            return False
        _, channel_id, ts = parts
        try:
            await self._client.chat_delete(channel=channel_id, ts=ts)
            return True
        except Exception as e:
            logger.warning("Slack delete failed for %s: %s", item_id, e)
            return False

    def transform_to_claim(self, item: ConnectorItem) -> dict:
        """Convert Slack message to SAW Claim dict.

        Per IM-03: Map to ClaimCreate with proper metadata.
        Per SLAK-04: Include thread_parent_id for threads.
        """
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
                "source_platform": "slack",
                "source_id": item.id.replace("slack-", ""),
                "channel_id": metadata.get("channel_id"),
                "thread_parent_id": metadata.get("thread_parent_id"),  # SLAK-04
                "author_id": metadata.get("author", {}).get("user_id"),
                "author_name": metadata.get("author", {}).get("name"),
                "attachments": metadata.get("attachments", []),
                "reactions": metadata.get("reactions", {}),
            },
        }

    def transform_from_claim(self, claim: dict) -> ConnectorItem:
        """Convert a SAW Claim into a Slack ConnectorItem for pushing."""
        meta = claim.get("metadata", {}) or {}
        return ConnectorItem(
            id=str(claim.get("source_id") or claim.get("id") or ""),
            title=str(claim.get("title", "")),
            content=str(claim.get("content", "")),
            url=claim.get("source_url"),
            author=claim.get("author"),
            metadata={
                "channel_id": meta.get("channel_id"),
                "platform": "slack",
                "source_platform": "saw",
            },
        )

    def _message_to_item(
        self, message: dict, channel_id: str
    ) -> Optional[ConnectorItem]:
        """Convert Slack message dict to ConnectorItem."""
        ts = message.get("ts", "")
        if not ts:
            return None

        text = message.get("text", "")
        user = message.get("user", "unknown")

        # Parse timestamp
        try:
            timestamp = datetime.fromtimestamp(float(ts), tz=timezone.utc)
        except ValueError:
            timestamp = None

        return ConnectorItem(
            id=f"slack-{channel_id}-{ts}",
            title=f"Slack message in {channel_id}",
            content=text,
            url=f"https://slack.com/archives/{channel_id}/p{ts.replace('.', '')}",
            author=user,
            created_at=timestamp,
            metadata={
                "platform": "slack",
                "channel_id": channel_id,
                "thread_ts": message.get("thread_ts"),
                "reply_count": message.get("reply_count", 0),
            },
        )

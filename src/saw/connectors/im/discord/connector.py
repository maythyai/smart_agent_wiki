"""Discord connector implementation.

Plan 13-03 Task 1: DiscordConnector core.
Per DISC-01~05: Full Discord connector implementation.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional, Callable

import discord
from discord.ext import commands

from saw.connectors.protocol import (
    UnifiedConnectorInterface,
    AuthResult,
    ConnectorItem,
)
from saw.connectors.base_connector import BaseConnector
from saw.connectors.im.discord.models import DiscordMessage, DiscordUser

logger = logging.getLogger(__name__)


class DiscordConnector(BaseConnector):
    """Discord connector for message ingestion via Gateway.

    Per DISC-01: Add Discord bot to server.
    Per DISC-02: Receive messages via Discord Gateway.
    Per DISC-03: Handle reconnection with resume.
    Per DISC-05: 50 req/sec global rate limit (built-in).
    """

    platform_name = "discord"
    supports_push = True  # Bot can send messages to channels it can see

    def __init__(self) -> None:
        """Initialize Discord connector."""
        super().__init__()
        self._bot_token: Optional[str] = None
        self._bot: Optional[commands.Bot] = None
        self._session_id: Optional[str] = None
        self._sequence: Optional[int] = None
        self._item_callback: Optional[Callable[[ConnectorItem], None]] = None
        self._running = False

    @property
    def platform_name(self) -> str:
        """Platform identifier."""
        return "discord"

    @property
    def supports_push(self) -> bool:
        """Discord bot can send messages to channels."""
        return True

    async def authenticate(self, credentials: dict) -> AuthResult:
        """Complete Discord authentication.

        Per DISC-01: Bot token authentication.

        Args:
            credentials: Must contain 'bot_token'.

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

        return AuthResult(
            access_token=bot_token,
            raw_response={"token_type": "bot"},
        )

    async def _do_get_items(
        self,
        since: datetime | None,
        filters: dict | None,
    ) -> list[ConnectorItem]:
        """Pull items from Discord (not used for Gateway).

        Note: Discord uses Gateway push model, not polling.
        This method is for historical fetch if needed.
        """
        # Discord uses Gateway for real-time, not polling
        return []

    async def put_item(self, item: ConnectorItem) -> str:
        """Send a message to a Discord channel.

        Requires ``item.metadata['channel_id']``. Returns
        ``discord-{channel_id}-{message_id}`` on success.
        """
        if not self._bot or not self._bot.is_ready():
            raise RuntimeError("Discord bot is not connected")

        channel_id = item.metadata.get("channel_id")
        if not channel_id:
            raise ValueError("channel_id is required in item.metadata to push to Discord")

        channel = self._bot.get_channel(int(channel_id))
        if channel is None:
            raise RuntimeError(f"Discord channel {channel_id} not found or not visible to bot")

        text = item.content or item.title
        if not text:
            raise ValueError("Cannot push an empty Discord message")

        message = await channel.send(text)
        return f"discord-{channel_id}-{message.id}"

    async def delete_item(self, item_id: str) -> bool:
        """Delete a previously posted Discord message.

        ``item_id`` must be the ``discord-{channel_id}-{message_id}`` form
        returned by ``put_item``.
        """
        if not self._bot or not self._bot.is_ready():
            return False

        parts = item_id.split("-", 2)
        if len(parts) < 3 or parts[0] != "discord":
            logger.warning("Discord delete requires 'discord-{channel}-{msg}' id, got %s", item_id)
            return False
        _, channel_id, msg_id = parts
        channel = self._bot.get_channel(int(channel_id))
        if channel is None:
            return False
        try:
            msg = await channel.fetch_message(int(msg_id))
            await msg.delete()
            return True
        except Exception as e:
            logger.warning("Discord delete failed for %s: %s", item_id, e)
            return False

    def transform_to_claim(self, item: ConnectorItem) -> dict:
        """Convert Discord message to SAW Claim dict."""
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
                "source_platform": "discord",
                "source_id": item.id.replace("discord-", ""),
                "channel_id": metadata.get("channel_id"),
                "guild_id": metadata.get("guild_id"),
                "author_id": metadata.get("author", {}).get("user_id"),
                "author_name": metadata.get("author", {}).get("username"),
                "attachments": metadata.get("attachments", []),
                "embeds": metadata.get("embeds", []),
                "reactions": metadata.get("reactions", []),
                "thread_id": metadata.get("thread_id"),
                "reference_id": metadata.get("reference_id"),
            },
        }

    def transform_from_claim(self, claim: dict) -> ConnectorItem:
        """Convert a SAW Claim into a Discord ConnectorItem for pushing."""
        meta = claim.get("metadata", {}) or {}
        return ConnectorItem(
            id=str(claim.get("source_id") or claim.get("id") or ""),
            title=str(claim.get("title", "")),
            content=str(claim.get("content", "")),
            url=claim.get("source_url"),
            author=claim.get("author"),
            metadata={
                "channel_id": meta.get("channel_id"),
                "platform": "discord",
                "source_platform": "saw",
            },
        )

    async def start_gateway(self) -> None:
        """Start Discord Gateway connection.

        Per DISC-02: Receive messages via Gateway.
        Per DISC-03: Handle reconnection with resume.
        Per DISC-05: Built-in rate limiting (50 req/sec).
        """
        if not self._bot_token:
            raise ValueError("Bot token not configured")

        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for message content
        intents.messages = True
        intents.guilds = True

        # Create bot instance
        self._bot = commands.Bot(command_prefix="!", intents=intents)

        # Register event handlers
        @self._bot.event
        async def on_ready():
            """Store session for resume."""
            self._session_id = self._bot.session_id
            self._sequence = self._bot.sequence
            logger.info(f"Discord Gateway ready, session={self._session_id}")

        @self._bot.event
        async def on_resumed():
            """Reconnection successful via RESUME opcode."""
            logger.info(f"Discord Gateway resumed, session={self._session_id}")

        @self._bot.event
        async def on_message(message: discord.Message):
            """Process incoming message."""
            await self._process_message(message)

        @self._bot.event
        async def on_error(event: str, *args, **kwargs):
            """Handle Gateway errors."""
            logger.error(f"Discord Gateway error in {event}")
            # discord.py auto-reconnects with RESUME if session valid

        # Start the bot
        self._running = True
        await self._bot.start(self._bot_token)

    async def stop_gateway(self) -> None:
        """Stop Gateway connection."""
        if self._bot and self._running:
            await self._bot.close()
            self._running = False
            logger.info("Discord Gateway stopped")

    def set_item_callback(self, callback: Callable[[ConnectorItem], None]) -> None:
        """Set callback for processed items."""
        self._item_callback = callback

    async def _process_message(self, message: discord.Message) -> None:
        """Process incoming Discord message.

        Per DISC-04: Capture embeds and attachments.
        """
        # Ignore own messages
        if message.author == self._bot.user:
            return

        # Convert to DiscordMessage
        discord_msg = DiscordMessage.from_discord(message)

        # Convert to ConnectorItem
        item = ConnectorItem(
            id=f"discord-{discord_msg.channel_id}-{discord_msg.message_id}",
            title=f"Discord message in {discord_msg.channel_id}",
            content=discord_msg.content,
            url=self._build_permalink(discord_msg),
            author=discord_msg.author.username,
            created_at=discord_msg.timestamp,
            metadata={
                "platform": "discord",
                "channel_id": discord_msg.channel_id,
                "guild_id": discord_msg.guild_id,
                "author": discord_msg.author.to_dict(),
                "attachments": discord_msg.attachments,
                "embeds": discord_msg.embeds,
                "reactions": discord_msg.reactions,
                "thread_id": discord_msg.thread_id,
                "reference_id": discord_msg.reference_id,
            },
        )

        # Invoke callback
        if self._item_callback:
            self._item_callback(item)

    def _build_permalink(self, message: DiscordMessage) -> Optional[str]:
        """Build permalink to original message."""
        if message.guild_id:
            return f"https://discord.com/channels/{message.guild_id}/{message.channel_id}/{message.message_id}"
        return None

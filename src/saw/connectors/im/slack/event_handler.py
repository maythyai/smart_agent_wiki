"""Slack Events API handler.

Plan 13-02 Task 3: Process Slack webhook events.
Per SLAK-02: Receive events via Slack Events API.
Per SLAK-03: Handle message events.
Per SLAK-04: Capture thread replies.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Optional

from saw.connectors.im.slack.models import SlackMessage, SlackUser
from saw.connectors.message_handler import MessageHandler, ExtractedMessage
from saw.connectors.reaction_processor import ReactionProcessor
from saw.connectors.protocol import ConnectorItem

logger = logging.getLogger(__name__)


class SlackEventHandler:
    """Handle Slack Events API webhooks.

    Per SLAK-02: Receive events via Slack Events API.
    Per SLAK-03: Handle message events.
    """

    _instance: Optional["SlackEventHandler"] = None

    def __init__(self) -> None:
        """Initialize event handler."""
        self._message_handler: Optional[MessageHandler] = None
        self._reaction_processor: Optional[ReactionProcessor] = None
        self._item_callback: Optional[Callable[[ConnectorItem], None]] = None

    @classmethod
    def get_instance(cls) -> "SlackEventHandler":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_message_handler(self, handler: MessageHandler) -> None:
        """Set message handler for processing."""
        self._message_handler = handler

    def set_reaction_processor(self, processor: ReactionProcessor) -> None:
        """Set reaction processor."""
        self._reaction_processor = processor

    def set_item_callback(self, callback: Callable[[ConnectorItem], None]) -> None:
        """Set callback for processed items."""
        self._item_callback = callback

    async def process_event(self, event_data: dict) -> list[ConnectorItem]:
        """Process Slack event and return items.

        Per SLAK-02: Events API event processing.
        """
        event_type = event_data.get("event", {}).get("type")

        if event_type == "message":
            return await self._handle_message_event(event_data)
        elif event_type == "reaction_added":
            return await self._handle_reaction_event(event_data)
        elif event_type == "reaction_removed":
            return await self._handle_reaction_removed_event(event_data)

        return []

    async def _handle_message_event(self, event_data: dict) -> list[ConnectorItem]:
        """Handle message event.

        Per SLAK-03: Handle message.channels, message.groups.
        Per SLAK-04: Capture thread replies with thread_ts.
        """
        event = event_data.get("event", {})

        # Skip message_changed and message_deleted subtypes for now
        subtype = event.get("subtype")
        if subtype in ("message_changed", "message_deleted", "message_replied"):
            return []

        # Skip bot messages (unless we want to track them)
        if event.get("bot_id") and not event.get("text"):
            return []

        message = SlackMessage.from_event(event)

        # Convert to ConnectorItem
        item = ConnectorItem(
            id=f"slack-{message.channel_id}-{message.message_id}",
            title=f"Slack message in {message.channel_id}",
            content=message.content,
            url=self._build_permalink(message),
            author=message.author.name,
            created_at=message.timestamp,
            metadata={
                "platform": "slack",
                "channel_id": message.channel_id,
                "author": message.author.to_dict(),
                "thread_parent_id": message.thread_ts,  # Per SLAK-04
                "attachments": message.attachments,
                "reactions": message.reactions,
                **message.metadata,
            },
        )

        if self._item_callback:
            self._item_callback(item)

        return [item]

    async def _handle_reaction_event(self, event_data: dict) -> list[ConnectorItem]:
        """Handle reaction_added event.

        Per IM-05: Map reactions to confidence signals.
        """
        event = event_data.get("event", {})

        if not self._reaction_processor:
            return []

        # Process reaction as confidence signal
        emoji = event.get("reaction", "")
        item_ts = event.get("item", {}).get("ts", "")
        channel = event.get("item", {}).get("channel", "")

        # This would update an existing claim's confidence
        # For now, we return metadata about the reaction
        return [ConnectorItem(
            id=f"slack-reaction-{channel}-{item_ts}-{emoji}",
            title=f"Reaction {emoji} on message",
            content=emoji,
            metadata={
                "type": "reaction",
                "emoji": emoji,
                "message_id": item_ts,
                "channel_id": channel,
                "user_id": event.get("user"),
            },
        )]

    async def _handle_reaction_removed_event(self, event_data: dict) -> list[ConnectorItem]:
        """Handle reaction_removed event."""
        # Similar to reaction_added but removing the confidence signal
        return []

    def _build_permalink(self, message: SlackMessage) -> Optional[str]:
        """Build permalink to original message.

        Per IM-03: Include source_url in Claim.
        """
        if message.channel_id and message.message_id:
            # Format: https://team.slack.com/archives/CHANNEL/pTIMESTAMP
            ts = message.message_id.replace(".", "")
            return f"https://slack.com/archives/{message.channel_id}/p{ts}"
        return None

    def verify_url_challenge(self, challenge: str) -> dict:
        """Handle URL verification challenge.

        Slack sends this when first configuring the Events API.
        """
        return {"challenge": challenge}

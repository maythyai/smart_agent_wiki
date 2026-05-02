"""Slack connector models.

Plan 13-02 Task 1: Slack message and user models.
Per SLAK-03: Message event handling.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any


@dataclass
class SlackUser:
    """Slack user model.

    Attributes:
        user_id: Slack user ID (Uxxxxxxxx).
        name: Username.
        display_name: Display name from profile.
        is_bot: Whether user is a bot.
        team_id: Team/workspace ID.
    """

    user_id: str
    name: str
    display_name: Optional[str] = None
    is_bot: bool = False
    team_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "display_name": self.display_name,
            "is_bot": self.is_bot,
            "team_id": self.team_id,
        }

    @classmethod
    def from_event(cls, event: dict) -> "SlackUser":
        """Create from Slack event data."""
        return cls(
            user_id=event.get("user", "unknown"),
            name=event.get("username", "unknown"),
            display_name=event.get("user_profile", {}).get("display_name"),
            is_bot=event.get("bot_id") is not None,
            team_id=event.get("team"),
        )


@dataclass
class SlackMessage:
    """Slack message model.

    Per SLAK-03: Handle message events.
    Per SLAK-04: Capture thread replies with parent context.
    Per SLAK-05: Handle attachments.

    Attributes:
        message_id: Message timestamp (ts).
        channel_id: Channel ID.
        content: Message text content.
        author: Message author.
        thread_ts: Parent message ts for thread replies.
        timestamp: Message timestamp.
        edited_at: Edit timestamp if edited.
        attachments: List of attachment data.
        reactions: Dict mapping emoji to count.
        metadata: Additional message metadata.
    """

    message_id: str
    channel_id: str
    content: str
    author: SlackUser
    thread_ts: Optional[str] = None
    timestamp: Optional[datetime] = None
    edited_at: Optional[datetime] = None
    attachments: list[dict] = field(default_factory=list)
    reactions: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_event(cls, event: dict) -> "SlackMessage":
        """Create from Slack message event.

        Per SLAK-04: Capture thread_ts for thread context.
        """
        author = SlackUser.from_event(event)

        # Parse attachments
        attachments = []
        for att in event.get("attachments", []):
            attachments.append({
                "fallback": att.get("fallback", ""),
                "title": att.get("title"),
                "text": att.get("text"),
                "title_link": att.get("title_link"),
                "image_url": att.get("image_url"),
                "footer": att.get("footer"),
            })

        # Parse timestamp
        ts_str = event.get("ts", "")
        timestamp = None
        if ts_str:
            try:
                ts_float = float(ts_str)
                timestamp = datetime.fromtimestamp(ts_float)
            except ValueError:
                pass

        # Parse edit timestamp
        edited_ts = event.get("edited", {}).get("ts")
        edited_at = None
        if edited_ts:
            try:
                edited_at = datetime.fromtimestamp(float(edited_ts))
            except ValueError:
                pass

        return cls(
            message_id=event.get("ts", ""),
            channel_id=event.get("channel", ""),
            content=event.get("text", ""),
            author=author,
            thread_ts=event.get("thread_ts"),  # Parent message ts for threads
            timestamp=timestamp,
            edited_at=edited_at,
            attachments=attachments,
            reactions={},  # Populated by reaction events
            metadata={
                "subtype": event.get("subtype"),
                "bot_id": event.get("bot_id"),
                "bot_link": event.get("bot_link"),
                "unfurl_links": event.get("unfurl_links"),
                "unfurl_origin": event.get("unfurl_origin"),
            },
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "message_id": self.message_id,
            "channel_id": self.channel_id,
            "content": self.content,
            "author": self.author.to_dict(),
            "thread_ts": self.thread_ts,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "attachments": self.attachments,
            "reactions": self.reactions,
            "metadata": self.metadata,
        }

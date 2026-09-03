"""Feishu connector models.

Plan 13-04 Task 1: Feishu message and user models.
Per FEIS-05: Handle Chinese content encoding correctly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
import json


@dataclass
class FeishuUser:
    """Feishu user model.

    Attributes:
        user_id: Feishu user ID (open_id).
        name: User name.
        en_name: English name.
        avatar_url: URL to user's avatar.
        is_bot: Whether user is a bot.
    """

    user_id: str
    name: str
    en_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_bot: bool = False

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "en_name": self.en_name,
            "avatar_url": self.avatar_url,
            "is_bot": self.is_bot,
        }

    @classmethod
    def from_event(cls, event: dict) -> "FeishuUser":
        """Create from Feishu event data."""
        sender = event.get("sender", {})
        sender_id = sender.get("sender_id", {})
        return cls(
            user_id=sender_id.get("user_id", "unknown"),
            name=sender.get("sender_name", "unknown"),
            en_name=sender_id.get("user_id"),
            is_bot=sender_id.get("user_type") == "bot",
        )


@dataclass
class FeishuMessage:
    """Feishu message model.

    Per FEIS-05: Handle Chinese content encoding correctly.

    Attributes:
        message_id: Message ID.
        chat_id: Chat/channel ID.
        content: Message content (decoded from JSON).
        author: Message author.
        message_type: Message type (text, post, file, etc).
        created_at: Message creation time.
        metadata: Additional message metadata.
    """

    message_id: str
    chat_id: str
    content: str
    author: FeishuUser
    message_type: str = "text"
    created_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_event(cls, event: dict, decode_content: bool = True) -> "FeishuMessage":
        """Create from Feishu message event.

        Per FEIS-05: Handle Chinese content encoding correctly.
        """
        message = event.get("message", {})

        author = FeishuUser.from_event(event)

        # Decode content - Feishu sends content as JSON string
        content = message.get("content", "")
        message_type = message.get("message_type", "text")

        if decode_content and message_type == "text":
            content = cls._decode_content(content)

        # Parse timestamp
        created_at = None
        create_time = message.get("create_time")
        if create_time:
            try:
                created_at = datetime.fromisoformat(create_time.replace("Z", "+00:00"))
            except ValueError:
                pass

        return cls(
            message_id=message.get("message_id", ""),
            chat_id=message.get("chat_id", ""),
            content=content,
            author=author,
            message_type=message_type,
            created_at=created_at,
            metadata={
                "chat_type": message.get("chat_type"),
                "parent_message_id": message.get("parent_message_id"),
            },
        )

    @staticmethod
    def _decode_content(content: str) -> str:
        """Handle Chinese content encoding correctly.

        Per FEIS-05: Decode Feishu's JSON-encoded content.
        """
        if not content:
            return ""

        # Feishu sends text content as JSON: '{"text":"content"}'
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "text" in parsed:
                return parsed["text"]
            # Handle rich text (post type)
            if isinstance(parsed, dict) and "content" in parsed:
                return parsed["content"]
        except json.JSONDecodeError:
            # Not JSON, return as-is
            pass

        return content

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "message_id": self.message_id,
            "chat_id": self.chat_id,
            "content": self.content,
            "author": self.author.to_dict(),
            "message_type": self.message_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata,
        }
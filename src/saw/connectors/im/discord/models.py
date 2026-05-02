"""Discord connector models.

Plan 13-03 Task 2: Discord message and user models.
Per DISC-04: Capture embeds and attachments.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any


@dataclass
class DiscordUser:
    """Discord user model.

    Attributes:
        user_id: Discord user ID (snowflake).
        username: Discord username.
        display_name: Display name (nickname in guild).
        discriminator: Legacy discriminator (#0000).
        is_bot: Whether user is a bot.
        avatar_url: URL to user's avatar.
    """

    user_id: str
    username: str
    display_name: Optional[str] = None
    discriminator: Optional[str] = None
    is_bot: bool = False
    avatar_url: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "display_name": self.display_name,
            "discriminator": self.discriminator,
            "is_bot": self.is_bot,
            "avatar_url": self.avatar_url,
        }

    @classmethod
    def from_discord(cls, user: Any) -> "DiscordUser":
        """Create from discord.py User object."""
        return cls(
            user_id=str(user.id),
            username=user.name,
            display_name=getattr(user, "display_name", user.name),
            discriminator=getattr(user, "discriminator", None),
            is_bot=user.bot,
            avatar_url=str(user.avatar.url) if user.avatar else None,
        )


@dataclass
class DiscordMessage:
    """Discord message model.

    Per DISC-04: Capture embeds and attachments.

    Attributes:
        message_id: Discord message ID (snowflake).
        channel_id: Channel ID.
        guild_id: Guild/server ID (None for DMs).
        content: Message text content.
        author: Message author.
        timestamp: Message timestamp.
        edited_at: Edit timestamp if edited.
        attachments: List of attachment data.
        embeds: List of embed data.
        reactions: List of reaction data.
        thread_id: Thread ID if in a thread.
        reference_id: Reference message ID for replies.
    """

    message_id: str
    channel_id: str
    content: str
    author: DiscordUser
    guild_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    edited_at: Optional[datetime] = None
    attachments: list[dict] = field(default_factory=list)
    embeds: list[dict] = field(default_factory=list)
    reactions: list[dict] = field(default_factory=list)
    thread_id: Optional[str] = None
    reference_id: Optional[str] = None

    @classmethod
    def from_discord(cls, message: Any) -> "DiscordMessage":
        """Create from discord.py Message object.

        Per DISC-04: Extract embeds and attachments.
        """
        author = DiscordUser.from_discord(message.author)

        # Extract attachments
        attachments = []
        for att in message.attachments:
            attachments.append({
                "id": str(att.id),
                "filename": att.filename,
                "url": att.url,
                "proxy_url": att.proxy_url,
                "size": att.size,
                "content_type": att.content_type,
            })

        # Extract embeds
        embeds = []
        for embed in message.embeds:
            embed_data = {
                "type": embed.type,
                "title": embed.title,
                "description": embed.description,
                "url": embed.url,
            }
            if hasattr(embed, "fields"):
                embed_data["fields"] = [
                    {"name": f.name, "value": f.value}
                    for f in embed.fields
                ]
            embeds.append(embed_data)

        # Extract reactions
        reactions = []
        for reaction in message.reactions:
            reactions.append({
                "emoji": str(reaction.emoji),
                "count": reaction.count,
            })

        # Get guild ID if in a guild
        guild_id = str(message.guild.id) if message.guild else None

        # Get thread ID if in a thread
        thread_id = str(message.thread.id) if message.thread else None

        # Get reference (reply) ID
        reference_id = None
        if message.reference and message.reference.message_id:
            reference_id = str(message.reference.message_id)

        return cls(
            message_id=str(message.id),
            channel_id=str(message.channel.id),
            content=message.content or "",
            author=author,
            guild_id=guild_id,
            timestamp=message.created_at,
            edited_at=message.edited_at,
            attachments=attachments,
            embeds=embeds,
            reactions=reactions,
            thread_id=thread_id,
            reference_id=reference_id,
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "message_id": self.message_id,
            "channel_id": self.channel_id,
            "guild_id": self.guild_id,
            "content": self.content,
            "author": self.author.to_dict(),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "attachments": self.attachments,
            "embeds": self.embeds,
            "reactions": self.reactions,
            "thread_id": self.thread_id,
            "reference_id": self.reference_id,
        }

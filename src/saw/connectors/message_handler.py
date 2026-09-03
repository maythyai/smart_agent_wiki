"""IM message extraction and processing.

Plan 11-03: IM message handling and sync API endpoints.
Per IM-03: Extract message content, author, timestamp, channel.
Per IM-04: Capture thread context with thread_parent_id.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from saw.connectors.protocol import ConnectorItem
from saw.domain.utils import utcnow  # noqa: F401


@dataclass
class MessageAuthor:
    """Author of a message.

    Attributes:
        user_id: Platform-specific user identifier.
        username: Username/handle.
        display_name: Human-readable display name (optional).
        is_bot: Whether this is a bot account.
        avatar_url: URL to user's avatar (optional).
    """

    user_id: str
    username: str
    display_name: Optional[str] = None
    is_bot: bool = False
    avatar_url: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "display_name": self.display_name,
            "is_bot": self.is_bot,
            "avatar_url": self.avatar_url,
        }


@dataclass
class MessageContext:
    """Context for a message in an IM platform.

    Attributes:
        platform: Platform name (slack, discord, feishu, wecom).
        channel_id: Channel/room identifier.
        channel_name: Human-readable channel name.
        server_id: Guild/team identifier (Discord/Slack).
        server_name: Human-readable server name.
        thread_parent_id: Parent message ID for thread replies.
        thread_root_id: Root message ID for nested threads.
    """

    platform: str
    channel_id: str
    channel_name: Optional[str] = None
    server_id: Optional[str] = None
    server_name: Optional[str] = None
    thread_parent_id: Optional[str] = None
    thread_root_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "platform": self.platform,
            "channel_id": self.channel_id,
            "channel_name": self.channel_name,
            "server_id": self.server_id,
            "server_name": self.server_name,
            "thread_parent_id": self.thread_parent_id,
            "thread_root_id": self.thread_root_id,
        }


@dataclass
class ExtractedMessage:
    """Extracted message from IM platform.

    Attributes:
        platform_id: Platform's message identifier.
        content: Normalized message content.
        content_raw: Original content with formatting.
        author: Message author.
        context: Message context (channel, thread).
        created_at: When message was created.
        edited_at: When message was last edited.
        deleted_at: When message was deleted.
        reactions: Dict mapping emoji to reaction count.
        attachments: List of attachment URLs.
        mentions: List of mentioned user IDs.
        links: List of extracted URLs from content.
    """

    platform_id: str
    content: str
    author: MessageAuthor
    context: MessageContext
    created_at: datetime
    content_raw: Optional[str] = None
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    reactions: dict[str, int] = field(default_factory=dict)
    attachments: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "platform_id": self.platform_id,
            "content": self.content,
            "content_raw": self.content_raw,
            "author": self.author.to_dict(),
            "context": self.context.to_dict(),
            "created_at": self.created_at.isoformat(),
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "reactions": self.reactions,
            "attachments": self.attachments,
            "mentions": self.mentions,
            "links": self.links,
        }


class MessageHandler:
    """Extracts and processes messages from IM platforms.

    Per IM-03: Extract message content, author, timestamp, channel.
    Per IM-04: Capture thread context with thread_parent_id.
    """

    # Platform-specific mention patterns
    MENTION_PATTERNS = {
        "slack": [r"<@([A-Z][A-Z0-9]+)>", r"<!([a-z]+)>"],
        "discord": [r"<@!?(\d+)>", r"<@&(\d+)>"],
        "feishu": [r"@_user_id=([a-zA-Z0-9]+)_"],
        "wecom": [r"<@([a-zA-Z0-9]+)>"],
    }

    # Platform-specific link patterns
    LINK_PATTERN = r"https?://[^\s<>\"']+"

    def __init__(self, session: Any) -> None:
        """Initialize message handler.

        Args:
            session: Database session for claim operations.
        """
        self._session = session

    def extract_message(
        self,
        item: ConnectorItem,
        platform: str,
    ) -> ExtractedMessage:
        """Extract message from connector item.

        Args:
            item: ConnectorItem from IM platform.
            platform: Platform name.

        Returns:
            ExtractedMessage with all extracted fields.
        """
        metadata = item.metadata

        # Extract author
        author = self._extract_author(metadata, platform)

        # Extract context
        context = self._extract_context(metadata, platform)

        # Normalize content
        content = self.normalize_content(item.content, platform)

        # Extract reactions
        reactions = metadata.get("reactions", {})

        # Extract attachments
        attachments = metadata.get("attachments", [])

        # Extract mentions and links
        mentions = self._extract_mentions(item.content, platform)
        links = self._extract_links(item.content)

        return ExtractedMessage(
            platform_id=item.id,
            content=content,
            content_raw=item.content,
            author=author,
            context=context,
            created_at=item.created_at or utcnow(),
            edited_at=metadata.get("edited_at"),
            deleted_at=metadata.get("deleted_at"),
            reactions=reactions,
            attachments=attachments,
            mentions=mentions,
            links=links,
        )

    def to_claim_create(self, message: ExtractedMessage) -> dict:
        """Convert extracted message to claim creation dict.

        Per IM-03: Map to ClaimCreate with proper metadata.
        Per IM-04: Include thread_parent_id in metadata.

        Args:
            message: ExtractedMessage to convert.

        Returns:
            Dict ready for Write Queue submission.
        """
        metadata = {
            "source_platform": message.context.platform,
            "source_id": message.platform_id,
            "source_url": self._build_permalink(message),
            "channel_id": message.context.channel_id,
            "channel_name": message.context.channel_name,
            "author_id": message.author.user_id,
            "author_name": message.author.username,
            "author_display_name": message.author.display_name,
            "is_bot": message.author.is_bot,
            "reactions": message.reactions,
            "attachments": message.attachments,
            "mentions": message.mentions,
            "links": message.links,
        }

        # Add thread context if present
        if message.context.thread_parent_id:
            metadata["thread_parent_id"] = message.context.thread_parent_id
        if message.context.thread_root_id:
            metadata["thread_root_id"] = message.context.thread_root_id

        # Add server context if present
        if message.context.server_id:
            metadata["server_id"] = message.context.server_id
            metadata["server_name"] = message.context.server_name

        # Add edit history
        if message.edited_at:
            metadata["edited_at"] = message.edited_at.isoformat()

        return {
            "content": message.content,
            "source_platform": message.context.platform,
            "source_id": message.platform_id,
            **metadata,
        }

    def normalize_content(self, content: str, platform: str) -> str:
        """Normalize message content for storage.

        Per IM-03: Remove platform-specific formatting.

        Args:
            content: Raw message content.
            platform: Platform name.

        Returns:
            Normalized content string.
        """
        import re

        normalized = content

        if platform == "slack":
            # Remove user mentions: <@U123> -> @user
            normalized = re.sub(r"<@([A-Z][A-Z0-9]+)>", r"@\1", normalized)
            # Remove special mentions: <!channel> -> @channel
            normalized = re.sub(r"<!([a-z]+)>", r"@\1", normalized)
            # Remove link formatting: <url|text> -> text
            normalized = re.sub(r"<([^|]+)\|([^>]+)>", r"\2", normalized)

        elif platform == "discord":
            # Remove user mentions: <@123> or <@!123> -> @user
            normalized = re.sub(r"<@!?(\d+)>", r"@user", normalized)
            # Remove role mentions: <@&123> -> @role
            normalized = re.sub(r"<@&(\d+)>", r"@role", normalized)
            # Remove channel mentions: <#123> -> #channel
            normalized = re.sub(r"<#(\d+)>", r"#channel", normalized)

        elif platform == "feishu":
            # Remove rich text formatting markers
            normalized = re.sub(r"@_user_id=[a-zA-Z0-9]+_", "@user", normalized)

        elif platform == "wecom":
            # Similar to Slack
            normalized = re.sub(r"<@([a-zA-Z0-9]+)>", r"@\1", normalized)

        # Normalize whitespace
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized

    async def handle_edit(
        self,
        message: ExtractedMessage,
        existing_claim_id: str,
    ) -> dict:
        """Handle message edit by updating existing claim.

        Args:
            message: Updated message content.
            existing_claim_id: ID of existing claim to update.

        Returns:
            Dict with update data for Write Queue.
        """
        return {
            "content": message.content,
            "claim_id": existing_claim_id,
            "edited_at": message.edited_at.isoformat() if message.edited_at else utcnow().isoformat(),
            "source_platform": message.context.platform,
            "source_id": message.platform_id,
            "operation": "update",
        }

    async def handle_deletion(self, message: ExtractedMessage) -> dict:
        """Handle message deletion gracefully.

        Per IM-07: Graceful degradation - mark deleted, don't remove.

        Args:
            message: Deleted message info.

        Returns:
            Dict marking claim as deleted.
        """
        return {
            "source_platform": message.context.platform,
            "source_id": message.platform_id,
            "deleted_at": message.deleted_at.isoformat() if message.deleted_at else utcnow().isoformat(),
            "operation": "soft_delete",
        }

    def _extract_author(
        self,
        metadata: dict,
        platform: str,
    ) -> MessageAuthor:
        """Extract author from metadata."""
        author_data = metadata.get("author", {})
        if isinstance(author_data, dict):
            return MessageAuthor(
                user_id=author_data.get("id", "unknown"),
                username=author_data.get("username", "unknown"),
                display_name=author_data.get("display_name"),
                is_bot=author_data.get("is_bot", False),
                avatar_url=author_data.get("avatar_url"),
            )
        return MessageAuthor(
            user_id="unknown",
            username="unknown",
        )

    def _extract_context(
        self,
        metadata: dict,
        platform: str,
    ) -> MessageContext:
        """Extract context from metadata."""
        return MessageContext(
            platform=platform,
            channel_id=metadata.get("channel_id", "unknown"),
            channel_name=metadata.get("channel_name"),
            server_id=metadata.get("server_id") or metadata.get("guild_id") or metadata.get("team_id"),
            server_name=metadata.get("server_name") or metadata.get("guild_name") or metadata.get("team_name"),
            thread_parent_id=metadata.get("thread_parent_id"),
            thread_root_id=metadata.get("thread_root_id"),
        )

    def _extract_mentions(self, content: str, platform: str) -> list[str]:
        """Extract mentioned user IDs from content."""
        import re

        patterns = self.MENTION_PATTERNS.get(platform, [])
        mentions = []

        for pattern in patterns:
            matches = re.findall(pattern, content)
            mentions.extend(matches)

        return list(set(mentions))

    def _extract_links(self, content: str) -> list[str]:
        """Extract URLs from content."""
        import re

        return re.findall(self.LINK_PATTERN, content)

    def _build_permalink(self, message: ExtractedMessage) -> Optional[str]:
        """Build permalink to original message."""
        platform = message.context.platform

        if platform == "slack":
            # https://workspace.slack.com/archives/CHANNEL/pTIMESTAMP
            if message.context.server_id and message.context.channel_id:
                ts = str(int(message.created_at.timestamp() * 1000000))
                return f"https://slack.com/archives/{message.context.channel_id}/p{ts.replace('.', '')}"

        elif platform == "discord":
            # https://discord.com/channels/GUILD/CHANNEL/MESSAGE
            if message.context.server_id:
                return f"https://discord.com/channels/{message.context.server_id}/{message.context.channel_id}/{message.platform_id}"

        elif platform == "github":
            # Depends on whether it's an issue or discussion
            pass

        return None

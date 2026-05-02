"""Tests for message handler.

Plan 11-03, Task 1: MessageHandler.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

from saw.connectors.message_handler import (
    MessageAuthor,
    MessageContext,
    ExtractedMessage,
    MessageHandler,
)
from saw.connectors.protocol import ConnectorItem


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TestMessageAuthor:
    """Tests for MessageAuthor."""

    def test_author_creation(self):
        """Test creating MessageAuthor."""
        author = MessageAuthor(
            user_id="U123",
            username="testuser",
            display_name="Test User",
            is_bot=False,
        )
        assert author.user_id == "U123"
        assert author.username == "testuser"
        assert author.display_name == "Test User"
        assert author.is_bot is False

    def test_author_to_dict(self):
        """Test MessageAuthor serialization."""
        author = MessageAuthor(
            user_id="U456",
            username="botuser",
            is_bot=True,
        )
        d = author.to_dict()
        assert d["user_id"] == "U456"
        assert d["is_bot"] is True


class TestMessageContext:
    """Tests for MessageContext."""

    def test_context_creation(self):
        """Test creating MessageContext."""
        context = MessageContext(
            platform="slack",
            channel_id="C123",
            channel_name="general",
            thread_parent_id="msg-parent",
        )
        assert context.platform == "slack"
        assert context.channel_id == "C123"
        assert context.thread_parent_id == "msg-parent"

    def test_context_to_dict(self):
        """Test MessageContext serialization."""
        context = MessageContext(
            platform="discord",
            channel_id="ch-123",
            server_id="guild-456",
            thread_parent_id="thread-1",
        )
        d = context.to_dict()
        assert d["platform"] == "discord"
        assert d["server_id"] == "guild-456"
        assert d["thread_parent_id"] == "thread-1"


class TestExtractedMessage:
    """Tests for ExtractedMessage."""

    def test_message_creation(self):
        """Test creating ExtractedMessage."""
        author = MessageAuthor(user_id="U1", username="user")
        context = MessageContext(platform="slack", channel_id="C1")
        msg = ExtractedMessage(
            platform_id="msg-123",
            content="Hello world",
            author=author,
            context=context,
            created_at=utcnow(),
        )
        assert msg.platform_id == "msg-123"
        assert msg.content == "Hello world"
        assert msg.reactions == {}

    def test_message_with_reactions(self):
        """Test ExtractedMessage with reactions."""
        author = MessageAuthor(user_id="U2", username="user2")
        context = MessageContext(platform="discord", channel_id="D1")
        msg = ExtractedMessage(
            platform_id="msg-456",
            content="Test message",
            author=author,
            context=context,
            created_at=utcnow(),
            reactions={"👍": 5, "❤️": 3},
        )
        assert msg.reactions["👍"] == 5
        assert msg.reactions["❤️"] == 3


class TestMessageHandler:
    """Tests for MessageHandler."""

    @pytest.fixture
    def handler(self):
        """Create MessageHandler instance."""
        session = MagicMock()
        return MessageHandler(session)

    def test_extract_message_creates_claim(self, handler):
        """Test 1: MessageHandler.extract_message() creates Claim with content, author, timestamp."""
        item = ConnectorItem(
            id="msg-123",
            title="Message",
            content="Hello world",
            created_at=utcnow(),
            metadata={
                "author": {"id": "U123", "username": "testuser"},
                "channel_id": "C123",
            },
        )

        msg = handler.extract_message(item, "slack")

        assert msg.platform_id == "msg-123"
        assert msg.content == "Hello world"
        assert msg.author.user_id == "U123"
        assert msg.author.username == "testuser"
        assert msg.created_at is not None

    def test_stores_thread_parent_id(self, handler):
        """Test 2: MessageHandler stores thread_parent_id for threaded messages."""
        item = ConnectorItem(
            id="msg-thread-123",
            title="Thread Reply",
            content="Thread reply content",
            created_at=utcnow(),
            metadata={
                "author": {"id": "U456", "username": "replier"},
                "channel_id": "C123",
                "thread_parent_id": "msg-parent-1",
                "thread_root_id": "msg-root-1",
            },
        )

        msg = handler.extract_message(item, "slack")

        assert msg.context.thread_parent_id == "msg-parent-1"
        assert msg.context.thread_root_id == "msg-root-1"

    def test_extracts_channel_metadata(self, handler):
        """Test 3: MessageHandler extracts channel and server metadata."""
        item = ConnectorItem(
            id="msg-789",
            title="Message",
            content="Content",
            created_at=utcnow(),
            metadata={
                "author": {"id": "U1", "username": "user"},
                "channel_id": "CH123",
                "channel_name": "general",
                "server_id": "TEAM123",
                "server_name": "My Team",
            },
        )

        msg = handler.extract_message(item, "slack")

        assert msg.context.channel_id == "CH123"
        assert msg.context.channel_name == "general"
        assert msg.context.server_id == "TEAM123"
        assert msg.context.server_name == "My Team"

    def test_handles_message_edits(self, handler):
        """Test 4: MessageHandler handles message edits with version tracking."""
        item = ConnectorItem(
            id="msg-edit-1",
            title="Edited Message",
            content="Edited content",
            created_at=utcnow(),
            metadata={
                "author": {"id": "U1", "username": "user"},
                "channel_id": "C1",
                "edited_at": utcnow(),
            },
        )

        msg = handler.extract_message(item, "slack")

        assert msg.edited_at is not None
        assert msg.content == "Edited content"

    @pytest.mark.asyncio
    async def test_handles_message_deletion(self, handler):
        """Test 5: MessageHandler handles message deletions gracefully."""
        author = MessageAuthor(user_id="U1", username="user")
        context = MessageContext(platform="slack", channel_id="C1")
        msg = ExtractedMessage(
            platform_id="msg-delete-1",
            content="Deleted content",
            author=author,
            context=context,
            created_at=utcnow(),
            deleted_at=utcnow(),
        )

        result = await handler.handle_deletion(msg)

        assert result["operation"] == "soft_delete"
        assert result["source_platform"] == "slack"
        assert result["source_id"] == "msg-delete-1"

    def test_normalizes_slack_mentions(self, handler):
        """Test 6a: MessageHandler normalizes Slack mentions and links."""
        content = "<@U123> said <!channel> check <https://example.com|this link>"
        normalized = handler.normalize_content(content, "slack")

        assert "<@" not in normalized
        assert "<!" not in normalized
        assert "<https://" not in normalized
        assert "@U123" in normalized or "@channel" in normalized

    def test_normalizes_discord_mentions(self, handler):
        """Test 6b: MessageHandler normalizes Discord mentions."""
        content = "<@123> mentioned <@!456> and <@&789> in <#012>"
        normalized = handler.normalize_content(content, "discord")

        assert "<@" not in normalized
        assert "<#" not in normalized
        assert "@user" in normalized or "@role" in normalized

    def test_to_claim_create_includes_metadata(self, handler):
        """Test to_claim_create includes all required metadata."""
        author = MessageAuthor(user_id="U1", username="user", display_name="Test User")
        context = MessageContext(
            platform="slack",
            channel_id="C1",
            channel_name="general",
            thread_parent_id="parent-1",
        )
        msg = ExtractedMessage(
            platform_id="msg-meta-1",
            content="Test content",
            author=author,
            context=context,
            created_at=utcnow(),
            reactions={"👍": 5},
        )

        claim_dict = handler.to_claim_create(msg)

        assert claim_dict["source_platform"] == "slack"
        assert claim_dict["source_id"] == "msg-meta-1"
        assert claim_dict["channel_id"] == "C1"
        assert claim_dict["channel_name"] == "general"
        assert claim_dict["author_id"] == "U1"
        assert claim_dict["author_name"] == "user"
        assert claim_dict["thread_parent_id"] == "parent-1"
        assert claim_dict["reactions"]["👍"] == 5


class TestExtractedMessageLinks:
    """Tests for link extraction."""

    @pytest.fixture
    def handler(self):
        """Create MessageHandler instance."""
        session = MagicMock()
        return MessageHandler(session)

    def test_extracts_urls_from_content(self, handler):
        """Test URL extraction from message content."""
        item = ConnectorItem(
            id="msg-links",
            title="Message with links",
            content="Check https://example.com and http://test.org/path",
            created_at=utcnow(),
            metadata={
                "author": {"id": "U1", "username": "user"},
                "channel_id": "C1",
            },
        )

        msg = handler.extract_message(item, "slack")

        assert len(msg.links) == 2
        assert "https://example.com" in msg.links
        assert "http://test.org/path" in msg.links
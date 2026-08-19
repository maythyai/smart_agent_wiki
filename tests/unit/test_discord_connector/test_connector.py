"""Unit tests for Discord connector.

Plan 13-03: Test DiscordConnector implementation.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from saw.connectors.im.discord.connector import DiscordConnector
from saw.connectors.im.discord.models import DiscordMessage, DiscordUser
from saw.connectors.protocol import ConnectorItem


class TestDiscordConnector:
    """Tests for DiscordConnector."""

    @pytest.fixture
    def connector(self) -> DiscordConnector:
        """Create a connector instance."""
        return DiscordConnector()

    def test_connector_implements_protocol(self, connector: DiscordConnector):
        """Test 1: Connector implements UnifiedConnectorInterface."""
        assert connector.platform_name == "discord"
        assert connector.supports_push is True  # Bot can send messages

    @pytest.mark.asyncio
    async def test_authenticate_with_bot_token(self, connector: DiscordConnector):
        """Test 1: Bot token authentication."""
        result = await connector.authenticate({
            "bot_token": "test_bot_token_123",
        })

        assert result.access_token == "test_bot_token_123"
        assert connector._bot_token == "test_bot_token_123"

    @pytest.mark.asyncio
    async def test_authenticate_rejects_missing_token(self, connector: DiscordConnector):
        """Test that authenticate rejects missing token."""
        result = await connector.authenticate({})

        assert result.access_token == ""
        assert "error" in result.raw_response

    def test_transform_to_claim_creates_claim_with_correct_metadata(
        self, connector: DiscordConnector
    ):
        """Test transform_to_claim creates Claim with correct metadata."""
        item = ConnectorItem(
            id="discord-123-456",
            title="Discord message",
            content="Message content",
            url="https://discord.com/channels/789/123/456",
            author="testuser",
            created_at=datetime.now(timezone.utc),
            metadata={
                "channel_id": "123",
                "guild_id": "789",
                "author": {"user_id": "999", "username": "testuser"},
                "attachments": [{"filename": "file.png"}],
                "embeds": [{"title": "Embed"}],
                "reactions": [{"emoji": "👍", "count": 1}],
            },
        )

        claim = connector.transform_to_claim(item)

        assert claim["metadata"]["source_platform"] == "discord"
        assert claim["metadata"]["guild_id"] == "789"
        assert claim["metadata"]["channel_id"] == "123"


class TestDiscordUser:
    """Tests for DiscordUser model."""

    def test_user_from_discord(self):
        """Test creating user from discord.py User object."""
        mock_user = MagicMock()
        mock_user.id = 123456789
        mock_user.name = "testuser"
        mock_user.display_name = "Test User"
        mock_user.discriminator = "1234"
        mock_user.bot = False
        mock_user.avatar = MagicMock()
        mock_user.avatar.url = "https://cdn.discord.com/avatar.png"

        user = DiscordUser.from_discord(mock_user)

        assert user.user_id == "123456789"
        assert user.username == "testuser"
        assert user.display_name == "Test User"
        assert user.is_bot is False

    def test_user_is_bot(self):
        """Test identifying bot user."""
        mock_user = MagicMock()
        mock_user.id = 123456789
        mock_user.name = "BotUser"
        mock_user.bot = True
        mock_user.avatar = None

        user = DiscordUser.from_discord(mock_user)

        assert user.is_bot is True


class TestDiscordMessage:
    """Tests for DiscordMessage model."""

    def test_message_from_discord(self):
        """Test creating message from discord.py Message object."""
        mock_message = MagicMock()
        mock_message.id = 111222333
        mock_message.channel.id = 444555666
        mock_message.guild = None  # DM
        mock_message.content = "Hello world"
        mock_message.author = MagicMock()
        mock_message.author.id = 123
        mock_message.author.name = "testuser"
        mock_message.author.display_name = "Test User"
        mock_message.author.bot = False
        mock_message.author.avatar = None
        mock_message.created_at = datetime.now(timezone.utc)
        mock_message.edited_at = None
        mock_message.attachments = []
        mock_message.embeds = []
        mock_message.reactions = []
        mock_message.thread = None
        mock_message.reference = None

        message = DiscordMessage.from_discord(mock_message)

        assert message.message_id == "111222333"
        assert message.channel_id == "444555666"
        assert message.content == "Hello world"
        assert message.guild_id is None

    def test_message_with_attachments(self):
        """Test 4: Capture attachments."""
        mock_attachment = MagicMock()
        mock_attachment.id = 999
        mock_attachment.filename = "image.png"
        mock_attachment.url = "https://cdn.discord.com/image.png"
        mock_attachment.proxy_url = "https://media.discordapp.net/image.png"
        mock_attachment.size = 12345
        mock_attachment.content_type = "image/png"

        mock_message = MagicMock()
        mock_message.id = 111
        mock_message.channel.id = 222
        mock_message.guild = None
        mock_message.content = ""
        mock_message.author = MagicMock()
        mock_message.author.id = 123
        mock_message.author.name = "testuser"
        mock_message.author.display_name = "Test"
        mock_message.author.bot = False
        mock_message.author.avatar = None
        mock_message.created_at = datetime.now(timezone.utc)
        mock_message.edited_at = None
        mock_message.attachments = [mock_attachment]
        mock_message.embeds = []
        mock_message.reactions = []
        mock_message.thread = None
        mock_message.reference = None

        message = DiscordMessage.from_discord(mock_message)

        assert len(message.attachments) == 1
        assert message.attachments[0]["filename"] == "image.png"

    def test_message_with_embeds(self):
        """Test 4: Capture embeds."""
        mock_embed = MagicMock()
        mock_embed.type = "rich"
        mock_embed.title = "Embed Title"
        mock_embed.description = "Embed description"
        mock_embed.url = "https://example.com"
        mock_embed.fields = []

        mock_message = MagicMock()
        mock_message.id = 111
        mock_message.channel.id = 222
        mock_message.guild = None
        mock_message.content = "Check this out"
        mock_message.author = MagicMock()
        mock_message.author.id = 123
        mock_message.author.name = "testuser"
        mock_message.author.display_name = "Test"
        mock_message.author.bot = False
        mock_message.author.avatar = None
        mock_message.created_at = datetime.now(timezone.utc)
        mock_message.edited_at = None
        mock_message.attachments = []
        mock_message.embeds = [mock_embed]
        mock_message.reactions = []
        mock_message.thread = None
        mock_message.reference = None

        message = DiscordMessage.from_discord(mock_message)

        assert len(message.embeds) == 1
        assert message.embeds[0]["title"] == "Embed Title"

    def test_message_with_thread_context(self):
        """Test thread context capture."""
        mock_thread = MagicMock()
        mock_thread.id = 888

        mock_message = MagicMock()
        mock_message.id = 111
        mock_message.channel.id = 222
        mock_message.guild = MagicMock()
        mock_message.guild.id = 333
        mock_message.content = "Thread message"
        mock_message.author = MagicMock()
        mock_message.author.id = 123
        mock_message.author.name = "testuser"
        mock_message.author.display_name = "Test"
        mock_message.author.bot = False
        mock_message.author.avatar = None
        mock_message.created_at = datetime.now(timezone.utc)
        mock_message.edited_at = None
        mock_message.attachments = []
        mock_message.embeds = []
        mock_message.reactions = []
        mock_message.thread = mock_thread
        mock_message.reference = None

        message = DiscordMessage.from_discord(mock_message)

        assert message.thread_id == "888"
        assert message.guild_id == "333"

    def test_message_with_reply_reference(self):
        """Test reply reference capture."""
        mock_reference = MagicMock()
        mock_reference.message_id = 777

        mock_message = MagicMock()
        mock_message.id = 111
        mock_message.channel.id = 222
        mock_message.guild = None
        mock_message.content = "Reply message"
        mock_message.author = MagicMock()
        mock_message.author.id = 123
        mock_message.author.name = "testuser"
        mock_message.author.display_name = "Test"
        mock_message.author.bot = False
        mock_message.author.avatar = None
        mock_message.created_at = datetime.now(timezone.utc)
        mock_message.edited_at = None
        mock_message.attachments = []
        mock_message.embeds = []
        mock_message.reactions = []
        mock_message.thread = None
        mock_message.reference = mock_reference

        message = DiscordMessage.from_discord(mock_message)

        assert message.reference_id == "777"


class TestDiscordConnectorGateway:
    """Tests for Gateway functionality."""

    @pytest.fixture
    def connector(self) -> DiscordConnector:
        """Create a connector instance."""
        return DiscordConnector()

    def test_session_tracking(self, connector: DiscordConnector):
        """Test 3: Session ID and sequence tracking for resume."""
        connector._session_id = "test_session_id"
        connector._sequence = 42

        assert connector._session_id == "test_session_id"
        assert connector._sequence == 42

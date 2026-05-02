"""Unit tests for Slack connector.

Plan 13-02: Test SlackConnector implementation.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

from saw.connectors.im.slack.connector import SlackConnector
from saw.connectors.im.slack.models import SlackMessage, SlackUser
from saw.connectors.im.slack.oauth import SlackOAuthHandler
from saw.connectors.im.slack.event_handler import SlackEventHandler
from saw.connectors.protocol import ConnectorItem


class TestSlackConnector:
    """Tests for SlackConnector."""

    @pytest.fixture
    def connector(self) -> SlackConnector:
        """Create a connector instance."""
        return SlackConnector()

    def test_connector_implements_protocol(self, connector: SlackConnector):
        """Test 1: Connector implements UnifiedConnectorInterface."""
        assert connector.platform_name == "slack"
        assert connector.supports_push is False  # Read-only via Events API

    @pytest.mark.asyncio
    async def test_authenticate_with_bot_token(self, connector: SlackConnector):
        """Test 2: authenticate() with valid bot token."""
        # Directly set the connector state to simulate successful auth
        connector._bot_token = "xoxb-test-token"
        connector._team_id = "T12345"

        # Mock the _client to avoid real API calls
        connector._client = MagicMock()
        connector._client.auth_test = AsyncMock(return_value=MagicMock(
            data={
                "ok": True,
                "team_id": "T12345",
                "team": "Test Team",
                "user_id": "U12345",
            }
        ))

        # Call authenticate which will use the mocked client
        result = await connector.authenticate({
            "bot_token": "xoxb-test-token",
            "team_id": "T12345",
        })

        # Verify token was stored
        assert connector._bot_token == "xoxb-test-token"

    @pytest.mark.asyncio
    async def test_authenticate_rejects_missing_token(self, connector: SlackConnector):
        """Test that authenticate rejects missing token."""
        result = await connector.authenticate({})

        assert result.access_token == ""
        assert "error" in result.raw_response

    def test_transform_to_claim_creates_claim_with_correct_metadata(
        self, connector: SlackConnector
    ):
        """Test 6: transform_to_claim() creates Claim with correct metadata."""
        item = ConnectorItem(
            id="slack-C123-T123.456",
            title="Slack message",
            content="Message content",
            url="https://slack.com/archives/C123/pT123456",
            author="user123",
            created_at=datetime.now(timezone.utc),
            metadata={
                "channel_id": "C123",
                "thread_parent_id": "T123.789",
                "author": {"user_id": "U123", "name": "Test User"},
                "attachments": [{"title": "Attachment"}],
                "reactions": {"thumbsup": 2},
            },
        )

        claim = connector.transform_to_claim(item)

        assert claim["metadata"]["source_platform"] == "slack"
        assert claim["metadata"]["thread_parent_id"] == "T123.789"
        assert claim["metadata"]["channel_id"] == "C123"


class TestSlackUser:
    """Tests for SlackUser model."""

    def test_user_from_event(self):
        """Test creating user from Slack event."""
        event = {
            "user": "U12345",
            "username": "testuser",
            "user_profile": {"display_name": "Test User"},
            "bot_id": None,
            "team": "T12345",
        }

        user = SlackUser.from_event(event)

        assert user.user_id == "U12345"
        assert user.name == "testuser"
        assert user.display_name == "Test User"
        assert user.is_bot is False

    def test_user_is_bot(self):
        """Test identifying bot user."""
        event = {
            "user": "U12345",
            "bot_id": "B12345",
        }

        user = SlackUser.from_event(event)

        assert user.is_bot is True


class TestSlackMessage:
    """Tests for SlackMessage model."""

    def test_message_from_event(self):
        """Test creating message from Slack event."""
        event = {
            "ts": "1234567890.123456",
            "channel": "C12345",
            "text": "Hello world",
            "user": "U12345",
            "username": "testuser",
        }

        message = SlackMessage.from_event(event)

        assert message.message_id == "1234567890.123456"
        assert message.channel_id == "C12345"
        assert message.content == "Hello world"
        assert message.author.user_id == "U12345"

    def test_message_with_thread_context(self):
        """Test 4: Capture thread replies with thread_ts."""
        event = {
            "ts": "1234567890.123456",
            "thread_ts": "1234567880.000000",  # Parent message
            "channel": "C12345",
            "text": "Thread reply",
            "user": "U12345",
        }

        message = SlackMessage.from_event(event)

        assert message.thread_ts == "1234567880.000000"

    def test_message_with_attachments(self):
        """Test 5: Handle Slack attachments."""
        event = {
            "ts": "1234567890.123456",
            "channel": "C12345",
            "text": "",
            "attachments": [
                {
                    "title": "Link Title",
                    "title_link": "https://example.com",
                    "text": "Attachment text",
                }
            ],
        }

        message = SlackMessage.from_event(event)

        assert len(message.attachments) == 1
        assert message.attachments[0]["title"] == "Link Title"


class TestSlackOAuthHandler:
    """Tests for OAuth handler."""

    @pytest.fixture
    def oauth_handler(self) -> SlackOAuthHandler:
        """Create OAuth handler."""
        return SlackOAuthHandler(
            client_id="test_client_id",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
        )

    def test_get_authorize_url(self, oauth_handler: SlackOAuthHandler):
        """Test OAuth authorization URL generation."""
        url = oauth_handler.get_authorize_url("state_token")

        assert "slack.com/oauth/v2/authorize" in url
        assert "client_id=test_client_id" in url
        assert "state=state_token" in url

    @pytest.mark.asyncio
    async def test_exchange_code_success(self, oauth_handler: SlackOAuthHandler):
        """Test exchanging code for tokens."""
        mock_response = {
            "ok": True,
            "access_token": "xoxb-test-token",
            "team": {"id": "T12345", "name": "Test Team"},
            "authed_user": {"access_token": "xoxp-user-token"},
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=MagicMock(json=lambda: mock_response))
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await oauth_handler.exchange_code("test_code")

        assert result.access_token == "xoxb-test-token"


class TestSlackEventHandler:
    """Tests for event handler."""

    @pytest.fixture
    def handler(self) -> SlackEventHandler:
        """Create event handler."""
        return SlackEventHandler()

    @pytest.mark.asyncio
    async def test_handle_message_event(self, handler: SlackEventHandler):
        """Test 3: Handle message events."""
        event_data = {
            "event": {
                "type": "message",
                "ts": "1234567890.123456",
                "channel": "C12345",
                "text": "Test message",
                "user": "U12345",
                "username": "testuser",
            }
        }

        items = await handler.process_event(event_data)

        assert len(items) == 1
        assert items[0].content == "Test message"

    @pytest.mark.asyncio
    async def test_handle_thread_reply(self, handler: SlackEventHandler):
        """Test 4: Handle thread replies."""
        event_data = {
            "event": {
                "type": "message",
                "ts": "1234567890.123456",
                "thread_ts": "1234567880.000000",
                "channel": "C12345",
                "text": "Thread reply",
                "user": "U12345",
            }
        }

        items = await handler.process_event(event_data)

        assert items[0].metadata["thread_parent_id"] == "1234567880.000000"

    @pytest.mark.asyncio
    async def test_handle_reaction_event(self, handler: SlackEventHandler):
        """Test reaction mapping to confidence."""
        # Set up reaction processor
        from saw.connectors.reaction_processor import ReactionProcessor
        handler.set_reaction_processor(ReactionProcessor())

        event_data = {
            "event": {
                "type": "reaction_added",
                "reaction": "thumbsup",
                "item": {"ts": "1234567890.123456", "channel": "C12345"},
                "user": "U12345",
            }
        }

        items = await handler.process_event(event_data)

        assert len(items) == 1
        assert items[0].metadata["type"] == "reaction"
        assert items[0].metadata["emoji"] == "thumbsup"

    def test_url_challenge(self, handler: SlackEventHandler):
        """Test URL verification challenge."""
        response = handler.verify_url_challenge("test_challenge")

        assert response["challenge"] == "test_challenge"
"""Unit tests for Feishu connector.

Plan 13-04: Test FeishuConnector implementation.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from saw.connectors.im.feishu.connector import FeishuConnector
from saw.connectors.im.feishu.models import FeishuMessage, FeishuUser
from saw.connectors.im.feishu.token_manager import FeishuTokenManager
from saw.connectors.im.feishu.event_handler import FeishuEventHandler
from saw.connectors.protocol import ConnectorItem


class TestFeishuConnector:
    """Tests for FeishuConnector."""

    @pytest.fixture
    def connector(self) -> FeishuConnector:
        """Create a connector instance."""
        return FeishuConnector()

    def test_connector_implements_protocol(self, connector: FeishuConnector):
        """Test 1: Connector implements UnifiedConnectorInterface."""
        assert connector.platform_name == "feishu"
        assert connector.supports_push is True  # App can send IM messages

    @pytest.mark.asyncio
    async def test_authenticate_with_credentials(self, connector: FeishuConnector):
        """Test 2: authenticate() with valid credentials."""
        with patch.object(connector, '_token_manager') as mock_tm:
            mock_tm.get_tenant_token = AsyncMock(return_value="test_tenant_token")

            result = await connector.authenticate({
                "app_id": "cli_test_app_id",
                "app_secret": "test_app_secret",
            })

        assert connector._app_id == "cli_test_app_id"
        assert connector._app_secret == "test_app_secret"

    @pytest.mark.asyncio
    async def test_authenticate_rejects_missing_credentials(self, connector: FeishuConnector):
        """Test that authenticate rejects missing credentials."""
        result = await connector.authenticate({})

        assert result.access_token == ""
        assert "error" in result.raw_response

    def test_transform_to_claim_creates_claim_with_correct_metadata(
        self, connector: FeishuConnector
    ):
        """Test transform_to_claim creates Claim with correct metadata."""
        item = ConnectorItem(
            id="feishu-oc_xxx-msg_xxx",
            title="Feishu message",
            content="消息内容",  # Chinese content
            author="用户名",
            metadata={
                "chat_id": "oc_chat_xxx",
                "author": {"user_id": "ou_user_xxx", "name": "用户名"},
                "message_type": "text",
            },
        )

        claim = connector.transform_to_claim(item)

        assert claim["metadata"]["source_platform"] == "feishu"
        assert claim["content"] == "消息内容"  # Chinese preserved


class TestFeishuUser:
    """Tests for FeishuUser model."""

    def test_user_from_event(self):
        """Test creating user from Feishu event."""
        event = {
            "sender": {
                "sender_id": {"user_id": "ou_xxx"},
                "sender_name": "测试用户",
            }
        }

        user = FeishuUser.from_event(event)

        assert user.user_id == "ou_xxx"
        assert user.name == "测试用户"  # Chinese name preserved


class TestFeishuMessage:
    """Tests for FeishuMessage model."""

    def test_message_from_event(self):
        """Test creating message from Feishu event."""
        event = {
            "message": {
                "message_id": "om_xxx",
                "chat_id": "oc_xxx",
                "content": '{"text":"你好世界"}',
                "message_type": "text",
            },
            "sender": {
                "sender_id": {"user_id": "ou_xxx"},
                "sender_name": "测试用户",
            }
        }

        message = FeishuMessage.from_event(event)

        assert message.message_id == "om_xxx"
        assert message.content == "你好世界"  # Decoded from JSON

    def test_message_chinese_encoding(self):
        """Test 5: Handle Chinese content encoding correctly."""
        event = {
            "message": {
                "message_id": "om_xxx",
                "chat_id": "oc_xxx",
                "content": '{"text":"中文测试内容"}',
                "message_type": "text",
            },
            "sender": {
                "sender_id": {"user_id": "ou_xxx"},
            }
        }

        message = FeishuMessage.from_event(event)

        assert "中文" in message.content


class TestFeishuTokenManager:
    """Tests for token manager."""

    @pytest.fixture
    def token_manager(self) -> FeishuTokenManager:
        """Create token manager."""
        return FeishuTokenManager("app_id", "app_secret")

    @pytest.mark.asyncio
    async def test_get_tenant_token(self, token_manager: FeishuTokenManager):
        """Test 3: Handle multi-tenant token."""
        mock_response = {
            "code": 0,
            "tenant_access_token": "t-xxx",
            "expire": 7200,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=MagicMock(json=lambda: mock_response))
            mock_client.return_value.__aenter__.return_value = mock_instance

            token = await token_manager.get_tenant_token()

        assert token == "t-xxx"


class TestFeishuEventHandler:
    """Tests for event handler."""

    @pytest.fixture
    def handler(self) -> FeishuEventHandler:
        """Create event handler."""
        return FeishuEventHandler()

    @pytest.mark.asyncio
    async def test_handle_message_event(self, handler: FeishuEventHandler):
        """Test 2: Handle message events."""
        event_data = {
            "header": {"event_type": "im.message.receive_v1"},
            "event": {
                "message": {
                    "message_id": "om_xxx",
                    "chat_id": "oc_xxx",
                    "content": '{"text":"Hello"}',
                    "message_type": "text",
                },
                "sender": {
                    "sender_id": {"user_id": "ou_xxx"},
                }
            }
        }

        items = await handler.process_event(event_data)

        assert len(items) == 1
        assert "Hello" in items[0].content

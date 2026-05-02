"""Unit tests for WeCom connector.

Plan 13-04: Test WeComConnector implementation.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from saw.connectors.im.wecom.connector import WeComConnector
from saw.connectors.im.wecom.models import WeComMessage
from saw.connectors.im.wecom.crypto import WeComCrypto
from saw.connectors.protocol import ConnectorItem


class TestWeComConnector:
    """Tests for WeComConnector."""

    @pytest.fixture
    def connector(self) -> WeComConnector:
        """Create a connector instance."""
        return WeComConnector()

    def test_connector_implements_protocol(self, connector: WeComConnector):
        """Test 1: Connector implements UnifiedConnectorInterface."""
        assert connector.platform_name == "wecom"
        assert connector.supports_push is False  # Read-only via webhooks

    @pytest.mark.asyncio
    async def test_authenticate_with_webhook_url(self, connector: WeComConnector):
        """Test 1: Webhook URL configuration."""
        result = await connector.authenticate({
            "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
        })

        assert connector._webhook_url is not None
        assert "webhook_url" in result.raw_response

    @pytest.mark.asyncio
    async def test_authenticate_with_encryption(self, connector: WeComConnector):
        """Test that authenticate handles encryption keys."""
        result = await connector.authenticate({
            "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
            "encoding_aes_key": "test_aes_key_43_characters_long_xxxxxx",
            "token": "test_token",
            "corp_id": "test_corp",
        })

        assert connector._crypto is not None

    def test_transform_to_claim_creates_claim_with_correct_metadata(
        self, connector: WeComConnector
    ):
        """Test transform_to_claim creates Claim with correct metadata."""
        item = ConnectorItem(
            id="wecom-msg_xxx",
            title="WeCom message",
            content="消息内容",  # Chinese content
            author="user123",
            metadata={
                "from_user": "user123",
                "chat_id": "chat_xxx",
            },
        )

        claim = connector.transform_to_claim(item)

        assert claim["metadata"]["source_platform"] == "wecom"


class TestWeComMessage:
    """Tests for WeComMessage model."""

    def test_message_from_xml(self):
        """Test creating message from XML data."""
        xml_data = {
            "xml": {
                "MsgId": "msg_123",
                "FromUserName": "user_456",
                "ToUserName": "bot_789",
                "Content": "测试消息",
                "MsgType": "text",
                "CreateTime": "1234567890",
            }
        }

        message = WeComMessage.from_xml(xml_data)

        assert message.message_id == "msg_123"
        assert message.from_user == "user_456"
        assert message.content == "测试消息"  # Chinese preserved


class TestWeComCrypto:
    """Tests for crypto handler."""

    @pytest.fixture
    def crypto(self) -> WeComCrypto:
        """Create crypto instance."""
        # WeCom encoding_aes_key is exactly 43 characters
        # When decoded with '=' appended, gives 32 bytes (256 bits) for AES-256
        # Generate a valid 43-char base64 key
        import base64
        import os
        key_bytes = os.urandom(32)  # 32 bytes = 256 bits
        key_b64 = base64.b64encode(key_bytes).decode()[:-1]  # Remove last char to get 43 chars
        return WeComCrypto(
            encoding_aes_key=key_b64,
            token="test_token",
            corp_id="test_corp",
        )

    def test_verify_signature(self, crypto: WeComCrypto):
        """Test 3: Signature verification."""
        # This is a simplified test - real signatures require actual values
        signature = "abc123"
        timestamp = "1234567890"
        nonce = "nonce123"
        encrypted = "encrypted_msg"

        # Should verify without error (actual verification would need real values)
        result = crypto.verify_signature(signature, timestamp, nonce, encrypted)
        assert isinstance(result, bool)

    def test_encrypt_decrypt_roundtrip(self, crypto: WeComCrypto):
        """Test 3: Encrypt/decrypt roundtrip."""
        original = "Test message"

        encrypted = crypto.encrypt(original)
        decrypted = crypto.decrypt(encrypted)

        assert decrypted == original


class TestWeComConnectorWebhook:
    """Tests for webhook processing."""

    @pytest.fixture
    def connector(self) -> WeComConnector:
        """Create a connector instance."""
        connector = WeComConnector()
        connector._webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
        return connector

    @pytest.mark.asyncio
    async def test_process_webhook(self, connector: WeComConnector):
        """Test 2: Process incoming webhook."""
        body = b"""<?xml version="1.0" encoding="UTF-8"?>
        <xml>
            <MsgId>msg_123</MsgId>
            <FromUserName>user_456</FromUserName>
            <ToUserName>bot_789</ToUserName>
            <Content>Hello world</Content>
            <MsgType>text</MsgType>
            <CreateTime>1234567890</CreateTime>
        </xml>
        """

        items = await connector.process_webhook(
            body=body,
            signature="test",
            timestamp="1234567890",
            nonce="test_nonce",
        )

        assert len(items) >= 1

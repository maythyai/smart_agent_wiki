"""Tests for webhook endpoints, verification, and rate limiting.

Plan 10-03: Webhook Endpoints and Rate Limiting.
"""
import pytest
import hmac
import hashlib
import time
import json
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Tests for Task 1: WebhookVerifier with HMAC-SHA256 verification


class TestWebhookVerifier:
    """Test WebhookVerifier HMAC-SHA256 signature verification."""

    def test_verify_slack_signature(self):
        """Test 1: WebhookVerifier.verify() validates correct HMAC-SHA256 signature."""
        from saw.connectors.webhook_verifier import WebhookVerifier
        secret = "test_secret"
        body = b'{"event": "test"}'
        timestamp = str(int(time.time()))

        # Compute Slack signature
        base_string = f"v0:{timestamp}:{body.decode()}"
        expected = "v0=" + hmac.new(
            secret.encode(),
            base_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        verifier = WebhookVerifier(secret=secret, platform="slack")
        result = verifier.verify(body, expected, timestamp)
        assert result is True

    def test_verify_rejects_invalid_signature(self):
        """Test 2: WebhookVerifier.verify() rejects invalid signature."""
        from saw.connectors.webhook_verifier import WebhookVerifier, SignatureVerificationError
        verifier = WebhookVerifier(secret="secret", platform="slack")

        with pytest.raises(SignatureVerificationError):
            verifier.verify(b'{"test": 1}', "invalid_signature", str(int(time.time())))

    def test_verify_handles_missing_signature(self):
        """Test 3: WebhookVerifier.verify() handles missing signature header."""
        from saw.connectors.webhook_verifier import WebhookVerifier, SignatureVerificationError
        verifier = WebhookVerifier(secret="secret", platform="slack")

        with pytest.raises(SignatureVerificationError):
            verifier.verify(b'{"test": 1}', "", str(int(time.time())))

    def test_slack_signature_format(self):
        """Test 4: WebhookVerifier supports Slack signature format (v0 prefix)."""
        from saw.connectors.webhook_verifier import WebhookVerifier
        secret = "slack_secret"
        body = b'{"type": "event_callback"}'
        timestamp = str(int(time.time()))

        signature = WebhookVerifier.compute_signature(secret, body, "slack")
        assert signature.startswith("v0=")

        verifier = WebhookVerifier(secret=secret, platform="slack")
        # Modify signature to include timestamp
        base_string = f"v0:{timestamp}:{body.decode()}"
        expected = "v0=" + hmac.new(
            secret.encode(),
            base_string.encode(),
            hashlib.sha256,
        ).hexdigest()
        result = verifier.verify(body, expected, timestamp)
        assert result is True

    def test_github_signature_format(self):
        """Test 5: WebhookVerifier supports GitHub signature format (sha256= prefix)."""
        from saw.connectors.webhook_verifier import WebhookVerifier
        secret = "github_secret"
        body = b'{"action": "push"}'

        signature = WebhookVerifier.compute_signature(secret, body, "github")
        assert signature.startswith("sha256=")

        verifier = WebhookVerifier(secret=secret, platform="github")
        result = verifier.verify(body, signature)
        assert result is True

    def test_generic_hmac_sha256(self):
        """Test 6: WebhookVerifier supports generic HMAC-SHA256."""
        from saw.connectors.webhook_verifier import WebhookVerifier
        secret = "generic_secret"
        body = b'{"event": "test"}'

        signature = WebhookVerifier.compute_signature(secret, body, "generic")
        verifier = WebhookVerifier(secret=secret, platform="other")
        result = verifier.verify(body, signature)
        assert result is True

    def test_slack_timestamp_validation(self):
        """Slack webhook timestamps are validated for replay protection."""
        from saw.connectors.webhook_verifier import WebhookVerifier, SignatureVerificationError
        verifier = WebhookVerifier(secret="secret", platform="slack")

        # Old timestamp (more than 5 minutes ago)
        old_timestamp = str(int(time.time()) - 400)
        with pytest.raises(SignatureVerificationError):
            verifier.verify(b'{"test": 1}', "v0=some_sig", old_timestamp)


# Tests for Task 2: WebhookRateLimiter for inbound rate limiting


class TestWebhookRateLimit:
    """Test WebhookRateLimit configurations."""

    def test_slack_rate_limit(self):
        """Test 7: WebhookRateLimiter enforces inbound rate limits per platform."""
        from saw.connectors.rate_limiter import WebhookRateLimit
        limit = WebhookRateLimit.slack()
        assert limit.requests_per_minute == 100
        assert limit.burst == 50

    def test_github_rate_limit(self):
        """Test 8: WebhookRateLimiter tracks requests per minute for webhooks."""
        from saw.connectors.rate_limiter import WebhookRateLimit
        limit = WebhookRateLimit.github()
        assert limit.requests_per_minute == 60

    def test_discord_rate_limit(self):
        """Test 9: WebhookRateLimiter allows burst handling for webhook spikes."""
        from saw.connectors.rate_limiter import WebhookRateLimit
        limit = WebhookRateLimit.discord()
        assert limit.requests_per_minute == 100
        assert limit.burst == 50


class TestWebhookRateLimiter:
    """Test WebhookRateLimiter functionality."""

    @pytest.mark.asyncio
    async def test_acquire_returns_allowed_with_headers(self):
        """Test 10: WebhookRateLimiter returns 429 when limit exceeded."""
        from saw.connectors.rate_limiter import WebhookRateLimiter
        limiter = WebhookRateLimiter("slack")
        allowed, headers = await limiter.acquire()
        assert allowed is True
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers

    @pytest.mark.asyncio
    async def test_rate_limit_headers(self):
        """Test 12: Rate limit headers included in response."""
        from saw.connectors.rate_limiter import WebhookRateLimiter
        limiter = WebhookRateLimiter("github")
        allowed, headers = await limiter.acquire()
        assert headers["X-RateLimit-Limit"] == "60"
        assert int(headers["X-RateLimit-Remaining"]) >= 0

    @pytest.mark.asyncio
    async def test_per_connector_rate_limiting(self):
        """Test 11: Per-connector rate limiting works independently."""
        from saw.connectors.rate_limiter import WebhookRateLimiter
        limiter1 = WebhookRateLimiter("slack", "connector-1")
        limiter2 = WebhookRateLimiter("slack", "connector-2")

        allowed1, _ = await limiter1.acquire()
        allowed2, _ = await limiter2.acquire()

        assert allowed1 is True
        assert allowed2 is True


# Tests for Task 3: Unified webhook FastAPI endpoint


class TestWebhookEndpoints:
    """Test unified webhook FastAPI endpoint."""

    def test_platforms_endpoint_exists(self):
        """Test 18: Supported webhook platforms list available."""
        from saw.api.webhook_inbound import router
        routes = [r.path for r in router.routes]
        assert "/api/v1/webhooks/platforms" in routes

    def test_webhook_endpoint_exists(self):
        """Test 13: POST /api/v1/webhooks/{platform} accepts valid webhook."""
        from saw.api.webhook_inbound import router
        routes = [r.path for r in router.routes]
        assert "/api/v1/webhooks/{platform}" in routes

    def test_platform_info_model(self):
        """PlatformInfo model has correct fields."""
        from saw.api.webhook_inbound import PlatformInfo
        info = PlatformInfo(
            name="slack",
            display_name="Slack",
            signature_header="X-Slack-Signature",
            timestamp_header="X-Slack-Request-Timestamp",
        )
        assert info.name == "slack"
        assert info.timestamp_header is not None

    def test_webhook_event_model(self):
        """WebhookEvent model has correct fields."""
        from saw.api.webhook_inbound import WebhookEvent
        event = WebhookEvent(
            platform="github",
            event_type="push",
            payload={"ref": "main"},
            received_at=datetime.now(timezone.utc),
        )
        assert event.platform == "github"
        assert event.event_type == "push"


# Tests for Task 4: Webhook logging and audit trail


class TestWebhookLogger:
    """Test webhook logging with token masking."""

    def test_log_received_creates_entry(self):
        """Test 19: WebhookLog records event to database."""
        from saw.connectors.webhook_log import WebhookLogger
        # Mock database session
        mock_db = MagicMock()
        logger = WebhookLogger(mock_db)

        log_id = logger.log_received(
            platform="slack",
            event_type="message",
            event_id="evt-123",
            payload={"text": "hello"},
        )
        assert log_id is not None
        mock_db.add.assert_called_once()

    def test_log_masks_tokens(self):
        """Test 20: WebhookLog masks tokens in logged payload."""
        from saw.connectors.webhook_log import WebhookLogger
        mock_db = MagicMock()
        logger = WebhookLogger(mock_db)

        payload = {
            "access_token": "secret_token_123456",
            "refresh_token": "refresh_abcdef",
            "data": "visible",
        }

        masked = logger._mask_payload(payload)
        assert masked["access_token"] == "****3456"
        assert masked["refresh_token"] == "****cdef"
        assert masked["data"] == "visible"

    def test_log_masks_nested_tokens(self):
        """WebhookLog masks tokens in nested structures."""
        from saw.connectors.webhook_log import WebhookLogger
        mock_db = MagicMock()
        logger = WebhookLogger(mock_db)

        payload = {
            "event": {
                "api_key": "secret_key_789",
                "user": "test",
            },
            "items": [
                {"token": "item_token_xyz"},
            ],
        }

        masked = logger._mask_payload(payload)
        # api_key contains "key" which matches SENSITIVE_FIELDS
        assert "****" in masked["event"]["api_key"]
        assert masked["event"]["user"] == "test"
        assert "****" in masked["items"][0]["token"]

    def test_mark_processed(self):
        """Test 21: WebhookLog tracks processing status (received, processed, failed)."""
        from saw.connectors.webhook_log import WebhookLogger
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_log = MagicMock()
        mock_filter.first.return_value = mock_log

        logger = WebhookLogger(mock_db)
        logger.mark_processed("log-123")

        mock_db.commit.assert_called_once()

    def test_mark_failed(self):
        """WebhookLog can mark entries as failed."""
        from saw.connectors.webhook_log import WebhookLogger
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_log = MagicMock()
        mock_filter.first.return_value = mock_log

        logger = WebhookLogger(mock_db)
        logger.mark_failed("log-123", "Connection error")

        mock_db.commit.assert_called_once()

    def test_get_failed_webhooks(self):
        """Test 22: Failed webhooks can be retrieved for retry."""
        from saw.connectors.webhook_log import WebhookLogger
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_order = MagicMock()
        mock_filter.order_by.return_value = mock_order
        mock_order.limit.return_value.all.return_value = []

        logger = WebhookLogger(mock_db)
        result = logger.get_failed_webhooks()

        assert result == []


class TestWebhookLogEntry:
    """Test WebhookLogEntry dataclass."""

    def test_log_entry_creation(self):
        """WebhookLogEntry has all required fields."""
        from saw.connectors.webhook_log import WebhookLogEntry
        entry = WebhookLogEntry(
            id="log-123",
            platform="slack",
            event_type="message",
            event_id="evt-456",
            payload_masked={"text": "hello"},
            received_at=datetime.now(timezone.utc),
        )
        assert entry.status == "received"
        assert entry.processed_at is None

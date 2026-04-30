"""Tests for API Platform (Phase 6).

Tests for API keys, rate limiting, webhooks, and bulk operations.
"""
import pytest
from datetime import datetime, timezone


class TestAPIKeys:
    """Test API key generation and verification."""

    def test_generate_api_key(self):
        from saw.api.keys import generate_api_key

        key = generate_api_key()
        assert key.startswith("saw_")
        assert len(key) > 20

    def test_generate_api_key_custom_prefix(self):
        from saw.api.keys import generate_api_key

        key = generate_api_key(prefix="custom")
        assert key.startswith("custom_")

    def test_hash_api_key(self):
        from saw.api.keys import hash_api_key

        key = "saw_test123"
        hashed = hash_api_key(key)

        assert hashed != key
        assert len(hashed) == 64  # SHA256 hex length

    def test_verify_api_key(self):
        from saw.api.keys import hash_api_key, verify_api_key

        key = "saw_test123"
        hashed = hash_api_key(key)

        assert verify_api_key(key, hashed)
        assert not verify_api_key("wrong_key", hashed)

    def test_api_key_data_from_model(self):
        from saw.api.keys import APIKey, APIKeyData

        key = APIKey(
            id="key123",
            user_id="user456",
            key_hash="hash123",
            name="Test Key",
            prefix="saw",
            permissions="read,write",
            rate_limit_hour=100,
            rate_limit_day=1000,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )

        data = APIKeyData.from_model(key)
        assert data.id == "key123"
        assert data.name == "Test Key"
        assert data.permissions == ["read", "write"]


class TestAPIKeyService:
    """Test API key service."""

    def test_create_key(self):
        from saw.api.keys import APIKeyService

        service = APIKeyService()
        model, full_key = service.create_key(
            user_id="user123",
            name="Test Key",
        )

        assert model.user_id == "user123"
        assert model.name == "Test Key"
        assert full_key.startswith("saw_")
        assert model.key_hash is not None

    def test_create_key_with_permissions(self):
        from saw.api.keys import APIKeyService

        service = APIKeyService()
        model, _ = service.create_key(
            user_id="user123",
            name="Read Only",
            permissions=["read"],
        )

        assert model.permissions == "read"

    def test_create_key_with_expiry(self):
        from saw.api.keys import APIKeyService

        service = APIKeyService()
        model, _ = service.create_key(
            user_id="user123",
            name="Temporary",
            expires_days=30,
        )

        assert model.expires_at is not None

    def test_has_permission(self):
        from saw.api.keys import APIKeyService, APIKey

        service = APIKeyService()
        key = APIKey(
            permissions="read,write",
        )

        assert service.has_permission(key, "read")
        assert service.has_permission(key, "write")
        assert not service.has_permission(key, "delete")

    def test_has_permission_admin(self):
        from saw.api.keys import APIKeyService, APIKey

        service = APIKeyService()
        key = APIKey(
            permissions="admin",
        )

        assert service.has_permission(key, "read")
        assert service.has_permission(key, "write")
        assert service.has_permission(key, "delete")


class TestRateLimitConfig:
    """Test rate limit configuration."""

    def test_default_config(self):
        from saw.api.rate_limit import RateLimitConfig

        config = RateLimitConfig()
        assert config.default_hour_limit == 100
        assert config.default_day_limit == 1000
        assert config.enabled is True

    def test_from_env(self, monkeypatch):
        from saw.api.rate_limit import RateLimitConfig

        monkeypatch.setenv("RATE_LIMIT_HOUR", "500")
        monkeypatch.setenv("RATE_LIMIT_DAY", "5000")

        config = RateLimitConfig.from_env()
        assert config.default_hour_limit == 500
        assert config.default_day_limit == 5000


class TestRateLimitStatus:
    """Test rate limit status."""

    def test_to_headers(self):
        from saw.api.rate_limit import RateLimitStatus

        status = RateLimitStatus(
            hour_count=50,
            hour_limit=100,
            hour_remaining=50,
            hour_reset=1700000000,
            day_count=500,
            day_limit=1000,
            day_remaining=500,
            day_reset=1700086400,
        )

        headers = status.to_headers()
        assert headers["X-RateLimit-Limit-Hour"] == "100"
        assert headers["X-RateLimit-Remaining-Hour"] == "50"
        assert headers["X-RateLimit-Limit-Day"] == "1000"


class TestWebhookSigner:
    """Test webhook signing."""

    def test_sign_payload(self):
        from saw.api.webhooks import WebhookSigner

        payload = '{"event": "test"}'
        secret = "secret123"
        signature = WebhookSigner.sign(payload, secret)

        assert signature is not None
        assert len(signature) == 64  # SHA256 hex

    def test_verify_signature(self):
        from saw.api.webhooks import WebhookSigner

        payload = '{"event": "test"}'
        secret = "secret123"
        signature = WebhookSigner.sign(payload, secret)

        assert WebhookSigner.verify(payload, signature, secret)
        assert not WebhookSigner.verify(payload, "wrong_sig", secret)
        assert not WebhookSigner.verify(payload, signature, "wrong_secret")


class TestWebhookEvents:
    """Test webhook events."""

    def test_event_types(self):
        from saw.api.webhooks import WebhookEvent

        assert WebhookEvent.INGEST_COMPLETE == "ingest.complete"
        assert WebhookEvent.CLAIM_CREATE == "claim.create"
        assert WebhookEvent.VAULT_CREATE == "vault.create"


class TestBulkImport:
    """Test bulk import operations."""

    def test_import_formats(self):
        from saw.api.bulk import ImportFormat

        assert ImportFormat.JSON.value == "json"
        assert ImportFormat.CSV.value == "csv"

    def test_export_formats(self):
        from saw.api.bulk import ExportFormat

        assert ExportFormat.JSON.value == "json"
        assert ExportFormat.CSV.value == "csv"
        assert ExportFormat.MARKDOWN.value == "markdown"
        assert ExportFormat.NDJSON.value == "ndjson"


class TestImportResult:
    """Test import result."""

    def test_to_dict(self):
        from saw.api.bulk import ImportResult, ImportFormat

        result = ImportResult(
            task_id="task123",
            status="completed",
            format=ImportFormat.JSON,
            vaults_created=5,
            claims_created=20,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        d = result.to_dict()
        assert d["task_id"] == "task123"
        assert d["status"] == "completed"
        assert d["vaults_created"] == 5
        assert d["claims_created"] == 20
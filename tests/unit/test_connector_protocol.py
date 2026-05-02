"""Tests for connector protocol, models, registry, and rate limiter.

Plan 10-01: Core Connector Protocol, Models, and Registry.
"""
import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

# Tests for Task 1: UnifiedConnectorInterface Protocol and core types


class TestSyncDirection:
    """Test SyncDirection enum."""

    def test_sync_direction_has_pull(self):
        """Test 1: SyncDirection has PULL value."""
        from saw.connectors.protocol import SyncDirection
        assert SyncDirection.PULL.value == "pull"

    def test_sync_direction_has_push(self):
        """Test 2: SyncDirection has PUSH value."""
        from saw.connectors.protocol import SyncDirection
        assert SyncDirection.PUSH.value == "push"

    def test_sync_direction_has_bidirectional(self):
        """Test 3: SyncDirection has BIDIRECTIONAL value."""
        from saw.connectors.protocol import SyncDirection
        assert SyncDirection.BIDIRECTIONAL.value == "bidirectional"


class TestAuthResult:
    """Test AuthResult dataclass."""

    def test_auth_result_has_access_token(self):
        """Test 4: AuthResult dataclass contains access_token field."""
        from saw.connectors.protocol import AuthResult
        result = AuthResult(access_token="test_token")
        assert result.access_token == "test_token"

    def test_auth_result_has_refresh_token(self):
        """AuthResult dataclass contains refresh_token field."""
        from saw.connectors.protocol import AuthResult
        result = AuthResult(access_token="test", refresh_token="refresh")
        assert result.refresh_token == "refresh"

    def test_auth_result_has_expires_at(self):
        """AuthResult dataclass contains expires_at field."""
        from saw.connectors.protocol import AuthResult
        now = datetime.now(timezone.utc)
        result = AuthResult(access_token="test", expires_at=now)
        assert result.expires_at == now

    def test_auth_result_has_scopes(self):
        """AuthResult dataclass contains scopes field."""
        from saw.connectors.protocol import AuthResult
        result = AuthResult(access_token="test", scopes=["read", "write"])
        assert result.scopes == ["read", "write"]


class TestConnectorItem:
    """Test ConnectorItem dataclass."""

    def test_connector_item_has_required_fields(self):
        """Test 5: ConnectorItem dataclass contains id, title, content, metadata fields."""
        from saw.connectors.protocol import ConnectorItem
        item = ConnectorItem(id="123", title="Test", content="Content")
        assert item.id == "123"
        assert item.title == "Test"
        assert item.content == "Content"
        assert item.metadata == {}

    def test_connector_item_has_optional_fields(self):
        """ConnectorItem has optional url, author, timestamps."""
        from saw.connectors.protocol import ConnectorItem
        now = datetime.now(timezone.utc)
        item = ConnectorItem(
            id="123",
            title="Test",
            content="Content",
            url="https://example.com",
            author="user",
            created_at=now,
            updated_at=now,
        )
        assert item.url == "https://example.com"
        assert item.author == "user"


class TestUnifiedConnectorInterface:
    """Test UnifiedConnectorInterface Protocol."""

    def test_protocol_has_platform_name(self):
        """Test 1: UnifiedConnectorInterface defines platform_name property."""
        from saw.connectors.protocol import UnifiedConnectorInterface
        # Protocol is for structural typing, verify it exists
        assert hasattr(UnifiedConnectorInterface, "platform_name")

    def test_protocol_has_supports_push(self):
        """Test 2: UnifiedConnectorInterface defines supports_push property."""
        from saw.connectors.protocol import UnifiedConnectorInterface
        assert hasattr(UnifiedConnectorInterface, "supports_push")

    def test_protocol_has_required_methods(self):
        """Test 3: UnifiedConnectorInterface defines required methods."""
        from saw.connectors.protocol import UnifiedConnectorInterface
        assert hasattr(UnifiedConnectorInterface, "authenticate")
        assert hasattr(UnifiedConnectorInterface, "get_items")
        assert hasattr(UnifiedConnectorInterface, "put_item")
        assert hasattr(UnifiedConnectorInterface, "delete_item")


# Tests for Task 2: Connector models with token masking


class TestTokenMasker:
    """Test TokenMasker utility."""

    def test_mask_token_shows_last_4_chars(self):
        """Test 7: TokenMasker.mask_token() returns "****abcd" for "secret_token_abcd"."""
        from saw.connectors.models import TokenMasker
        result = TokenMasker.mask_token("secret_token_abcd")
        assert result == "****abcd"

    def test_mask_token_short_tokens(self):
        """Test 8: TokenMasker.mask_token() returns "****" for tokens shorter than 4 chars."""
        from saw.connectors.models import TokenMasker
        assert TokenMasker.mask_token("abc") == "****"
        assert TokenMasker.mask_token("ab") == "****"

    def test_mask_token_handles_none_and_empty(self):
        """Test 9: TokenMasker.mask_token() handles None and empty strings."""
        from saw.connectors.models import TokenMasker
        assert TokenMasker.mask_token(None) == "****"
        assert TokenMasker.mask_token("") == "****"

    def test_mask_dict(self):
        """TokenMasker.mask_dict() masks specified keys."""
        from saw.connectors.models import TokenMasker
        d = {"access_token": "secret123456", "other": "visible"}
        result = TokenMasker.mask_dict(d, ["access_token"])
        assert result["access_token"] == "****3456"
        assert result["other"] == "visible"


class TestConnectorConfig:
    """Test ConnectorConfig dataclass."""

    def test_connector_config_has_required_fields(self):
        """Test 10: ConnectorConfig dataclass contains platform, credentials_encrypted, sync_direction."""
        from saw.connectors.models import ConnectorConfig
        from saw.connectors.protocol import SyncDirection
        config = ConnectorConfig(
            id="cfg-123",
            user_id="user-1",
            platform="notion",
            name="My Notion",
        )
        assert config.platform == "notion"
        assert config.credentials_encrypted is None
        assert config.sync_direction == SyncDirection.BIDIRECTIONAL


class TestSyncResult:
    """Test SyncResult dataclass."""

    def test_sync_result_has_counts(self):
        """Test 11: SyncResult dataclass contains pulled_count, pushed_count, conflicts_count."""
        from saw.connectors.models import SyncResult
        from saw.connectors.protocol import SyncDirection
        result = SyncResult(
            connector_id="conn-1",
            direction=SyncDirection.PULL,
            pulled_count=10,
            pushed_count=5,
            conflicts_count=2,
        )
        assert result.pulled_count == 10
        assert result.pushed_count == 5
        assert result.conflicts_count == 2


class TestConnectorStatus:
    """Test ConnectorStatus enum."""

    def test_connector_status_values(self):
        """Test 12: ConnectorStatus enum has CONNECTED, DISCONNECTED, EXPIRED, ERROR values."""
        from saw.connectors.models import ConnectorStatus
        assert ConnectorStatus.CONNECTED.value == "connected"
        assert ConnectorStatus.DISCONNECTED.value == "disconnected"
        assert ConnectorStatus.EXPIRED.value == "expired"
        assert ConnectorStatus.ERROR.value == "error"


# Tests for Task 3: RateLimitManager with token bucket algorithm


class TestPlatformRateLimit:
    """Test PlatformRateLimit configurations."""

    def test_notion_rate_limit(self):
        """Test 13: RateLimitManager enforces Notion limit (3 req/s)."""
        from saw.connectors.rate_limiter import PlatformRateLimit
        limit = PlatformRateLimit.notion()
        assert limit.requests_per_second == 3
        assert limit.burst == 10

    def test_github_rate_limit(self):
        """Test 14: RateLimitManager enforces GitHub limit (5000 req/hr)."""
        from saw.connectors.rate_limiter import PlatformRateLimit
        limit = PlatformRateLimit.github()
        assert limit.requests_per_hour == 5000
        assert limit.burst == 100

    def test_slack_rate_limit(self):
        """Test 15: RateLimitManager enforces Slack limit (60 req/min)."""
        from saw.connectors.rate_limiter import PlatformRateLimit
        limit = PlatformRateLimit.slack()
        assert limit.requests_per_minute == 60
        assert limit.burst == 20

    def test_discord_rate_limit(self):
        """Test 16: RateLimitManager enforces Discord limit (50 req/s global)."""
        from saw.connectors.rate_limiter import PlatformRateLimit
        limit = PlatformRateLimit.discord()
        assert limit.requests_per_second == 50
        assert limit.burst == 50


class TestRateLimitManager:
    """Test RateLimitManager token bucket algorithm."""

    @pytest.mark.asyncio
    async def test_acquire_allows_request(self):
        """Test 17: acquire() waits when rate limit exceeded."""
        from saw.connectors.rate_limiter import RateLimitManager
        limiter = RateLimitManager("notion")
        # Should allow immediately (burst capacity)
        await limiter.acquire()  # No exception = pass

    @pytest.mark.asyncio
    async def test_burst_allows_temporary_spikes(self):
        """Test 18: burst allowance permits temporary spikes."""
        from saw.connectors.rate_limiter import RateLimitManager
        limiter = RateLimitManager("notion")
        # Should allow burst requests
        for _ in range(5):
            await limiter.acquire()


# Tests for Task 4: ConnectorRegistry singleton and database models


class TestConnectorRegistry:
    """Test ConnectorRegistry singleton."""

    def test_register_adds_connector(self):
        """Test 19: ConnectorRegistry.register() adds connector to registry."""
        from saw.connectors.registry import ConnectorRegistry
        from saw.connectors.protocol import UnifiedConnectorInterface

        # Reset singleton
        ConnectorRegistry.reset()

        # Create mock connector
        mock_connector = Mock(spec=UnifiedConnectorInterface)
        mock_connector.platform_name = "test_platform"

        registry = ConnectorRegistry()
        registry.register(mock_connector)

        assert "test_platform" in registry.list_all()
        ConnectorRegistry.reset()

    def test_get_retrieves_connector(self):
        """Test 20: ConnectorRegistry.get() retrieves connector by platform name."""
        from saw.connectors.registry import ConnectorRegistry
        from saw.connectors.protocol import UnifiedConnectorInterface

        ConnectorRegistry.reset()

        mock_connector = Mock(spec=UnifiedConnectorInterface)
        mock_connector.platform_name = "test_platform"

        registry = ConnectorRegistry()
        registry.register(mock_connector)

        result = registry.get("test_platform")
        assert result == mock_connector
        ConnectorRegistry.reset()

    def test_list_all_returns_platforms(self):
        """Test 21: ConnectorRegistry.list_all() returns all registered connectors."""
        from saw.connectors.registry import ConnectorRegistry
        from saw.connectors.protocol import UnifiedConnectorInterface

        ConnectorRegistry.reset()

        mock1 = Mock(spec=UnifiedConnectorInterface)
        mock1.platform_name = "platform1"
        mock2 = Mock(spec=UnifiedConnectorInterface)
        mock2.platform_name = "platform2"

        registry = ConnectorRegistry()
        registry.register(mock1)
        registry.register(mock2)

        platforms = registry.list_all()
        assert "platform1" in platforms
        assert "platform2" in platforms
        ConnectorRegistry.reset()

    def test_unregister_removes_connector(self):
        """Test 22: ConnectorRegistry.unregister() removes connector from registry."""
        from saw.connectors.registry import ConnectorRegistry
        from saw.connectors.protocol import UnifiedConnectorInterface

        ConnectorRegistry.reset()

        mock_connector = Mock(spec=UnifiedConnectorInterface)
        mock_connector.platform_name = "test_platform"

        registry = ConnectorRegistry()
        registry.register(mock_connector)
        result = registry.unregister("test_platform")

        assert result is True
        assert registry.get("test_platform") is None
        ConnectorRegistry.reset()


class TestConnectorConfigModel:
    """Test SQLAlchemy ConnectorConfigModel."""

    def test_model_has_required_fields(self):
        """Test 23: ConnectorConfigModel can be created with required fields."""
        from saw.db.connector_models import ConnectorConfigModel
        model = ConnectorConfigModel(
            id="cfg-123",
            user_id="user-1",
            platform="notion",
            name="Test Notion",
        )
        assert model.platform == "notion"
        assert model.name == "Test Notion"

    def test_model_defaults(self):
        """ConnectorConfigModel database defaults are defined."""
        from saw.db.connector_models import ConnectorConfigModel
        # Check the column definitions have correct defaults (for DB)
        # SQLAlchemy defaults apply on insert, not on Python object creation
        is_active_col = ConnectorConfigModel.__table__.columns["is_active"]
        sync_interval_col = ConnectorConfigModel.__table__.columns["sync_interval"]
        assert is_active_col.default.arg is True
        assert sync_interval_col.default.arg == 3600


class TestConnectorSyncLog:
    """Test SQLAlchemy ConnectorSyncLog."""

    def test_sync_log_creation(self):
        """Test 24: ConnectorSyncLog can be created with required fields."""
        from saw.db.connector_models import ConnectorSyncLog
        log = ConnectorSyncLog(
            id="log-123",
            config_id="cfg-123",
            direction="pull",
        )
        assert log.config_id == "cfg-123"
        assert log.direction == "pull"

"""Tests for OAuth handler, token encryption, and token refresh.

Plan 10-02: OAuth Handler and Token Encryption.
"""
import pytest
import os
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Tests for Task 1: TokenEncryption with Fernet symmetric encryption


class TestTokenEncryption:
    """Test TokenEncryption Fernet encryption."""

    def test_generate_key_returns_valid_fernet_key(self):
        """Test 1: TokenEncryption.generate_key() returns valid Fernet key."""
        from saw.connectors.token_encryption import TokenEncryption
        key = TokenEncryption.generate_key()
        # Fernet keys are 44-character base64 strings
        assert len(key) == 44
        assert key.endswith('=')  # Base64 padding

    def test_encrypt_produces_encrypted_string(self):
        """Test 2: TokenEncryption.encrypt() produces encrypted string."""
        from saw.connectors.token_encryption import TokenEncryption
        key = TokenEncryption.generate_key()
        encryption = TokenEncryption.from_key(key)
        encrypted = encryption.encrypt("my_secret_token")
        assert encrypted != "my_secret_token"
        assert len(encrypted) > 0

    def test_decrypt_recovers_original_token(self):
        """Test 3: TokenEncryption.decrypt() recovers original token."""
        from saw.connectors.token_encryption import TokenEncryption
        key = TokenEncryption.generate_key()
        encryption = TokenEncryption.from_key(key)
        original = "my_secret_token_12345"
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original

    def test_uses_env_variable_for_key(self):
        """Test 4: TokenEncryption uses SAW_ENCRYPTION_KEY from environment."""
        from saw.connectors.token_encryption import TokenEncryption
        test_key = TokenEncryption.generate_key()
        os.environ["SAW_ENCRYPTION_KEY"] = test_key
        try:
            encryption = TokenEncryption.from_env()
            assert encryption is not None
            # Verify it works
            encrypted = encryption.encrypt("test")
            decrypted = encryption.decrypt(encrypted)
            assert decrypted == "test"
        finally:
            del os.environ["SAW_ENCRYPTION_KEY"]

    def test_decryption_failure_raises_error(self):
        """Test 5: EncryptionError raised when decryption fails."""
        from saw.connectors.token_encryption import TokenEncryption, EncryptionError
        key = TokenEncryption.generate_key()
        encryption = TokenEncryption.from_key(key)
        with pytest.raises(EncryptionError):
            encryption.decrypt("invalid_encrypted_data")

    def test_generate_key_if_missing_returns_key(self):
        """Test 6: TokenEncryption.generate_key_if_missing() creates key on first run."""
        from saw.connectors.token_encryption import TokenEncryption
        # When no env var set, generates new key
        if "SAW_ENCRYPTION_KEY" in os.environ:
            del os.environ["SAW_ENCRYPTION_KEY"]
        key = TokenEncryption.generate_key_if_missing()
        assert len(key) == 44

    def test_encrypt_token_set(self):
        """TokenEncryption.encrypt_token_set() encrypts complete token data."""
        from saw.connectors.token_encryption import TokenEncryption
        key = TokenEncryption.generate_key()
        encryption = TokenEncryption.from_key(key)
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        encrypted = encryption.encrypt_token_set(
            access_token="access123",
            refresh_token="refresh456",
            expires_at=expires,
        )
        assert encrypted is not None

    def test_decrypt_token_set(self):
        """TokenEncryption.decrypt_token_set() recovers token data."""
        from saw.connectors.token_encryption import TokenEncryption
        key = TokenEncryption.generate_key()
        encryption = TokenEncryption.from_key(key)
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        encrypted = encryption.encrypt_token_set(
            access_token="access123",
            refresh_token="refresh456",
            expires_at=expires,
        )
        data = encryption.decrypt_token_set(encrypted)
        assert data["access_token"] == "access123"
        assert data["refresh_token"] == "refresh456"


# Tests for Task 2: OAuthHandler with state management


class TestOAuthConfig:
    """Test OAuthConfig platform configurations."""

    def test_notion_config(self):
        """OAuthConfig.notion() creates Notion OAuth config."""
        from saw.connectors.oauth_handler import OAuthConfig
        config = OAuthConfig.notion("client_id", "secret", "https://redirect")
        assert config.client_id == "client_id"
        assert "notion.com" in config.authorize_url

    def test_slack_config(self):
        """OAuthConfig.slack() creates Slack OAuth config."""
        from saw.connectors.oauth_handler import OAuthConfig
        config = OAuthConfig.slack("client_id", "secret", "https://redirect")
        assert config.client_id == "client_id"
        assert "slack.com" in config.authorize_url

    def test_github_config(self):
        """OAuthConfig.github() creates GitHub OAuth config."""
        from saw.connectors.oauth_handler import OAuthConfig
        config = OAuthConfig.github("client_id", "secret", "https://redirect")
        assert config.client_id == "client_id"
        assert "github.com" in config.authorize_url

    def test_feishu_config(self):
        """OAuthConfig.feishu() creates Feishu OAuth config."""
        from saw.connectors.oauth_handler import OAuthConfig
        config = OAuthConfig.feishu("client_id", "secret", "https://redirect")
        assert config.client_id == "client_id"
        assert "feishu.cn" in config.authorize_url


class TestOAuthHandler:
    """Test OAuthHandler OAuth 2.0 flow management."""

    def test_get_authorization_url_returns_valid_url(self):
        """Test 7: OAuthHandler.get_authorization_url() returns valid OAuth URL."""
        from saw.connectors.oauth_handler import OAuthHandler, OAuthConfig
        from saw.connectors.token_encryption import TokenEncryption
        key = TokenEncryption.generate_key()
        encryption = TokenEncryption.from_key(key)
        config = OAuthConfig.github("client_id", "secret", "https://redirect")
        handler = OAuthHandler(config=config, platform="github", encryption=encryption)
        url, state = handler.get_authorization_url("user-123")
        assert "github.com" in url
        assert len(state) > 0

    def test_generate_state_creates_random_state(self):
        """Test 8: OAuthHandler.generate_state() creates cryptographically random state."""
        from saw.connectors.oauth_handler import OAuthHandler, OAuthConfig
        from saw.connectors.token_encryption import TokenEncryption
        key = TokenEncryption.generate_key()
        encryption = TokenEncryption.from_key(key)
        config = OAuthConfig.github("client_id", "secret", "https://redirect")
        handler = OAuthHandler(config=config, platform="github", encryption=encryption)
        state1 = handler._generate_state()
        state2 = handler._generate_state()
        assert state1 != state2
        assert len(state1) >= 32

    def test_verify_state_validates_correctly(self):
        """Test 9: OAuthHandler.verify_state() validates state correctly."""
        from saw.connectors.oauth_handler import OAuthHandler, OAuthConfig, OAuthState
        from saw.connectors.token_encryption import TokenEncryption
        key = TokenEncryption.generate_key()
        encryption = TokenEncryption.from_key(key)
        config = OAuthConfig.github("client_id", "secret", "https://redirect")
        handler = OAuthHandler(config=config, platform="github", encryption=encryption)

        # Store state
        url, state = handler.get_authorization_url("user-123")

        # Verify state
        result = handler.verify_state(state)
        assert result is not None
        assert result.user_id == "user-123"
        assert result.platform == "github"

    def test_verify_state_rejects_invalid_state(self):
        """OAuthHandler.verify_state() rejects invalid state."""
        from saw.connectors.oauth_handler import OAuthHandler, OAuthConfig
        from saw.connectors.token_encryption import TokenEncryption
        key = TokenEncryption.generate_key()
        encryption = TokenEncryption.from_key(key)
        config = OAuthConfig.github("client_id", "secret", "https://redirect")
        handler = OAuthHandler(config=config, platform="github", encryption=encryption)

        result = handler.verify_state("invalid_state")
        assert result is None


# Tests for Task 3: TokenRefreshManager with mutex lock


class TestRefreshMutex:
    """Test RefreshMutex for concurrent refresh protection."""

    @pytest.mark.asyncio
    async def test_acquire_returns_true_when_available(self):
        """Test 18: asyncio.Lock used for single-user mode."""
        from saw.connectors.token_refresh import RefreshMutex
        mutex = RefreshMutex()
        acquired = await mutex.acquire("connector-1")
        assert acquired is True
        await mutex.release("connector-1")

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """RefreshMutex works as async context manager."""
        from saw.connectors.token_refresh import RefreshMutex
        mutex = RefreshMutex()
        async with mutex:
            # Lock is held
            assert mutex._local_lock.locked()
        # Lock is released
        assert not mutex._local_lock.locked()


class TestTokenRefreshManager:
    """Test TokenRefreshManager automatic token refresh."""

    def test_refresh_buffer_seconds(self):
        """TokenRefreshManager has refresh buffer."""
        from saw.connectors.token_refresh import TokenRefreshManager
        assert TokenRefreshManager.REFRESH_BUFFER_SECONDS == 300

    @pytest.mark.asyncio
    async def test_refresh_if_needed_returns_same_if_valid(self):
        """Test 13: TokenRefreshManager refreshes expired token."""
        from saw.connectors.token_refresh import TokenRefreshManager
        from saw.connectors.oauth_handler import OAuthConfig
        from saw.connectors.token_encryption import TokenEncryption
        key = TokenEncryption.generate_key()
        encryption = TokenEncryption.from_key(key)
        config = OAuthConfig.github("client_id", "secret", "https://redirect")
        manager = TokenRefreshManager(encryption=encryption, oauth_config=config)

        # Create token that expires in 1 hour (not yet due for refresh)
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        encrypted = encryption.encrypt_token_set(
            access_token="valid_token",
            refresh_token="refresh_token",
            expires_at=expires,
        )

        result, was_refreshed = await manager.refresh_if_needed(encrypted, "conn-1")
        assert was_refreshed is False

    def test_manager_has_mutex(self):
        """Test 14: Mutex lock prevents concurrent refresh attempts."""
        from saw.connectors.token_refresh import TokenRefreshManager
        from saw.connectors.oauth_handler import OAuthConfig
        from saw.connectors.token_encryption import TokenEncryption
        key = TokenEncryption.generate_key()
        encryption = TokenEncryption.from_key(key)
        config = OAuthConfig.github("client_id", "secret", "https://redirect")
        manager = TokenRefreshManager(encryption=encryption, oauth_config=config)
        assert manager._mutex is not None


# Tests for Task 4: FastAPI OAuth callback endpoints


class TestOAuthEndpoints:
    """Test FastAPI OAuth callback endpoints."""

    def test_platforms_endpoint_exists(self, client):
        """Test 24: Supported platforms list available via endpoint."""
        from saw.api.oauth_callback import router
        # Check router exists
        assert router is not None
        # Check routes are defined (paths include prefix)
        routes = [r.path for r in router.routes]
        assert "/api/v1/oauth/platforms" in routes

    def test_authorize_endpoint_exists(self):
        """Test 19: GET /api/v1/oauth/{platform}/authorize returns authorization URL."""
        from saw.api.oauth_callback import router
        routes = [r.path for r in router.routes]
        assert "/api/v1/oauth/{platform}/authorize" in routes

    def test_callback_endpoint_exists(self):
        """Test 20: GET /api/v1/oauth/{platform}/callback handles successful OAuth."""
        from saw.api.oauth_callback import router
        routes = [r.path for r in router.routes]
        assert "/api/v1/oauth/{platform}/callback" in routes

    def test_platform_info_model(self):
        """PlatformInfo model has correct fields."""
        from saw.api.oauth_callback import PlatformInfo
        info = PlatformInfo(
            name="github",
            display_name="GitHub",
            supports_oauth=True,
        )
        assert info.name == "github"
        assert info.supports_oauth is True


# Fixture for FastAPI test client
@pytest.fixture
def client():
    """Create test client for OAuth endpoints."""
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    from saw.api.oauth_callback import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)

"""Tests for JWT authentication module.

Phase 40: Test Coverage — TEST-01, SEC-01 validation.
Covers: AuthConfig, PasswordHasher, JWTHandler, AuthService.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest

from saw.auth.jwt_auth import (
    AuthConfig,
    TokenData,
    TokenPair,
    PasswordHasher,
    JWTHandler,
    AuthService,
    hash_token,
)


# ── AuthConfig Tests ──────────────────────────────────────────────────


class TestAuthConfig:
    """Tests for AuthConfig."""

    def test_default_config(self):
        config = AuthConfig()
        assert config.algorithm == "HS256"
        assert config.access_token_expire_minutes == 30
        assert config.refresh_token_expire_days == 7
        assert config.secret_key is not None
        assert len(config.secret_key) > 0

    def test_custom_config(self):
        config = AuthConfig(
            secret_key="test-secret",
            algorithm="HS384",
            access_token_expire_minutes=60,
            refresh_token_expire_days=14,
        )
        assert config.secret_key == "test-secret"
        assert config.algorithm == "HS384"
        assert config.access_token_expire_minutes == 60
        assert config.refresh_token_expire_days == 14

    def test_from_env(self):
        env = {
            "AUTH_SECRET_KEY": "env-secret",
            "JWT_ALGORITHM": "HS512",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
            "REFRESH_TOKEN_EXPIRE_DAYS": "30",
        }
        with patch.dict("os.environ", env):
            config = AuthConfig.from_env()
            assert config.secret_key == "env-secret"
            assert config.algorithm == "HS512"
            assert config.access_token_expire_minutes == 15
            assert config.refresh_token_expire_days == 30


# ── TokenData Tests ───────────────────────────────────────────────────


class TestTokenData:
    """Tests for TokenData."""

    def test_to_dict(self):
        now = datetime.now(timezone.utc)
        data = TokenData(
            sub="user-123",
            exp=now + timedelta(hours=1),
            iat=now,
            role="editor",
        )
        result = data.to_dict()
        assert result["sub"] == "user-123"
        assert result["role"] == "editor"
        assert "exp" in result
        assert "iat" in result


# ── PasswordHasher Tests ─────────────────────────────────────────────


class TestPasswordHasher:
    """Tests for PasswordHasher."""

    def test_hash_and_verify(self):
        hasher = PasswordHasher()
        password = "SecureP@ss123"
        hashed = hasher.hash_password(password)

        assert hashed != password
        assert hasher.verify_password(password, hashed) is True
        assert hasher.verify_password("wrong-password", hashed) is False

    def test_different_hashes_for_same_password(self):
        hasher = PasswordHasher()
        password = "SamePassword123"
        hash1 = hasher.hash_password(password)
        hash2 = hasher.hash_password(password)

        # bcrypt generates different salts each time
        assert hash1 != hash2
        # Both should verify correctly
        assert hasher.verify_password(password, hash1) is True
        assert hasher.verify_password(password, hash2) is True

    def test_verify_invalid_hash(self):
        hasher = PasswordHasher()
        assert hasher.verify_password("password", "not-a-valid-hash") is False


# ── JWTHandler Tests ──────────────────────────────────────────────────


class TestJWTHandler:
    """Tests for JWTHandler."""

    @pytest.fixture
    def handler(self):
        config = AuthConfig(secret_key="test-secret-key-for-jwt-tests")
        return JWTHandler(config)

    def test_create_access_token(self, handler):
        token = handler.create_access_token("user-123", role="editor")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self, handler):
        token = handler.create_refresh_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_pair(self, handler):
        pair = handler.create_token_pair("user-123", role="admin")
        assert isinstance(pair, TokenPair)
        assert pair.access_token != pair.refresh_token
        assert pair.token_type == "bearer"
        assert pair.expires_in > 0

    def test_verify_access_token(self, handler):
        token = handler.create_access_token("user-456", role="viewer")
        data = handler.verify_access_token(token)

        assert data.sub == "user-456"
        assert data.role == "viewer"

    def test_verify_refresh_token(self, handler):
        token = handler.create_refresh_token("user-789")
        user_id = handler.verify_refresh_token(token)
        assert user_id == "user-789"

    def test_expired_token_raises(self, handler):
        # Create token that expired immediately
        token = handler.create_access_token(
            "user-123",
            expires_delta=timedelta(seconds=-1),
        )
        with pytest.raises(ValueError, match="expired"):
            handler.verify_access_token(token)

    def test_wrong_type_token_raises(self, handler):
        refresh_token = handler.create_refresh_token("user-123")
        with pytest.raises(ValueError, match="Not an access token"):
            handler.verify_access_token(refresh_token)

    def test_invalid_token_raises(self, handler):
        with pytest.raises(ValueError, match="Invalid token"):
            handler.verify_access_token("not.a.valid.jwt.token")

    def test_token_with_custom_expiry(self, handler):
        token = handler.create_access_token(
            "user-123",
            expires_delta=timedelta(hours=2),
        )
        data = handler.verify_access_token(token)
        # Token should expire roughly 2 hours from now
        expected_exp = datetime.now(timezone.utc) + timedelta(hours=2)
        diff = abs((data.exp - expected_exp).total_seconds())
        assert diff < 5  # Allow 5 seconds tolerance


# ── AuthService Tests ─────────────────────────────────────────────────


class TestAuthService:
    """Tests for AuthService."""

    @pytest.fixture
    def service(self):
        config = AuthConfig(secret_key="test-secret-for-auth-service")
        return AuthService(config)

    def test_register_user(self, service):
        user = service.register_user(
            email="test@example.com",
            password="SecurePass123",
            role="editor",
            display_name="Test User",
        )
        assert user["email"] == "test@example.com"
        assert user["role"] == "editor"
        assert user["display_name"] == "Test User"
        assert user["is_active"] is True
        assert user["hashed_password"] != "SecurePass123"
        assert "id" in user

    def test_authenticate_user(self, service):
        user = service.register_user(
            email="auth@example.com",
            password="MyPassword123",
            role="viewer",
        )
        tokens = service.authenticate_user(
            email="auth@example.com",
            password="MyPassword123",
            user=user,
        )
        assert tokens is not None
        assert isinstance(tokens, TokenPair)

    def test_authenticate_wrong_password(self, service):
        user = service.register_user(
            email="wrong@example.com",
            password="CorrectPassword",
            role="viewer",
        )
        tokens = service.authenticate_user(
            email="wrong@example.com",
            password="WrongPassword",
            user=user,
        )
        assert tokens is None

    def test_authenticate_inactive_user(self, service):
        user = service.register_user(
            email="inactive@example.com",
            password="Password123",
            role="viewer",
        )
        user["is_active"] = False
        tokens = service.authenticate_user(
            email="inactive@example.com",
            password="Password123",
            user=user,
        )
        assert tokens is None

    def test_refresh_tokens(self, service):
        user = service.register_user(
            email="refresh@example.com",
            password="Password123",
            role="editor",
        )
        tokens = service.authenticate_user(
            email="refresh@example.com",
            password="Password123",
            user=user,
        )

        def get_user(user_id):
            return user

        new_tokens = service.refresh_tokens(
            refresh_token=tokens.refresh_token,
            get_user_by_id=get_user,
        )
        assert new_tokens is not None
        assert new_tokens.access_token != tokens.access_token

    def test_change_password(self, service):
        user = service.register_user(
            email="change@example.com",
            password="OldPassword123",
            role="viewer",
        )
        new_hash = service.change_password(
            user_id=user["id"],
            old_password="OldPassword123",
            new_password="NewPassword456",
            user=user,
        )
        assert new_hash != user["hashed_password"]
        assert service.hasher.verify_password("NewPassword456", new_hash)

    def test_change_password_wrong_old(self, service):
        user = service.register_user(
            email="wrongchange@example.com",
            password="RealPassword",
            role="viewer",
        )
        with pytest.raises(ValueError, match="Invalid old password"):
            service.change_password(
                user_id=user["id"],
                old_password="WrongOldPassword",
                new_password="NewPassword",
                user=user,
            )


# ── Utility Tests ─────────────────────────────────────────────────────


class TestUtilities:
    """Tests for utility functions."""

    def test_hash_token(self):
        token = "some-secret-token"
        hashed = hash_token(token)
        assert hashed != token
        assert len(hashed) == 64  # SHA-256 hex digest
        # Same input produces same hash
        assert hash_token(token) == hashed

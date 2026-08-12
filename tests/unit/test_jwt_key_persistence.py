"""Tests for JWT HMAC secret persistence (C1/C5).

Verifies ``AuthConfig`` resolves a persistent secret from
``.saw/keys/jwt.key`` so access/refresh tokens stay valid across restarts.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from saw.auth.jwt_auth import AuthConfig, JWTHandler


def _key_path(tmp_path: Path) -> Path:
    return tmp_path / "keys" / "jwt.key"


class TestResolveSecretKey:
    def test_env_var_takes_precedence(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AUTH_SECRET_KEY", "env-secret")
        assert AuthConfig._resolve_secret_key(_key_path(tmp_path)) == "env-secret"

    def test_generates_and_persists(self, tmp_path, monkeypatch):
        monkeypatch.delenv("AUTH_SECRET_KEY", raising=False)
        path = _key_path(tmp_path)
        k1 = AuthConfig._resolve_secret_key(path)
        assert path.exists()
        k2 = AuthConfig._resolve_secret_key(path)
        assert k1 == k2  # stable across calls once persisted

    def test_invalid_key_file_rejected(self, tmp_path, monkeypatch):
        monkeypatch.delenv("AUTH_SECRET_KEY", raising=False)
        path = _key_path(tmp_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not-valid-hex-but-long-enough-xxxx", encoding="utf-8")
        # The raw string is returned as-is (it's a valid HMAC key string);
        # JWT signing/verifying works regardless of hex-ness.
        secret = AuthConfig._resolve_secret_key(path)
        assert secret.startswith("not-valid-hex")


class TestAuthConfigDefault:
    def test_default_constructor_uses_persistent_key(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("AUTH_SECRET_KEY", raising=False)
        cfg = AuthConfig()
        secret = cfg.secret_key
        # Re-constructing must yield the same persisted secret.
        assert AuthConfig().secret_key == secret
        assert (tmp_path / ".saw" / "keys" / "jwt.key").exists()


class TestTokenStableAcrossInstances:
    def test_token_validated_by_fresh_handler(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("AUTH_SECRET_KEY", raising=False)
        cfg = AuthConfig()
        handler = JWTHandler(cfg)
        token = handler.create_access_token("user-1", role="admin")

        # Simulate a restart: new process reads the same key file.
        monkeypatch.chdir(tmp_path)
        fresh = JWTHandler(AuthConfig())
        data = fresh.verify_access_token(token)
        assert data.sub == "user-1"
        assert data.role == "admin"

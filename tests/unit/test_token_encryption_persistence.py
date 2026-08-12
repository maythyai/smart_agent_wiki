"""Tests for Fernet key persistence (C5).

Verifies that ``TokenEncryption`` resolves a persistent key from disk
(generating + writing it on first use) so encrypted tokens remain
decryptable across process restarts.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from saw.connectors.token_encryption import EncryptionError, TokenEncryption


def _key_path(tmp_path: Path) -> Path:
    return tmp_path / "keys" / "fernet.key"


class TestFromKeyFile:
    def test_generates_and_persists_when_missing(self, tmp_path):
        path = _key_path(tmp_path)
        enc = TokenEncryption.from_key_file(path)
        assert path.exists()
        # The persisted key can decrypt what this instance encrypted.
        cipher = enc.encrypt("secret-token")
        assert enc.decrypt(cipher) == "secret-token"

    def test_reuses_existing_key(self, tmp_path):
        path = _key_path(tmp_path)
        first = TokenEncryption.from_key_file(path)
        cipher = first.encrypt("persistent-token")
        # A second instance from the same file must read the same key.
        second = TokenEncryption.from_key_file(path)
        assert second.decrypt(cipher) == "persistent-token"

    def test_key_file_permissions(self, tmp_path):
        path = _key_path(tmp_path)
        TokenEncryption.from_key_file(path)
        if __import__("os").name != "nt":
            import stat

            mode = stat.S_IMODE(path.stat().st_mode)
            assert mode == 0o600


class TestFromEnvFallback:
    def test_env_var_takes_precedence(self, tmp_path, monkeypatch):
        from cryptography.fernet import Fernet

        env_key = Fernet.generate_key().decode()
        monkeypatch.setenv("SAW_ENCRYPTION_KEY", env_key)
        path = _key_path(tmp_path)
        enc = TokenEncryption.from_env(key_path=path)
        # Env var wins; no file should be written.
        assert not path.exists()
        assert enc.decrypt(enc.encrypt("x")) == "x"

    def test_falls_back_to_key_file_and_persists(self, tmp_path, monkeypatch):
        monkeypatch.delenv("SAW_ENCRYPTION_KEY", raising=False)
        path = _key_path(tmp_path)
        enc = TokenEncryption.from_env(key_path=path)
        assert path.exists()
        cipher = enc.encrypt("restart-safe")
        # New instance, same file → can still decrypt.
        again = TokenEncryption.from_env(key_path=path)
        assert again.decrypt(cipher) == "restart-safe"


class TestGenerateKeyIfMissing:
    def test_persists_generated_key(self, tmp_path, monkeypatch):
        monkeypatch.delenv("SAW_ENCRYPTION_KEY", raising=False)
        path = _key_path(tmp_path)
        k1 = TokenEncryption.generate_key_if_missing(key_path=path)
        assert path.exists()
        k2 = TokenEncryption.generate_key_if_missing(key_path=path)
        assert k1 == k2  # deterministic across calls once persisted

    def test_env_preferred(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SAW_ENCRYPTION_KEY", "envvalue")
        assert TokenEncryption.generate_key_if_missing(key_path=_key_path(tmp_path)) == "envvalue"


class TestRoundTrip:
    def test_encrypt_decrypt_token_set(self, tmp_path):
        from datetime import datetime, timezone

        enc = TokenEncryption.from_key_file(_key_path(tmp_path))
        cipher = enc.encrypt_token_set(
            access_token="acc",
            refresh_token="ref",
            expires_at=datetime.now(timezone.utc),
        )
        decoded = enc.decrypt_token_set(cipher)
        assert decoded["access_token"] == "acc"
        assert decoded["refresh_token"] == "ref"

    def test_empty_input_rejected(self, tmp_path):
        enc = TokenEncryption.from_key_file(_key_path(tmp_path))
        with pytest.raises(EncryptionError):
            enc.encrypt("")

"""Fernet-based token encryption for OAuth credentials.

Plan 10-02: OAuth Handler and Token Encryption.
Per AUTH-02: OAuth tokens encrypted at rest using Fernet encryption.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from saw.adapters.crypto._keyfiles import load_or_create, read_key_file, write_key_file


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass


class TokenEncryption:
    """Fernet-based token encryption for OAuth credentials.

    Per AUTH-02: OAuth tokens encrypted at rest using Fernet encryption.
    """

    def __init__(self, fernet: Fernet):
        """Initialize with Fernet instance.

        Args:
            fernet: Fernet instance for encryption/decryption.
        """
        self._fernet = fernet

    @classmethod
    def from_env(cls, key_path: Path | None = None) -> "TokenEncryption":
        """Create instance, resolving the Fernet key with persistence.

        Resolution order (first wins):

        1. ``SAW_ENCRYPTION_KEY`` environment variable (team/CI deployments).
        2. The key file at ``key_path`` (default ``.saw/keys/fernet.key``);
           if it does not exist it is generated and persisted with ``0600``
           permissions so that previously-encrypted tokens remain readable
           across restarts.

        Returns:
            TokenEncryption instance.

        Raises:
            EncryptionError: If the resolved key is not a valid Fernet key.
        """
        key = os.environ.get("SAW_ENCRYPTION_KEY")
        if not key:
            path = key_path or Path(".saw/keys/fernet.key")
            key = load_or_create(path, cls.generate_key)
        try:
            return cls(Fernet(key.encode()))
        except Exception as e:
            raise EncryptionError(f"Invalid Fernet key: {e}") from e

    @classmethod
    def from_key(cls, key: str) -> "TokenEncryption":
        """Create instance with provided key.

        Args:
            key: Base64-encoded Fernet key string.

        Returns:
            TokenEncryption instance.
        """
        return cls(Fernet(key.encode()))

    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet key.

        Returns:
            Base64-encoded Fernet key string.
        """
        return Fernet.generate_key().decode()

    @classmethod
    def from_key_file(cls, path: Path) -> "TokenEncryption":
        """Load the Fernet key from ``path``, persisting a new one if missing.

        Equivalent to ``from_env(key_path=path)`` but ignores the env var.
        Useful for tests and explicit key-file wiring.
        """
        key = load_or_create(path, cls.generate_key)
        try:
            return cls(Fernet(key.encode()))
        except Exception as e:
            raise EncryptionError(f"Invalid Fernet key: {e}") from e

    @staticmethod
    def generate_key_if_missing(key_path: Path | None = None) -> str:
        """Return an existing key, persisting a new one only if missing.

        Resolution order: ``SAW_ENCRYPTION_KEY`` env var → key file
        (``key_path`` or ``.saw/keys/fernet.key``) → generate + persist.

        Unlike the previous implementation, a freshly generated key is
        always persisted so it survives restarts.
        """
        env_key = os.environ.get("SAW_ENCRYPTION_KEY")
        if env_key:
            return env_key
        path = key_path or Path(".saw/keys/fernet.key")
        return load_or_create(path, lambda: Fernet.generate_key().decode())

    def encrypt(self, token: str) -> str:
        """Encrypt a token string.

        Args:
            token: Plain text token to encrypt.

        Returns:
            Encrypted token string (base64).

        Raises:
            EncryptionError: If token is empty.
        """
        if not token:
            raise EncryptionError("Cannot encrypt empty token")
        encrypted = self._fernet.encrypt(token.encode())
        return encrypted.decode()

    def decrypt(self, encrypted_token: str) -> str:
        """Decrypt an encrypted token.

        Args:
            encrypted_token: Encrypted token string.

        Returns:
            Decrypted plain text token.

        Raises:
            EncryptionError: If decryption fails.
        """
        if not encrypted_token:
            raise EncryptionError("Cannot decrypt empty token")
        try:
            decrypted = self._fernet.decrypt(encrypted_token.encode())
            return decrypted.decode()
        except InvalidToken as e:
            raise EncryptionError(f"Decryption failed: {e}") from e

    def encrypt_token_set(
        self,
        access_token: str,
        refresh_token: str | None = None,
        expires_at: datetime | None = None,
    ) -> str:
        """Encrypt a complete token set as JSON.

        Args:
            access_token: OAuth access token.
            refresh_token: OAuth refresh token (optional).
            expires_at: Token expiration timestamp (optional).

        Returns:
            Encrypted JSON string.
        """
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }
        return self.encrypt(json.dumps(token_data))

    def decrypt_token_set(self, encrypted: str) -> dict:
        """Decrypt a token set.

        Args:
            encrypted: Encrypted token set string.

        Returns:
            Dict with access_token, refresh_token, expires_at.
        """
        decrypted = self.decrypt(encrypted)
        data = json.loads(decrypted)
        if data.get("expires_at"):
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
        return data

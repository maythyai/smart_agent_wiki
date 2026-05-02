"""Fernet-based token encryption for OAuth credentials.

Plan 10-02: OAuth Handler and Token Encryption.
Per AUTH-02: OAuth tokens encrypted at rest using Fernet encryption.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


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
    def from_env(cls) -> "TokenEncryption":
        """Create instance using SAW_ENCRYPTION_KEY from environment.

        Per Decision 1: Use Fernet with env var SAW_ENCRYPTION_KEY.
        Generate on first run if not set.

        Returns:
            TokenEncryption instance.
        """
        key = os.environ.get("SAW_ENCRYPTION_KEY")
        if not key:
            key = cls.generate_key()
            # In production, log warning that key was generated
            # User should set SAW_ENCRYPTION_KEY for persistence
        return cls(Fernet(key.encode()))

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

    @staticmethod
    def generate_key_if_missing() -> str:
        """Get existing key from env or generate new one.

        Returns:
            The key to use (from env or newly generated).
        """
        key = os.environ.get("SAW_ENCRYPTION_KEY")
        if key:
            return key
        new_key = Fernet.generate_key().decode()
        # In production, persist this key somewhere safe
        return new_key

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

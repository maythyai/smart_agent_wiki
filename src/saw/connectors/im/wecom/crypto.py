"""WeCom message encryption/decryption.

Plan 13-04 Task 5: WeCom AES-256-CBC encryption.
Per WECO-03: Handle WeCom's message encryption (AES-256-CBC).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from typing import Optional

logger = logging.getLogger(__name__)


class WeComCrypto:
    """Handle WeCom message encryption/decryption.

    Per WECO-03: AES-256-CBC with PKCS7 padding.
    """

    def __init__(
        self,
        encoding_aes_key: str,
        token: str,
        corp_id: str,
    ) -> None:
        """Initialize crypto handler.

        Args:
            encoding_aes_key: WeCom encoding AES key (43 chars, base64).
            token: WeCom token for signature verification.
            corp_id: Enterprise corp ID.
        """
        # Key is 43 chars + '=' for base64 decode
        self._key = base64.b64decode(encoding_aes_key + "=")
        self._token = token
        self._corp_id = corp_id

    def decrypt(self, encrypted_msg: str) -> str:
        """Decrypt WeCom message using AES-256-CBC.

        Per WECO-03: AES-256-CBC decryption.

        Args:
            encrypted_msg: Base64-encoded encrypted message.

        Returns:
            Decrypted message content.
        """
        # Decode base64
        encrypted = base64.b64decode(encrypted_msg)

        # AES-256-CBC decrypt
        # Key is 32 bytes, IV is first 16 bytes of encrypted data
        iv = encrypted[:16]
        cipher = Cipher(
            algorithms.AES(self._key),
            modes.CBC(iv),
            backend=default_backend(),
        )
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted[16:]) + decryptor.finalize()

        # Remove PKCS7 padding
        pad_len = decrypted[-1]
        decrypted = decrypted[:-pad_len]

        # Parse: random(16) + msg_len(4) + msg + corp_id
        # First 16 bytes are random, next 4 are message length
        msg_len = int.from_bytes(decrypted[16:20], "big")
        msg = decrypted[20:20 + msg_len].decode("utf-8")

        return msg

    def verify_signature(
        self,
        signature: str,
        timestamp: str,
        nonce: str,
        encrypted: str,
    ) -> bool:
        """Verify message signature.

        WeCom uses SHA1(sort(token, timestamp, nonce, encrypted)) for signature.

        Args:
            signature: Received signature.
            timestamp: Request timestamp.
            nonce: Request nonce.
            encrypted: Encrypted message.

        Returns:
            True if signature is valid.
        """
        # SHA1(sort(token, timestamp, nonce, encrypted))
        sorted_str = "".join(sorted([self._token, timestamp, nonce, encrypted]))
        computed = hashlib.sha1(sorted_str.encode()).hexdigest()
        # M-24: constant-time comparison (was `==`, timing-attack vulnerable).
        if not hmac.compare_digest(computed, signature):
            return False
        # M-25: reject replayed webhooks (matching the Slack/Feishu 300s window).
        try:
            ts = int(timestamp)
            if abs(time.time() - ts) > 300:
                return False
        except (TypeError, ValueError):
            return False
        return True

    def encrypt(self, message: str) -> str:
        """Encrypt message for WeCom (for reply).

        Args:
            message: Message to encrypt.

        Returns:
            Base64-encoded encrypted message.
        """
        import os

        # Format: random(16) + msg_len(4) + msg + corp_id
        random_bytes = os.urandom(16)
        msg_bytes = message.encode("utf-8")
        msg_len = len(msg_bytes).to_bytes(4, "big")
        corp_bytes = self._corp_id.encode("utf-8")

        data = random_bytes + msg_len + msg_bytes + corp_bytes

        # Pad to 32-byte boundary (AES block size)
        pad_len = 32 - (len(data) % 32)
        data += bytes([pad_len] * pad_len)

        # AES-256-CBC encrypt
        iv = os.urandom(16)
        cipher = Cipher(
            algorithms.AES(self._key),
            modes.CBC(iv),
            backend=default_backend(),
        )
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(data) + encryptor.finalize()

        return base64.b64encode(iv + encrypted).decode("utf-8")
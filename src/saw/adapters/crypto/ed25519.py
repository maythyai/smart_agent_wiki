"""Ed25519 signing and verification for audit receipts.

Per PITFALLS.md:
- Key stored in OS keychain or separate encrypted file (not alongside wiki data)
- Private key file has 0600 permissions

Uses PyNaCl for Ed25519 implementation.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from nacl.signing import SigningKey, VerifyKey

logger = logging.getLogger(__name__)


@dataclass
class Receipt:
    """Signed receipt for an agent operation.

    Per D-08: Every operation produces a signed receipt.
    """
    operation_id: str
    operation_type: str  # "ingest", "query", "edit", "review", etc.
    agent: str  # which agent performed this (e.g., "Writer", "Scholar")
    timestamp: datetime
    claim_uuid: str | None = None
    page_path: str | None = None
    payload_hash: str | None = None
    signature: str | None = None
    prev_receipt_id: str | None = None

    def to_signable_data(self) -> bytes:
        """Get canonical data for signing.

        Returns:
            Canonical byte representation for signature.
        """
        data = {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "agent": self.agent,
            "timestamp": self.timestamp.isoformat(),
            "claim_uuid": self.claim_uuid,
            "page_path": self.page_path,
            "payload_hash": self.payload_hash,
            "prev_receipt_id": self.prev_receipt_id,
        }
        # Sort keys for canonical JSON
        return json.dumps(data, sort_keys=True).encode("utf-8")


class ReceiptSigner:
    """Ed25519 signing and verification for operation receipts.

    Per PITFALLS.md: Keys stored securely, not in wiki directory.
    """

    def __init__(self, key_path: Path | None = None) -> None:
        """Initialize signer.

        Args:
            key_path: Path to store/load private key.
                     Default: .saw/keys/ed25519.key (in wiki root)
        """
        self._key_path = key_path
        self._signing_key: SigningKey | None = None
        self._public_key: str | None = None

        # Try to load existing key
        if key_path and key_path.exists():
            self._load_keypair(key_path)

    def generate_keypair(self) -> tuple[str, str]:
        """Generate new Ed25519 key pair.

        Returns:
            Tuple of (private_key_b64, public_key_b64).
        """
        # Generate new signing key
        self._signing_key = SigningKey.generate()
        verify_key = self._signing_key.verify_key

        # Encode as base64
        private_key_b64 = base64.b64encode(
            bytes(self._signing_key)
        ).decode("ascii")
        public_key_b64 = base64.b64encode(
            bytes(verify_key)
        ).decode("ascii")

        self._public_key = public_key_b64

        # Store if path provided
        if self._key_path:
            self._store_keypair(private_key_b64)

        return private_key_b64, public_key_b64

    def _store_keypair(self, private_key_b64: str) -> None:
        """Store private key to file.

        Per PITFALLS.md: Key file has 0600 permissions.

        Args:
            private_key_b64: Base64-encoded private key.
        """
        if not self._key_path:
            return

        # Create directory with 0700 permissions
        self._key_path.parent.mkdir(parents=True, exist_ok=True)
        if os.name != "nt":  # Unix-like
            self._key_path.parent.chmod(0o700)

        # Write private key
        self._key_path.write_text(private_key_b64, encoding="ascii")

        # Set restrictive permissions (0600)
        if os.name != "nt":  # Unix-like
            self._key_path.chmod(0o600)

    def _load_keypair(self, key_path: Path) -> None:
        """Load existing keypair from file.

        Args:
            key_path: Path to private key file.

        DEF-2: a corrupt key file used to be silently swallowed (``except:
        pass``), leaving the signer with no key. That made
        ``AuditTrail.verify_chain`` skip signature checks entirely (every
        receipt "valid"). We still do not raise from ``__init__`` (to keep app
        startup stable), but we log the failure loudly; ``verify_chain`` now
        treats a missing public key as an unverifiable (invalid) chain.
        """
        try:
            private_key_b64 = key_path.read_text(encoding="ascii").strip()
            private_key_bytes = base64.b64decode(private_key_b64)
            self._signing_key = SigningKey(private_key_bytes)
            verify_key = self._signing_key.verify_key
            self._public_key = base64.b64encode(
                bytes(verify_key)
            ).decode("ascii")
        except Exception as e:  # noqa: BLE001
            logger.critical(
                "Failed to load Ed25519 key from %s: %s. Audit signature "
                "verification will treat the chain as INVALID until a valid "
                "key is (re)generated.", key_path, e,
            )

    def get_public_key(self) -> str | None:
        """Get public key for verification.

        Returns:
            Base64-encoded public key, or None if not initialized.
        """
        return self._public_key

    def sign_receipt(self, receipt: Receipt) -> str:
        """Sign a receipt with Ed25519.

        Args:
            receipt: The receipt to sign.

        Returns:
            Base64-encoded signature.
        """
        if not self._signing_key:
            raise ValueError("No signing key available. Call generate_keypair() first.")

        # Get canonical data to sign
        data = receipt.to_signable_data()

        # Sign with Ed25519
        signed = self._signing_key.sign(data)
        signature = signed.signature

        return base64.b64encode(signature).decode("ascii")

    def verify_receipt(
        self,
        receipt: Receipt,
        signature: str,
        public_key: str,
    ) -> bool:
        """Verify a receipt signature.

        Args:
            receipt: The receipt to verify.
            signature: Base64-encoded signature.
            public_key: Base64-encoded public key.

        Returns:
            True if signature is valid, False otherwise.
        """
        try:
            # Decode public key
            public_key_bytes = base64.b64decode(public_key)
            verify_key = VerifyKey(public_key_bytes)

            # Get canonical data
            data = receipt.to_signable_data()

            # Decode signature
            signature_bytes = base64.b64decode(signature)

            # Verify
            verify_key.verify(data, signature_bytes)
            return True
        except Exception:
            return False

    def sign_message(self, message: str) -> str:
        """Sign an arbitrary UTF-8 message with Ed25519.

        Args:
            message: The message to sign.

        Returns:
            Base64-encoded signature.

        Raises:
            ValueError: If no signing key is available.
        """
        if not self._signing_key:
            raise ValueError("No signing key available. Call generate_keypair() first.")
        signed = self._signing_key.sign(message.encode("utf-8"))
        return base64.b64encode(signed.signature).decode("ascii")

    def verify_message(
        self,
        message: str,
        signature: str,
        public_key: str,
    ) -> bool:
        """Verify an arbitrary-message signature.

        Args:
            message: The original message.
            signature: Base64-encoded signature produced by ``sign_message``.
            public_key: Base64-encoded public key.

        Returns:
            True if the signature is valid, False otherwise.
        """
        try:
            public_key_bytes = base64.b64decode(public_key)
            verify_key = VerifyKey(public_key_bytes)
            signature_bytes = base64.b64decode(signature)
            verify_key.verify(message.encode("utf-8"), signature_bytes)
            return True
        except Exception:
            return False

    def compute_payload_hash(self, payload: dict[str, Any]) -> str:
        """Compute SHA-256 hash of payload.

        Args:
            payload: Dictionary of operation details.

        Returns:
            Hex-encoded hash string.
        """
        data = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(data).hexdigest()

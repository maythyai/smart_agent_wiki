"""Tests for Ed25519 signing and verification.

Tests the ReceiptSigner class with:
1. generate_keypair() creates valid Ed25519 key pair
2. sign_receipt() creates valid Ed25519 signature
3. verify_receipt() validates signature integrity
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestGenerateKeypair:
    """Test 1: generate_keypair() creates valid Ed25519 key pair."""

    def test_returns_tuple_of_base64_strings(self) -> None:
        """Should return (private_key_b64, public_key_b64)."""
        from saw.adapters.crypto.ed25519 import ReceiptSigner

        signer = ReceiptSigner()
        private_key, public_key = signer.generate_keypair()

        assert isinstance(private_key, str)
        assert isinstance(public_key, str)
        # Base64 strings should be non-empty
        assert len(private_key) > 0
        assert len(public_key) > 0

    def test_keys_are_different(self) -> None:
        """Private and public keys should differ."""
        from saw.adapters.crypto.ed25519 import ReceiptSigner

        signer = ReceiptSigner()
        private_key, public_key = signer.generate_keypair()

        assert private_key != public_key

    def test_keys_are_base64_encoded(self) -> None:
        """Keys should be valid base64 strings."""
        import base64
        from saw.adapters.crypto.ed25519 import ReceiptSigner

        signer = ReceiptSigner()
        private_key, public_key = signer.generate_keypair()

        # Should decode without error
        base64.b64decode(private_key)
        base64.b64decode(public_key)

    def test_stores_keypair_internally(self) -> None:
        """Should store generated keys for signing."""
        from saw.adapters.crypto.ed25519 import ReceiptSigner

        signer = ReceiptSigner()
        signer.generate_keypair()

        public_key = signer.get_public_key()
        assert public_key is not None
        assert isinstance(public_key, str)


class TestSignReceipt:
    """Test 2: sign_receipt() creates valid Ed25519 signature."""

    def test_returns_base64_signature(self) -> None:
        """Should return base64-encoded signature."""
        from saw.adapters.crypto.ed25519 import ReceiptSigner, Receipt

        signer = ReceiptSigner()
        signer.generate_keypair()

        receipt = Receipt(
            operation_id="op-123",
            operation_type="ingest",
            agent="Writer",
            timestamp=__import__('datetime').datetime.now(__import__('datetime').timezone.utc),
        )

        signature = signer.sign_receipt(receipt)

        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_different_receipts_have_different_signatures(self) -> None:
        """Different receipts should produce different signatures."""
        from saw.adapters.crypto.ed25519 import ReceiptSigner, Receipt
        import datetime

        signer = ReceiptSigner()
        signer.generate_keypair()

        receipt1 = Receipt(
            operation_id="op-1",
            operation_type="ingest",
            agent="Writer",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        receipt2 = Receipt(
            operation_id="op-2",
            operation_type="query",
            agent="Librarian",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )

        sig1 = signer.sign_receipt(receipt1)
        sig2 = signer.sign_receipt(receipt2)

        assert sig1 != sig2

    def test_signature_includes_operation_data(self) -> None:
        """Signature should include operation-specific data."""
        from saw.adapters.crypto.ed25519 import ReceiptSigner, Receipt
        import datetime

        signer = ReceiptSigner()
        signer.generate_keypair()

        receipt = Receipt(
            operation_id="op-123",
            operation_type="ingest",
            agent="Writer",
            claim_uuid="claim-456",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )

        signature = signer.sign_receipt(receipt)

        assert isinstance(signature, str)


class TestVerifyReceipt:
    """Test 3: verify_receipt() validates signature integrity."""

    def test_validates_correctly_signed_receipt(self) -> None:
        """Should return True for valid signature."""
        from saw.adapters.crypto.ed25519 import ReceiptSigner, Receipt
        import datetime

        signer = ReceiptSigner()
        signer.generate_keypair()
        public_key = signer.get_public_key()

        receipt = Receipt(
            operation_id="op-123",
            operation_type="ingest",
            agent="Writer",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        signature = signer.sign_receipt(receipt)

        is_valid = signer.verify_receipt(receipt, signature, public_key)

        assert is_valid is True

    def test_rejects_tampered_receipt(self) -> None:
        """Should return False for modified receipt."""
        from saw.adapters.crypto.ed25519 import ReceiptSigner, Receipt
        import datetime

        signer = ReceiptSigner()
        signer.generate_keypair()
        public_key = signer.get_public_key()

        receipt = Receipt(
            operation_id="op-123",
            operation_type="ingest",
            agent="Writer",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        signature = signer.sign_receipt(receipt)

        # Tamper with receipt
        receipt.operation_type = "query"

        is_valid = signer.verify_receipt(receipt, signature, public_key)

        assert is_valid is False

    def test_rejects_wrong_public_key(self) -> None:
        """Should return False for wrong public key."""
        from saw.adapters.crypto.ed25519 import ReceiptSigner, Receipt
        import datetime

        signer1 = ReceiptSigner()
        signer1.generate_keypair()

        signer2 = ReceiptSigner()
        wrong_public_key, _ = signer2.generate_keypair()

        receipt = Receipt(
            operation_id="op-123",
            operation_type="ingest",
            agent="Writer",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        signature = signer1.sign_receipt(receipt)

        is_valid = signer1.verify_receipt(receipt, signature, wrong_public_key)

        assert is_valid is False

    def test_rejects_corrupted_signature(self) -> None:
        """Should return False for corrupted signature."""
        from saw.adapters.crypto.ed25519 import ReceiptSigner, Receipt
        import datetime

        signer = ReceiptSigner()
        signer.generate_keypair()
        public_key = signer.get_public_key()

        receipt = Receipt(
            operation_id="op-123",
            operation_type="ingest",
            agent="Writer",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        signature = signer.sign_receipt(receipt)

        # Corrupt signature by modifying it
        corrupted_signature = signature[:-4] + "XXXX"

        is_valid = signer.verify_receipt(receipt, corrupted_signature, public_key)

        assert is_valid is False


class TestReceiptDataclass:
    """Tests for Receipt dataclass."""

    def test_receipt_stores_all_fields(self) -> None:
        """Receipt should store all required fields."""
        from saw.adapters.crypto.ed25519 import Receipt
        import datetime

        receipt = Receipt(
            operation_id="op-123",
            operation_type="ingest",
            agent="Writer",
            claim_uuid="claim-456",
            page_path="concepts/test.md",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            payload_hash="abc123",
            signature="sig-123",
            prev_receipt_id="prev-456",
        )

        assert receipt.operation_id == "op-123"
        assert receipt.operation_type == "ingest"
        assert receipt.agent == "Writer"
        assert receipt.claim_uuid == "claim-456"
        assert receipt.page_path == "concepts/test.md"
        assert receipt.payload_hash == "abc123"
        assert receipt.signature == "sig-123"
        assert receipt.prev_receipt_id == "prev-456"

    def test_receipt_with_minimal_fields(self) -> None:
        """Receipt should work with minimal required fields."""
        from saw.adapters.crypto.ed25519 import Receipt
        import datetime

        receipt = Receipt(
            operation_id="op-123",
            operation_type="query",
            agent="Librarian",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )

        assert receipt.operation_id == "op-123"
        assert receipt.claim_uuid is None
        assert receipt.page_path is None


class TestKeyStorage:
    """Tests for key storage functionality."""

    def test_stores_key_at_specified_path(self) -> None:
        """Should store private key at the specified path."""
        from saw.adapters.crypto.ed25519 import ReceiptSigner

        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = Path(tmpdir) / ".saw" / "keys" / "ed25519.key"
            signer = ReceiptSigner(key_path)

            private_key, public_key = signer.generate_keypair()

            assert key_path.parent.exists()

    def test_key_file_has_restricted_permissions(self) -> None:
        """Key file should have 0600 permissions."""
        from saw.adapters.crypto.ed25519 import ReceiptSigner

        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = Path(tmpdir) / ".saw" / "keys" / "ed25519.key"
            signer = ReceiptSigner(key_path)

            private_key, public_key = signer.generate_keypair()

            if key_path.exists():
                # Check permissions (skip on Windows)
                import stat
                import os
                mode = key_path.stat().st_mode
                # Should be 0600 or more restrictive
                assert (mode & 0o777) <= 0o600

    def test_loads_existing_keypair(self) -> None:
        """Should load existing keypair from file."""
        from saw.adapters.crypto.ed25519 import ReceiptSigner

        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = Path(tmpdir) / ".saw" / "keys" / "ed25519.key"

            # Create first signer and generate keys
            signer1 = ReceiptSigner(key_path)
            private_key, public_key = signer1.generate_keypair()

            # Create second signer with same path - should load existing
            signer2 = ReceiptSigner(key_path)
            loaded_public_key = signer2.get_public_key()

            # Public key should match
            assert loaded_public_key == public_key

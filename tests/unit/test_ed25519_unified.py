"""Tests for the unified Ed25519 signing path (C5/C1).

Verifies:
- ``ReceiptSigner.sign_message`` / ``verify_message`` round-trip
- ``AuditSigner`` delegates to a persistent ``ReceiptSigner`` (PyNaCl,
  base64) and persists its key to ``.saw/keys/ed25519.key``
- a signature produced by one ``AuditSigner`` instance verifies under a
  fresh instance constructed from the same key file (cross-restart)
"""
from __future__ import annotations

from pathlib import Path

from saw.adapters.crypto.ed25519 import ReceiptSigner
from saw.audit.service import AuditSigner


def _key_path(tmp_path: Path) -> Path:
    return tmp_path / "keys" / "ed25519.key"


class TestReceiptSignerMessages:
    def test_sign_and_verify_roundtrip(self, tmp_path):
        signer = ReceiptSigner(key_path=_key_path(tmp_path))
        signer.generate_keypair()
        pub = signer.get_public_key()
        sig = signer.sign_message("hello audit")
        assert signer.verify_message("hello audit", sig, pub) is True

    def test_verify_rejects_wrong_message(self, tmp_path):
        signer = ReceiptSigner(key_path=_key_path(tmp_path))
        signer.generate_keypair()
        sig = signer.sign_message("original")
        assert signer.verify_message("tampered", sig, signer.get_public_key()) is False

    def test_sign_without_key_raises(self, tmp_path):
        signer = ReceiptSigner(key_path=None)
        import pytest

        with pytest.raises(ValueError):
            signer.sign_message("nope")


class TestAuditSignerPersistence:
    def test_generates_and_persists_key(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        signer = AuditSigner()
        # Key file created under .saw/keys/ed25519.key
        assert (tmp_path / ".saw" / "keys" / "ed25519.key").exists()
        assert signer.get_public_key_hex() is not None

    def test_cross_instance_verify(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        signer_a = AuditSigner()
        message = "audit-event-1"
        signature = signer_a.sign(message)
        assert signature is not None

        # A second instance loads the same persisted key and must verify.
        signer_b = AuditSigner()
        assert signer_b.verify(message, signature) is True

    def test_verify_rejects_foreign_signature(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        foreign = AuditSigner(key_path=tmp_path / "other.key")
        foreign_sig = foreign.sign("msg")
        assert foreign_sig is not None

        signer = AuditSigner()
        # Different keys → verification fails.
        assert signer.verify("msg", foreign_sig) is False

    def test_sign_returns_base64(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import base64

        sig = AuditSigner().sign("msg")
        assert sig is not None
        # Must decode as base64 (PyNaCl path), not hex.
        base64.b64decode(sig)

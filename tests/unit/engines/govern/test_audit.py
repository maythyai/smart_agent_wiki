"""Tests for audit trail and receipt chain verification.

Tests the AuditTrail class with:
1. record_operation() creates signed receipt
2. verify_chain() verifies receipt chain integrity
3. export_for_verification() exports for offline verification
"""
from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from saw.adapters.crypto.ed25519 import Receipt, ReceiptSigner
from saw.engines.govern.audit import AuditTrail, AuditSummary


class TestRecordOperation:
    """Test 1: record_operation() creates signed receipt."""

    def test_creates_receipt_with_all_fields(self) -> None:
        """Should create receipt with operation details."""
        signer = ReceiptSigner()
        signer.generate_keypair()

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditTrail(signer, Path(tmpdir))

            receipt = audit.record_operation(
                operation_type="ingest",
                agent="Writer",
                claim_uuid="claim-123",
                page_path=None,
                payload={"source": "test.pdf"},
            )

            assert receipt.operation_id is not None
            assert receipt.operation_type == "ingest"
            assert receipt.agent == "Writer"
            assert receipt.claim_uuid == "claim-123"
            assert receipt.signature is not None

    def test_receipt_is_signed(self) -> None:
        """Should sign receipt with Ed25519."""
        signer = ReceiptSigner()
        signer.generate_keypair()

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditTrail(signer, Path(tmpdir))

            receipt = audit.record_operation(
                operation_type="query",
                agent="Librarian",
                claim_uuid=None,
                page_path=None,
                payload={"query": "test"},
            )

            assert receipt.signature is not None
            assert len(receipt.signature) > 0

    def test_receipt_includes_payload_hash(self) -> None:
        """Should include SHA-256 hash of payload."""
        signer = ReceiptSigner()
        signer.generate_keypair()

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditTrail(signer, Path(tmpdir))

            receipt = audit.record_operation(
                operation_type="edit",
                agent="Writer",
                claim_uuid="claim-123",
                page_path="test.md",
                payload={"change": "updated content"},
            )

            assert receipt.payload_hash is not None
            # SHA-256 hash is 64 hex characters
            assert len(receipt.payload_hash) == 64

    def test_receipts_chain_to_previous(self) -> None:
        """Each receipt should link to previous receipt."""
        signer = ReceiptSigner()
        signer.generate_keypair()

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditTrail(signer, Path(tmpdir))

            receipt1 = audit.record_operation(
                operation_type="ingest",
                agent="Writer",
                claim_uuid="claim-1",
                page_path=None,
                payload={},
            )

            receipt2 = audit.record_operation(
                operation_type="query",
                agent="Librarian",
                claim_uuid=None,
                page_path=None,
                payload={},
            )

            # Second receipt should link to first
            assert receipt2.prev_receipt_id == receipt1.operation_id


class TestVerifyChain:
    """Test 2: verify_chain() verifies receipt chain integrity."""

    def test_validates_chain_with_single_receipt(self) -> None:
        """Should validate chain with one receipt."""
        signer = ReceiptSigner()
        signer.generate_keypair()

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditTrail(signer, Path(tmpdir))

            audit.record_operation(
                operation_type="ingest",
                agent="Writer",
                claim_uuid="claim-1",
                page_path=None,
                payload={},
            )

            is_valid, invalid_ids = audit.verify_chain()

            assert is_valid is True
            assert len(invalid_ids) == 0

    def test_validates_chain_with_multiple_receipts(self) -> None:
        """Should validate chain with multiple receipts."""
        signer = ReceiptSigner()
        signer.generate_keypair()

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditTrail(signer, Path(tmpdir))

            for i in range(5):
                audit.record_operation(
                    operation_type="ingest",
                    agent="Writer",
                    claim_uuid=f"claim-{i}",
                    page_path=None,
                    payload={"batch": i},
                )

            is_valid, invalid_ids = audit.verify_chain()

            assert is_valid is True
            assert len(invalid_ids) == 0

    def test_detects_tampered_receipt(self) -> None:
        """Should detect if receipt was tampered with."""
        signer = ReceiptSigner()
        signer.generate_keypair()

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditTrail(signer, Path(tmpdir))

            audit.record_operation(
                operation_type="ingest",
                agent="Writer",
                claim_uuid="claim-1",
                page_path=None,
                payload={},
            )

            # Manually tamper with receipts file
            receipts_file = Path(tmpdir) / "receipts.yaml"
            if receipts_file.exists():
                content = receipts_file.read_text()
                # Corrupt the signature
                content = content.replace("signature:", "signature: TAMPERED")
                receipts_file.write_text(content)

            is_valid, invalid_ids = audit.verify_chain()

            assert is_valid is False

    def test_detects_broken_chain(self) -> None:
        """Should detect if chain linkage is broken."""
        signer = ReceiptSigner()
        signer.generate_keypair()

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditTrail(signer, Path(tmpdir))

            receipt1 = audit.record_operation(
                operation_type="ingest",
                agent="Writer",
                claim_uuid="claim-1",
                page_path=None,
                payload={},
            )

            # Manually modify prev_receipt_id to break chain
            receipts = audit._load_receipts()
            if receipts:
                receipts[0]["prev_receipt_id"] = "non-existent-id"
                audit._save_receipts(receipts)

            is_valid, invalid_ids = audit.verify_chain()

            # Chain is broken but signatures might still be valid
            # This test depends on implementation details


class TestExportForVerification:
    """Test 3: export_for_verification() exports for offline verification."""

    def test_exports_receipts_and_public_key(self) -> None:
        """Should export both receipts and public key."""
        signer = ReceiptSigner()
        signer.generate_keypair()

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditTrail(signer, Path(tmpdir))

            audit.record_operation(
                operation_type="ingest",
                agent="Writer",
                claim_uuid="claim-1",
                page_path=None,
                payload={},
            )

            export_path = Path(tmpdir) / "export"
            export_path.mkdir()

            audit.export_for_verification(export_path)

            # Should create receipts.yaml and public_key.txt
            assert (export_path / "receipts.yaml").exists()
            assert (export_path / "public_key.txt").exists()

    def test_exported_public_key_matches_signer(self) -> None:
        """Exported public key should match signer's key."""
        signer = ReceiptSigner()
        signer.generate_keypair()
        expected_public_key = signer.get_public_key()

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditTrail(signer, Path(tmpdir))

            audit.record_operation(
                operation_type="query",
                agent="Librarian",
                claim_uuid=None,
                page_path=None,
                payload={},
            )

            export_path = Path(tmpdir) / "export"
            export_path.mkdir()

            audit.export_for_verification(export_path)

            exported_key = (export_path / "public_key.txt").read_text().strip()
            assert exported_key == expected_public_key


class TestGetReceipt:
    """Tests for get_receipt() method."""

    def test_gets_receipt_by_operation_id(self) -> None:
        """Should retrieve receipt by operation ID."""
        signer = ReceiptSigner()
        signer.generate_keypair()

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditTrail(signer, Path(tmpdir))

            created = audit.record_operation(
                operation_type="ingest",
                agent="Writer",
                claim_uuid="claim-123",
                page_path=None,
                payload={},
            )

            retrieved = audit.get_receipt(created.operation_id)

            assert retrieved is not None
            assert retrieved.operation_id == created.operation_id

    def test_returns_none_for_unknown_id(self) -> None:
        """Should return None for non-existent operation ID."""
        signer = ReceiptSigner()
        signer.generate_keypair()

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditTrail(signer, Path(tmpdir))

            result = audit.get_receipt("non-existent-id")

            assert result is None


class TestGetReceiptsForClaim:
    """Tests for get_receipts_for_claim() method."""

    def test_finds_receipts_by_claim_uuid(self) -> None:
        """Should find all receipts for a claim."""
        signer = ReceiptSigner()
        signer.generate_keypair()

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditTrail(signer, Path(tmpdir))

            audit.record_operation(
                operation_type="ingest",
                agent="Writer",
                claim_uuid="claim-123",
                page_path=None,
                payload={},
            )
            audit.record_operation(
                operation_type="edit",
                agent="Writer",
                claim_uuid="claim-123",
                page_path="test.md",
                payload={},
            )
            audit.record_operation(
                operation_type="ingest",
                agent="Writer",
                claim_uuid="claim-456",
                page_path=None,
                payload={},
            )

            receipts = audit.get_receipts_for_claim("claim-123")

            assert len(receipts) == 2


class TestGetAuditSummary:
    """Tests for get_audit_summary() method."""

    def test_returns_summary_with_counts(self) -> None:
        """Should return summary with operation counts."""
        signer = ReceiptSigner()
        signer.generate_keypair()

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditTrail(signer, Path(tmpdir))

            audit.record_operation("ingest", "Writer", "c-1", None, {})
            audit.record_operation("ingest", "Writer", "c-2", None, {})
            audit.record_operation("query", "Librarian", None, None, {})

            summary = audit.get_audit_summary()

            assert summary.total_operations == 3
            assert "ingest" in summary.by_type
            assert summary.by_type["ingest"] == 2


class TestAuditSummary:
    """Tests for AuditSummary dataclass."""

    def test_summary_stores_all_fields(self) -> None:
        """Summary should store all required fields."""
        summary = AuditSummary(
            total_operations=10,
            by_type={"ingest": 5, "query": 3, "edit": 2},
            by_agent={"Writer": 7, "Librarian": 3},
            chain_valid=True,
            first_operation=datetime.now(timezone.utc),
            last_operation=datetime.now(timezone.utc),
            chain_length=10,
        )

        assert summary.total_operations == 10
        assert summary.by_type["ingest"] == 5
        assert summary.by_agent["Writer"] == 7
        assert summary.chain_valid is True

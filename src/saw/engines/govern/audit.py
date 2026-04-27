"""Audit trail and receipt chain management.

Per D-08: Every operation produces a signed receipt.
Per GOVE-08: Offline-verifiable receipt chain.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from saw.adapters.crypto.ed25519 import Receipt, ReceiptSigner


@dataclass
class AuditSummary:
    """Summary of audit trail state.

    Used for CLI display and verification.
    """
    total_operations: int = 0
    by_type: dict[str, int] = field(default_factory=dict)
    by_agent: dict[str, int] = field(default_factory=dict)
    chain_valid: bool = True
    first_operation: datetime | None = None
    last_operation: datetime | None = None
    chain_length: int = 0


class AuditTrail:
    """Audit trail with Ed25519 signed receipts.

    Per D-08: Every agent operation generates a signed receipt.
    Per GOVE-08: Chain can be verified offline.
    """

    def __init__(
        self,
        signer: ReceiptSigner,
        storage_path: Path,
    ) -> None:
        """Initialize audit trail.

        Args:
            signer: ReceiptSigner for signing operations.
            storage_path: Directory to store receipts.yaml.
        """
        self._signer = signer
        self._storage_path = storage_path
        self._receipts_file = storage_path / "receipts.yaml"
        self._prev_receipt_id: str | None = None

        # Ensure storage directory exists
        self._storage_path.mkdir(parents=True, exist_ok=True)

        # Load existing receipts to get chain info
        self._load_chain_state()

    def _load_chain_state(self) -> None:
        """Load existing receipts to restore chain state."""
        receipts = self._load_receipts()
        if receipts:
            # Get the last receipt ID for chaining
            self._prev_receipt_id = receipts[-1].get("operation_id")

    def record_operation(
        self,
        operation_type: str,
        agent: str,
        claim_uuid: str | None,
        page_path: str | None,
        payload: dict[str, Any],
    ) -> Receipt:
        """Record an operation with signed receipt.

        Per D-08: Creates receipt with payload hash, signs with Ed25519,
        chains to previous receipt, persists to .saw/audit/receipts.yaml.

        Args:
            operation_type: Type of operation (ingest/query/edit/review).
            agent: Agent that performed the operation.
            claim_uuid: UUID of affected claim, if any.
            page_path: Path of affected page, if any.
            payload: Operation details for hash computation.

        Returns:
            The created and signed Receipt.
        """
        # Generate operation ID
        operation_id = str(uuid.uuid4())

        # Compute payload hash
        payload_hash = self._signer.compute_payload_hash(payload)

        # Create receipt
        receipt = Receipt(
            operation_id=operation_id,
            operation_type=operation_type,
            agent=agent,
            timestamp=datetime.now(timezone.utc),
            claim_uuid=claim_uuid,
            page_path=page_path,
            payload_hash=payload_hash,
            prev_receipt_id=self._prev_receipt_id,
        )

        # Sign receipt
        signature = self._signer.sign_receipt(receipt)
        receipt.signature = signature

        # Persist receipt
        self._persist_receipt(receipt)

        # Update chain state
        self._prev_receipt_id = operation_id

        return receipt

    def _persist_receipt(self, receipt: Receipt) -> None:
        """Persist receipt to storage.

        Args:
            receipt: Receipt to persist.
        """
        # Load existing receipts
        receipts = self._load_receipts()

        # Add new receipt
        receipt_data = {
            "operation_id": receipt.operation_id,
            "operation_type": receipt.operation_type,
            "agent": receipt.agent,
            "claim_uuid": receipt.claim_uuid,
            "page_path": receipt.page_path,
            "timestamp": receipt.timestamp.isoformat(),
            "payload_hash": receipt.payload_hash,
            "signature": receipt.signature,
            "prev_receipt_id": receipt.prev_receipt_id,
        }
        receipts.append(receipt_data)

        # Save with public key
        self._save_receipts(receipts)

    def _load_receipts(self) -> list[dict[str, Any]]:
        """Load receipts from storage.

        Returns:
            List of receipt dictionaries.
        """
        if not self._receipts_file.exists():
            return []

        try:
            with open(self._receipts_file, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return data.get("receipts", [])
        except Exception:
            return []

    def _save_receipts(self, receipts: list[dict[str, Any]]) -> None:
        """Save receipts to storage.

        Args:
            receipts: List of receipt dictionaries.
        """
        public_key = self._signer.get_public_key() or ""

        data = {
            "public_key": public_key,
            "receipts": receipts,
        }

        with open(self._receipts_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False)

    def verify_chain(
        self,
        start_id: str | None = None,
    ) -> tuple[bool, list[str]]:
        """Verify receipt chain integrity.

        Checks:
        1. All signatures are valid
        2. Chain linkage is correct (prev_receipt_id matches)
        3. No missing or duplicate receipts

        Args:
            start_id: Optional starting receipt ID. If None, verifies all.

        Returns:
            Tuple of (is_valid, list_of_invalid_receipt_ids).
        """
        receipts = self._load_receipts()
        public_key = self._signer.get_public_key()

        if not receipts:
            return True, []

        invalid_ids: list[str] = []
        seen_ids: set[str] = set()

        # Find starting point if specified
        start_index = 0
        if start_id:
            for i, r in enumerate(receipts):
                if r.get("operation_id") == start_id:
                    start_index = i
                    break

        prev_id: str | None = None
        for i, r in enumerate(receipts[start_index:], start=start_index):
            receipt_id = r.get("operation_id")

            # Check for duplicates
            if receipt_id in seen_ids:
                invalid_ids.append(receipt_id)
                continue
            seen_ids.add(receipt_id)

            # Check chain linkage (skip for first receipt if starting from beginning)
            if i > start_index and r.get("prev_receipt_id") != prev_id:
                invalid_ids.append(receipt_id)

            # Verify signature
            receipt_obj = Receipt(
                operation_id=receipt_id,
                operation_type=r.get("operation_type", ""),
                agent=r.get("agent", ""),
                timestamp=datetime.fromisoformat(r.get("timestamp", "")),
                claim_uuid=r.get("claim_uuid"),
                page_path=r.get("page_path"),
                payload_hash=r.get("payload_hash"),
                prev_receipt_id=r.get("prev_receipt_id"),
            )

            signature = r.get("signature", "")
            if public_key and signature:
                is_valid = self._signer.verify_receipt(
                    receipt_obj, signature, public_key
                )
                if not is_valid:
                    invalid_ids.append(receipt_id)

            prev_id = receipt_id

        return len(invalid_ids) == 0, invalid_ids

    def get_receipt(self, operation_id: str) -> Receipt | None:
        """Get receipt by operation ID.

        Args:
            operation_id: UUID of the operation.

        Returns:
            Receipt if found, None otherwise.
        """
        receipts = self._load_receipts()

        for r in receipts:
            if r.get("operation_id") == operation_id:
                return Receipt(
                    operation_id=operation_id,
                    operation_type=r.get("operation_type", ""),
                    agent=r.get("agent", ""),
                    timestamp=datetime.fromisoformat(r.get("timestamp", "")),
                    claim_uuid=r.get("claim_uuid"),
                    page_path=r.get("page_path"),
                    payload_hash=r.get("payload_hash"),
                    signature=r.get("signature"),
                    prev_receipt_id=r.get("prev_receipt_id"),
                )

        return None

    def get_receipts_for_claim(self, claim_uuid: str) -> list[Receipt]:
        """Get all receipts for a specific claim.

        Args:
            claim_uuid: UUID of the claim.

        Returns:
            List of receipts affecting this claim.
        """
        receipts = self._load_receipts()
        result: list[Receipt] = []

        for r in receipts:
            if r.get("claim_uuid") == claim_uuid:
                result.append(Receipt(
                    operation_id=r.get("operation_id", ""),
                    operation_type=r.get("operation_type", ""),
                    agent=r.get("agent", ""),
                    timestamp=datetime.fromisoformat(r.get("timestamp", "")),
                    claim_uuid=claim_uuid,
                    page_path=r.get("page_path"),
                    payload_hash=r.get("payload_hash"),
                    signature=r.get("signature"),
                    prev_receipt_id=r.get("prev_receipt_id"),
                ))

        return result

    def export_for_verification(self, output_path: Path) -> None:
        """Export receipts and public key for offline verification.

        Per GOVE-08: Enables verification without running the system.

        Args:
            output_path: Directory to export to.
        """
        output_path.mkdir(parents=True, exist_ok=True)

        # Export receipts
        receipts = self._load_receipts()
        public_key = self._signer.get_public_key() or ""

        data = {
            "public_key": public_key,
            "receipts": receipts,
        }

        with open(output_path / "receipts.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False)

        # Export public key separately
        with open(output_path / "public_key.txt", "w", encoding="ascii") as f:
            f.write(public_key)

    def get_audit_summary(self) -> AuditSummary:
        """Get summary of audit trail.

        Returns:
            AuditSummary with operation counts and chain status.
        """
        receipts = self._load_receipts()

        if not receipts:
            return AuditSummary()

        by_type: dict[str, int] = {}
        by_agent: dict[str, int] = {}

        for r in receipts:
            op_type = r.get("operation_type", "unknown")
            by_type[op_type] = by_type.get(op_type, 0) + 1

            agent = r.get("agent", "unknown")
            by_agent[agent] = by_agent.get(agent, 0) + 1

        # Verify chain
        is_valid, _ = self.verify_chain()

        # Get timestamps
        first_ts = datetime.fromisoformat(receipts[0].get("timestamp", ""))
        last_ts = datetime.fromisoformat(receipts[-1].get("timestamp", ""))

        return AuditSummary(
            total_operations=len(receipts),
            by_type=by_type,
            by_agent=by_agent,
            chain_valid=is_valid,
            first_operation=first_ts,
            last_operation=last_ts,
            chain_length=len(receipts),
        )

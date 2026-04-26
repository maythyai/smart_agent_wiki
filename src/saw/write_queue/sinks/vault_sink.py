"""Vault sink - writes source documents to immutable vault storage.

Per Pitfall 7: idempotent (if vault/{uuid}/ exists, skip).
Vault writes happen FIRST (per Pitfall 7 recommendation 4).
"""
from __future__ import annotations

from pathlib import Path

from saw.adapters.storage.vault_repository import VaultRepository
from saw.domain.exceptions import VaultError


class VaultSink:
    """Write Queue sink for vault storage."""

    def __init__(self, vault_repo: VaultRepository) -> None:
        self._repo = vault_repo

    @property
    def name(self) -> str:
        return "vault"

    def write(self, op) -> None:
        """Write a vault entry from a WriteOp.

        Idempotent: if vault/{uuid}/ exists, skip.
        """
        payload = op.payload
        uuid = payload.get("uuid", op.op_id)
        source_path = payload.get("source_path")
        metadata = payload.get("metadata", {})

        if not source_path:
            raise VaultError(f"Vault sink: missing source_path in op {op.op_id}")

        self._repo.store(Path(source_path), uuid, metadata)

    def can_handle(self, sink_name: str) -> bool:
        return sink_name == "vault"

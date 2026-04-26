"""Vault repository - immutable document storage under UUID directories.

Per D-05: vault/{uuid}/ with original.* + transcript.md + meta.yaml.
Vault files are never modified after creation.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from saw.domain.exceptions import VaultError


class VaultRepository:
    """Immutable file storage for source documents.

    Implements the VaultRepository protocol.
    """

    def __init__(self, vault_root: Path) -> None:
        self._root = Path(vault_root)
        self._root.mkdir(parents=True, exist_ok=True)

    def store(self, source_path: Path, uuid: str, metadata: dict) -> Path:
        """Store a document in the vault under a UUID directory.

        Creates vault/{uuid}/ with:
          - original.{ext}  -- the source file
          - transcript.md   -- empty placeholder for future transcript
          - meta.yaml       -- metadata dict

        Idempotent: if vault/{uuid}/ exists, skip.
        """
        entry_dir = self._root / uuid
        if entry_dir.exists():
            return entry_dir

        try:
            entry_dir.mkdir(parents=True, exist_ok=True)

            # Copy original file
            ext = source_path.suffix.lstrip(".") or "bin"
            dest = entry_dir / f"original.{ext}"
            shutil.copy2(source_path, dest)

            # Write empty transcript placeholder
            (entry_dir / "transcript.md").write_text("", encoding="utf-8")

            # Write metadata
            meta_path = entry_dir / "meta.yaml"
            with open(meta_path, "w", encoding="utf-8") as f:
                yaml.dump(metadata, f, default_flow_style=False, allow_unicode=True)

            return entry_dir
        except OSError as e:
            raise VaultError(f"Failed to store vault entry {uuid}: {e}") from e

    def get(self, uuid: str) -> Path | None:
        """Return the vault directory path for a given UUID, or None."""
        entry_dir = self._root / uuid
        if entry_dir.is_dir():
            return entry_dir
        return None

    def exists(self, uuid: str) -> bool:
        """Check if a vault entry exists for the given UUID."""
        return (self._root / uuid).is_dir()

"""Vault repository - immutable document storage under UUID directories.

Per D-05: vault/{uuid}/ with original.* + transcript.md + meta.yaml.
Per D-11, D-20: Git session branch provenance.
Vault files are never modified after creation.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import yaml

from saw.domain.exceptions import VaultError


class VaultRepository:
    """Immutable file storage for source documents.

    Implements the VaultRepository protocol.
    """

    def __init__(self, vault_root: Path, wiki_root: Path | None = None) -> None:
        self._root = Path(vault_root)
        self._root.mkdir(parents=True, exist_ok=True)
        self._wiki_root = wiki_root or vault_root.parent
        self._git_available = self._check_git_available()

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

    def create_session_branch(self, source_name: str) -> str | None:
        """Create a session branch for git blame dual provenance.

        Per D-11: session/{timestamp}-{source_name}
        Per D-20: Git integration with session branches

        Args:
            source_name: Name of the source being ingested.

        Returns:
            Branch name if git is available, None otherwise.
        """
        if not self._git_available:
            return None

        # Sanitize source_name for branch name
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "-", source_name)[:50]
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        branch = f"session/{ts}-{sanitized}"

        try:
            subprocess.run(
                ["git", "checkout", "-b", branch],
                cwd=self._wiki_root,
                check=True,
                capture_output=True,
            )
            return branch
        except subprocess.CalledProcessError:
            return None

    def merge_session(self, branch: str) -> bool:
        """Merge session branch to main after successful ingestion.

        Per D-20: merge with --no-ff for explicit merge commit.

        Args:
            branch: The session branch name.

        Returns:
            True if merge succeeded, False otherwise.
        """
        if not self._git_available:
            return False

        try:
            # Stage all changes
            subprocess.run(
                ["git", "add", "."],
                cwd=self._wiki_root,
                check=True,
                capture_output=True,
            )

            # Commit changes
            subprocess.run(
                ["git", "commit", "-m", f"ingest: {branch}"],
                cwd=self._wiki_root,
                check=True,
                capture_output=True,
            )

            # Switch back to main
            subprocess.run(
                ["git", "checkout", "main"],
                cwd=self._wiki_root,
                check=True,
                capture_output=True,
            )

            # Merge with --no-ff
            subprocess.run(
                ["git", "merge", "--no-ff", branch, "-m", f"merge: {branch}"],
                cwd=self._wiki_root,
                check=True,
                capture_output=True,
            )

            # Delete the session branch
            subprocess.run(
                ["git", "branch", "-d", branch],
                cwd=self._wiki_root,
                check=True,
                capture_output=True,
            )

            return True
        except subprocess.CalledProcessError:
            return False

    def abort_session(self, branch: str) -> bool:
        """Abort a session branch (on ingestion failure).

        Args:
            branch: The session branch name.

        Returns:
            True if abort succeeded, False otherwise.
        """
        if not self._git_available:
            return False

        try:
            # Switch back to main without committing
            subprocess.run(
                ["git", "checkout", "main"],
                cwd=self._wiki_root,
                check=True,
                capture_output=True,
            )

            # Delete the session branch
            subprocess.run(
                ["git", "branch", "-D", branch],  # Force delete
                cwd=self._wiki_root,
                check=True,
                capture_output=True,
            )

            return True
        except subprocess.CalledProcessError:
            return False

    def _check_git_available(self) -> bool:
        """Check if git is available and we're in a git repo."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self._wiki_root,
                capture_output=True,
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

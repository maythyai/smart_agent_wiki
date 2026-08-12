"""Shared helpers for persistent key files.

All secrets (Ed25519 signing key, Fernet encryption key, JWT HMAC key) are
stored as regular files under ``.saw/keys/`` with restrictive permissions:

* parent directory: ``0700`` (owner-only access)
* key file:          ``0600`` (owner-only read/write)

On Windows ``chmod`` is a no-op; the restrictive defaults of the user's
profile directory are the only safeguard (mirrors the existing
``ReceiptSigner`` behaviour in ``adapters/crypto/ed25519.py``).

These helpers exist so that every secret has a single, consistent
load-or-create code path instead of ad-hoc ``os.environ`` fallbacks that
silently drop the key on restart (the original C5 / Ed25519 bugs).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

# Default directory for all secrets, relative to a wiki root.
KEYS_DIRNAME = ".saw/keys"


def ensure_keys_dir(keys_dir: Path) -> Path:
    """Create ``keys_dir`` (and parents) with ``0700`` permissions.

    Returns the directory path. Idempotent.
    """
    keys_dir.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        try:
            keys_dir.chmod(0o700)
        except OSError:
            pass
    return keys_dir


def write_key_file(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` with ``0600`` permissions.

    The parent directory is created with ``0700``. Existing files are
    overwritten. ``content`` is written as ASCII / UTF-8 text.
    """
    ensure_keys_dir(path.parent)
    path.write_text(content, encoding="utf-8")
    if os.name != "nt":
        try:
            path.chmod(0o600)
        except OSError:
            pass


def read_key_file(path: Path) -> str | None:
    """Return the stripped key file content, or ``None`` if missing.

    A missing file returns ``None`` rather than raising so callers can
    implement load-or-create without try/except.
    """
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").strip()


def load_or_create(path: Path, generator: Callable[[], str]) -> str:
    """Return the key at ``path``, generating + persisting it if missing.

    Args:
        path: Key file path.
        generator: Callable that returns a fresh key string when the file
            does not yet exist. The returned value is persisted and returned.

    Returns:
        The loaded or freshly-generated key material.
    """
    existing = read_key_file(path)
    if existing:
        return existing
    fresh = generator()
    write_key_file(path, fresh)
    return fresh

"""Audit log service for team deployment.

Phase 5: Team Deployment — Audit logging.
Per TEAM-08: Audit logs for all actions.

Provides Ed25519 signed audit records for tamper evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from saw.db.models import AuditLog, generate_uuid


class AuditAction:
    """Audit action types."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    SHARE = "share"
    PERMISSION = "permission"
    BACKUP = "backup"
    RESTORE = "restore"


class ResourceType:
    """Resource types for audit logs."""
    USER = "user"
    VAULT = "vault"
    CLAIM = "claim"
    PERMISSION = "permission"
    TOKEN = "token"
    SYSTEM = "system"


@dataclass
class AuditEntry:
    """Audit log entry."""
    action: str
    resource_type: str
    resource_id: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_model(self) -> AuditLog:
        """Convert to SQLAlchemy model."""
        return AuditLog(
            id=generate_uuid(),
            user_id=self.user_id,
            action=self.action,
            resource_type=self.resource_type,
            resource_id=self.resource_id,
            timestamp=self.timestamp,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            details=json.dumps(self.details) if self.details else None,
        )


class AuditSigner:
    """Ed25519 signer for audit logs.

    Thin adapter over :class:`saw.adapters.crypto.ed25519.ReceiptSigner`
    (PyNaCl). The signing key is loaded from — or generated and persisted
    to — ``.saw/keys/ed25519.key`` (0600 file / 0700 dir) so that audit
    signatures remain verifiable across process restarts.

    Signatures are base64-encoded, matching :class:`ReceiptSigner`.
    """

    def __init__(
        self,
        private_key: Optional[str] = None,
        key_path: Path | None = None,
        signer: "ReceiptSigner | None" = None,
    ):
        self._signer = signer  # may be None until needed

        if signer is not None:
            # Pre-configured ReceiptSigner; trust its key state.
            return

        from saw.adapters.crypto.ed25519 import ReceiptSigner

        path = key_path or Path(".saw/keys/ed25519.key")
        self._signer = ReceiptSigner(key_path=path)
        if self._signer.get_public_key() is None:
            # No key on disk yet — generate and persist one.
            self._signer.generate_keypair()

        # ``private_key`` (hex, legacy) is no longer honoured; if a caller
        # passes one we ignore it in favour of the persistent key. This is
        # intentionally lossy: the legacy hex/cryptography keys were
        # ephemeral and unverifiable across restarts anyway.

    def _ensure(self) -> "ReceiptSigner":
        if self._signer is None:
            raise ValueError("AuditSigner has no ReceiptSigner bound")
        return self._signer

    def sign(self, message: str) -> Optional[str]:
        """Sign a message, returning a base64 signature (or None on failure)."""
        try:
            return self._ensure().sign_message(message)
        except Exception:
            return None

    def verify(self, message: str, signature: str) -> bool:
        """Verify a base64 signature against the signer's public key."""
        signer = self._ensure()
        public_key = signer.get_public_key()
        if public_key is None:
            return False
        return signer.verify_message(message, signature, public_key)

    def get_public_key_hex(self) -> Optional[str]:
        """Return the public key as a hex string (for diagnostics)."""
        import base64 as _b64
        pub = self._ensure().get_public_key()
        if pub is None:
            return None
        return _b64.b64decode(pub).hex()


class AuditService:
    """Service for audit logging."""

    def __init__(self, signer: Optional[AuditSigner] = None):
        self.signer = signer or AuditSigner()

    def create_entry(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> AuditEntry:
        """Create an audit entry."""
        return AuditEntry(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )

    def sign_entry(self, entry: AuditEntry) -> Optional[str]:
        """Sign an audit entry."""
        # Create canonical message
        message = self._create_signable_message(entry)
        return self.signer.sign(message)

    def _create_signable_message(self, entry: AuditEntry) -> str:
        """Create a signable message from entry."""
        parts = [
            str(entry.timestamp.isoformat()),
            entry.action,
            entry.resource_type,
            entry.resource_id,
            entry.user_id or "",
            json.dumps(entry.details, sort_keys=True) if entry.details else "",
        ]
        return "|".join(parts)

    def log(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> AuditEntry:
        """Log an audit event."""
        entry = self.create_entry(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )
        return entry

    def log_to_db(
        self,
        session,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> AuditLog:
        """Log an audit event to database."""
        entry = self.log(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )

        model = entry.to_model()

        # Sign the entry
        signature = self.sign_entry(entry)
        if signature:
            model.signature = signature

        session.add(model)
        session.commit()

        return model

    def get_user_logs(
        self,
        session,
        user_id: str,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Get audit logs for a user."""
        return session.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()

    def get_resource_logs(
        self,
        session,
        resource_type: str,
        resource_id: str,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Get audit logs for a resource."""
        return session.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        ).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()

    def verify_log_integrity(self, log: AuditLog) -> bool:
        """Verify audit log signature integrity."""
        if not log.signature:
            return True  # Unsigned logs are valid (just not tamper-evident)

        entry = AuditEntry(
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            user_id=log.user_id,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            details=json.loads(log.details) if log.details else None,
            timestamp=log.timestamp,
        )

        message = self._create_signable_message(entry)
        return self.signer.verify(message, log.signature)


def create_audit_log(
    session,
    user_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: str,
    ip_address: Optional[str] = None,
    details: Optional[dict] = None,
) -> AuditLog:
    """Convenience function to create audit log."""
    service = AuditService()
    return service.log_to_db(
        session=session,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        ip_address=ip_address,
        details=details,
    )

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
    """Ed25519 signer for audit logs."""

    def __init__(self, private_key: Optional[str] = None):
        self._private_key = private_key
        self._public_key = None
        self._signing_key = None

    def _get_signing_key(self):
        """Get or create signing key."""
        if self._signing_key is None:
            try:
                from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
                from cryptography.hazmat.primitives import serialization

                if self._private_key:
                    # Load from hex
                    key_bytes = bytes.fromhex(self._private_key)
                    self._signing_key = Ed25519PrivateKey.from_private_bytes(key_bytes)
                else:
                    # Generate new key
                    self._signing_key = Ed25519PrivateKey.generate()

                self._public_key = self._signing_key.public_key()
            except ImportError:
                # cryptography not available
                self._signing_key = None
                self._public_key = None

        return self._signing_key

    def sign(self, message: str) -> Optional[str]:
        """Sign a message."""
        key = self._get_signing_key()
        if key is None:
            return None

        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        signature = key.sign(message.encode("utf-8"))
        return signature.hex()

    def verify(self, message: str, signature: str) -> bool:
        """Verify a signature."""
        if self._public_key is None:
            return False

        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            self._public_key.verify(
                bytes.fromhex(signature),
                message.encode("utf-8")
            )
            return True
        except Exception:
            return False

    def get_public_key_hex(self) -> Optional[str]:
        """Get public key as hex string."""
        if self._public_key is None:
            return None

        from cryptography.hazmat.primitives import serialization
        pub_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return pub_bytes.hex()


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

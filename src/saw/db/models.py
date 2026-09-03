"""SQLAlchemy models for team deployment.

Phase 5: Team Deployment — Database models.
Per TEAM-02~08: Users, Vaults, Permissions, Audit Logs.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Float,
    Integer,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from saw.domain.utils import utcnow  # noqa: F401


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="viewer", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    vaults: Mapped[List["Vault"]] = relationship("Vault", back_populates="owner")
    permissions: Mapped[List["VaultPermission"]] = relationship(
        "VaultPermission",
        back_populates="user",
        foreign_keys="VaultPermission.user_id"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Vault(Base):
    """Vault model for knowledge storage."""
    __tablename__ = "vaults"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="vaults")
    claims: Mapped[List["Claim"]] = relationship("Claim", back_populates="vault")
    permissions: Mapped[List["VaultPermission"]] = relationship(
        "VaultPermission", back_populates="vault"
    )

    def __repr__(self) -> str:
        return f"<Vault {self.name}>"


class Claim(Base):
    """Claim model for knowledge assertions."""
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    vault_id: Mapped[str] = mapped_column(String, ForeignKey("vaults.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_uuid: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, default=1)
    source_mark: Mapped[int] = mapped_column(Integer, default=1)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    entities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    # Media timestamp fields (Phase 4)
    media_timestamp_start: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    media_timestamp_end: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    media_vault_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    vault: Mapped["Vault"] = relationship("Vault", back_populates="claims")

    # Indexes
    __table_args__ = (
        Index("ix_claims_vault_created", "vault_id", "created_at"),
        Index("ix_claims_content_hash", "content_hash"),
    )


class VaultPermission(Base):
    """Vault permission model for access control."""
    __tablename__ = "vault_permissions"

    vault_id: Mapped[str] = mapped_column(
        String, ForeignKey("vaults.id"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), primary_key=True
    )
    permission: Mapped[str] = mapped_column(String(50), default="read")  # read, write, admin
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    granted_by: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"), nullable=True)

    # Relationships (specify foreign_keys to resolve ambiguity)
    vault: Mapped["Vault"] = relationship("Vault", back_populates="permissions")
    user: Mapped["User"] = relationship(
        "User",
        back_populates="permissions",
        foreign_keys=[user_id]
    )

    def __repr__(self) -> str:
        return f"<VaultPermission vault={self.vault_id} user={self.user_id} perm={self.permission}>"


class AuditLog(Base):
    """Audit log model for operation tracking."""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # create, read, update, delete
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # vault, claim, user
    resource_id: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON details
    signature: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # Ed25519 signature

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    # Indexes
    __table_args__ = (
        Index("ix_audit_logs_user_timestamp", "user_id", "timestamp"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.resource_type}:{self.resource_id}>"


class RefreshToken(Base):
    """Refresh token model for JWT authentication."""
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class SystemConfig(Base):
    """System configuration model."""
    __tablename__ = "system_config"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


def init_db(engine):
    """Initialize database tables."""
    Base.metadata.create_all(engine)


def drop_db(engine):
    """Drop all database tables."""
    Base.metadata.drop_all(engine)

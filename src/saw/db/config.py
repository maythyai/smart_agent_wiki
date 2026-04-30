"""Database layer for Smart Agent Wiki.

Phase 5: Team Deployment — PostgreSQL support.
Per TEAM-02: PostgreSQL database support.

Supports both SQLite (development) and PostgreSQL (production).
Uses SQLAlchemy 2.0 async API for PostgreSQL.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = "sqlite:///saw.db"
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """Create config from environment variables."""
        url = os.environ.get("DATABASE_URL", "sqlite:///saw.db")
        pool_size = int(os.environ.get("DB_POOL_SIZE", "5"))
        max_overflow = int(os.environ.get("DB_MAX_OVERFLOW", "10"))
        echo = os.environ.get("DB_ECHO", "false").lower() == "true"
        return cls(url=url, pool_size=pool_size, max_overflow=max_overflow, echo=echo)

    @property
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL."""
        return self.url.startswith("postgresql")

    @property
    def async_url(self) -> str:
        """Get async-compatible URL."""
        if self.is_postgres:
            # Replace postgresql:// with postgresql+asyncpg://
            return self.url.replace("postgresql://", "postgresql+asyncpg://")
        return self.url


def get_engine(config: DatabaseConfig | None = None):
    """Get SQLAlchemy engine based on config."""
    config = config or DatabaseConfig.from_env()

    from sqlalchemy import create_engine
    from sqlalchemy.ext.asyncio import create_async_engine

    if config.is_postgres:
        return create_async_engine(
            config.async_url,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            echo=config.echo,
        )
    else:
        return create_engine(config.url, echo=config.echo)


def get_async_engine(config: DatabaseConfig | None = None):
    """Get async SQLAlchemy engine."""
    config = config or DatabaseConfig.from_env()

    from sqlalchemy.ext.asyncio import create_async_engine

    if config.is_postgres:
        return create_async_engine(
            config.async_url,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            echo=config.echo,
        )
    else:
        # SQLite async requires aiosqlite
        async_url = config.url.replace("sqlite:///", "sqlite+aiosqlite:///")
        return create_async_engine(async_url, echo=config.echo)


# Session factories
def get_session_factory(engine):
    """Get session factory for engine."""
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    if hasattr(engine, "sync_engine"):
        # Async engine
        return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    else:
        # Sync engine
        return sessionmaker(engine, expire_on_commit=False)
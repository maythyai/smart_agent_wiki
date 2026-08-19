"""Async session dependency for connector / team-deployment endpoints.

Several API routers (``saw.api.integrations``, ``saw.api.connector_settings``)
import ``get_session`` from here as a FastAPI dependency. Previously this
module did not exist, so those endpoints raised ``ImportError`` at call time
and never worked in local ``saw web`` mode.

``get_session()`` is an async context manager yielding an ``AsyncSession``
backed by the configured async engine (SQLite via aiosqlite by default,
PostgreSQL via asyncpg in team mode). On first use it lazily creates the
shared SQLAlchemy metadata (users, connectors, sync state, feeds, …) so the
connector dashboard and settings endpoints work out of the box without a
manual migration step.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from saw.db.config import DatabaseConfig, get_async_engine

logger = logging.getLogger(__name__)

# Module-level singletons so repeated endpoint calls reuse one engine.
_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_schema_initialized = False


def _get_engine():
    """Return the lazily-created async engine singleton."""
    global _engine
    if _engine is None:
        _engine = get_async_engine(DatabaseConfig.from_env())
    return _engine


def _get_factory() -> async_sessionmaker[AsyncSession]:
    """Return the lazily-created async session factory singleton."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def _ensure_schema() -> None:
    """Create all connector/team tables on the shared Base if missing.

    Importing ``saw.db`` registers every model on the shared ``Base``; we
    then run ``create_all`` inside a transaction. Safe to call repeatedly —
    ``create_all`` is idempotent.
    """
    global _schema_initialized
    if _schema_initialized:
        return

    # Importing the package registers every ORM model that __init__
    # re-exports on the shared Base. Some models (e.g. connector_settings)
    # are not re-exported by __init__, so import their modules explicitly
    # to guarantee every table is registered before create_all runs.
    import saw.db  # noqa: F401
    from saw.db import (  # noqa: F401
        connector_settings,
        connector_models,
        feed_models,
        sync_models,
        notion_models,
        logseq_models,
        github_models,
    )
    from saw.db.models import Base

    engine = _get_engine()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _schema_initialized = True
        logger.debug("Connector/team schema initialized on %s", engine.url)
    except Exception as e:  # pragma: no cover — best-effort bootstrap
        # Non-fatal: leave _schema_initialized=False so we retry next call.
        logger.warning("Schema bootstrap failed (will retry on next call): %s", e)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an ``AsyncSession``, ensuring schema exists on first call.

    Usage as a FastAPI dependency::

        async def endpoint(session: AsyncSession = Depends(get_db_session)):
            ...

    where ``get_db_session`` is::

        async def get_db_session():
            async with get_session() as session:
                yield session
    """
    await _ensure_schema()
    factory = _get_factory()
    async with factory() as session:
        yield session


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding an ``AsyncSession``.

    Use this directly as ``Depends(get_db_session)`` in routers — it is an
    async generator (not a context manager), which is what FastAPI's
    dependency resolver expects for a yield-style dependency.
    """
    async with get_session() as session:
        yield session


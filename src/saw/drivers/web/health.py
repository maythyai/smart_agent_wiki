"""Health check endpoints for team deployment.

Phase 5: Team Deployment — Health checks.
Per TEAM-10: Health check endpoints.

Provides Kubernetes-compatible health probes.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request, Response


router = APIRouter(tags=["health"])


def _saw_version() -> str:
    """M-18: version from package metadata (single source of truth)."""
    try:
        from importlib.metadata import version as _pkg_version

        return _pkg_version("smart-agent-wiki")
    except Exception:  # pragma: no cover
        return "0.0.0"


_db_engine = None  # cached SQLAlchemy engine for /health/ready (M-10)


def check_database() -> dict[str, Any]:
    """Check database connectivity (M-10: reuse a cached pooled engine)."""
    global _db_engine
    if _db_engine is None:
        try:
            from sqlalchemy import create_engine
            from saw.db.config import DatabaseConfig

            _db_engine = create_engine(
                DatabaseConfig.from_env().url, pool_pre_ping=True
            )
        except Exception:
            _db_engine = False  # mark unavailable so we don't retry every probe
    if _db_engine is False:
        return {"status": "unhealthy", "error": "engine unavailable"}
    try:
        from sqlalchemy import text

        with _db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def check_redis() -> dict[str, Any]:
    """Check Redis connectivity."""
    import os

    redis_url = os.environ.get("REDIS_URL", "")

    if not redis_url:
        return {"status": "skipped", "reason": "Redis not configured"}

    try:
        import redis
        client = redis.from_url(redis_url)
        client.ping()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@router.get("/health")
async def health_check():
    """Basic health check.

    Returns 200 if the application is running.
    Used by load balancers and Docker health checks.
    """
    return {
        "status": "healthy",
        "version": _saw_version(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe.

    Returns 200 if the process is alive.
    If this fails, Kubernetes will restart the container.
    """
    return {"status": "alive"}


def check_engines(state: Any) -> dict[str, Any]:
    """Check that core engines are initialized (SPEC-F-D-3: AC-OBS-2).

    ``/health/ready`` must reflect engine readiness, not just DB/Redis — a
    deployed process whose engines failed to construct would otherwise still
    answer 200.  We probe the query, collaborate, and write_queue engines on
    ``app.state``; any missing → unhealthy → 503.  Deep engine health probes
    (most engines expose no ``health()`` method) are deferred to a later wave.
    """
    details: dict[str, str] = {}
    all_ready = True
    for name in ("query", "collaborate", "write_queue"):
        engine = getattr(state, name, None)
        details[name] = "ready" if engine is not None else "missing"
        if engine is None:
            all_ready = False
    return {
        "status": "healthy" if all_ready else "unhealthy",
        "details": details,
    }


@router.get("/health/ready")
async def readiness_check(request: Request, response: Response):
    """Kubernetes readiness probe.

    Checks if the application is ready to serve traffic.
    Verifies database, Redis, and core engine readiness (SPEC-F-D-3: AC-OBS-2).
    """
    checks = {
        "database": await asyncio.to_thread(check_database),
        "redis": await asyncio.to_thread(check_redis),
        "engines": check_engines(request.app.state),
    }

    # Determine overall status
    all_healthy = all(
        c.get("status") in ("healthy", "skipped")
        for c in checks.values()
    )

    if not all_healthy:
        response.status_code = 503

    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _compute_metrics(state: Any) -> dict:
    """Sync metrics computation (M-9: offloaded to a threadpool).

    Path.rglob + repo.count + wq.get_pending are all blocking sync calls;
    running them in the event loop stalled the server under /metrics scrapes.
    """
    from pathlib import Path

    claims_total = 0
    try:
        engine = getattr(state, "query", None)
        repo = (
            getattr(engine, "_claims_repo", None) or getattr(engine, "claims_repo", None)
            if engine is not None else None
        )
        if repo is not None:
            claims_total = int(repo.count())
    except Exception:
        claims_total = 0

    pages_total = 0
    try:
        pages_total = sum(1 for _ in Path(".").rglob("*.md"))
    except Exception:
        pass

    users_total = 0
    try:
        from saw.auth.user_store import get_user_store

        store = get_user_store()
        if hasattr(store, "_users"):
            users_total = len(getattr(store, "_users", {}) or {})
        elif hasattr(store, "count"):
            try:
                users_total = int(store.count())  # type: ignore[attr-defined]
            except Exception:
                users_total = 0
    except Exception:
        users_total = 0

    outbox_pending = 0
    outbox_dead = 0
    try:
        wq = getattr(state, "write_queue", None)
        if wq is not None:
            outbox_pending = len(wq.get_pending() or [])
            outbox_dead = len(wq.get_dead_letter() or [])
    except Exception:
        pass

    return {
        "claims_total": claims_total,
        "pages_total": pages_total,
        "users_total": users_total,
        "outbox_pending": outbox_pending,
        "outbox_dead": outbox_dead,
    }


@router.get("/metrics")
async def metrics(request: Request):
    """Prometheus metrics endpoint (text exposition format, HI-17; M-9).

    Returns real counts in Prometheus 0.0.4 text format. All computation is
    offloaded to a threadpool so sync rglob/SQLite calls don't block the loop.
    """
    import asyncio

    from fastapi.responses import PlainTextResponse

    # M-18: version derived from pyproject.toml (was hardcoded "2.0.0").
    try:
        from importlib.metadata import version as _pkg_version

        saw_version = _pkg_version("smart-agent-wiki")
    except Exception:  # pragma: no cover
        saw_version = "0.0.0"

    m = await asyncio.to_thread(_compute_metrics, request.app.state)

    lines = [
        "# HELP saw_users_total Total registered users.",
        "# TYPE saw_users_total gauge",
        f"saw_users_total {m['users_total']}",
        "# HELP saw_pages_total Total wiki markdown pages.",
        "# TYPE saw_pages_total gauge",
        f"saw_pages_total {m['pages_total']}",
        "# HELP saw_claims_total Total claims in the knowledge base.",
        "# TYPE saw_claims_total gauge",
        f"saw_claims_total {m['claims_total']}",
        "# HELP saw_write_outbox_pending Pending write-queue operations.",
        "# TYPE saw_write_outbox_pending gauge",
        f"saw_write_outbox_pending {m['outbox_pending']}",
        "# HELP saw_write_outbox_dead_letter Dead-lettered write-queue operations.",
        "# TYPE saw_write_outbox_dead_letter gauge",
        f"saw_write_outbox_dead_letter {m['outbox_dead']}",
        "",
    ]
    return PlainTextResponse(
        "\n".join(lines), media_type="text/plain; version=0.0.4; charset=utf-8"
    )

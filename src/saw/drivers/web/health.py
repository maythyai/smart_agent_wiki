"""Health check endpoints for team deployment.

Phase 5: Team Deployment — Health checks.
Per TEAM-10: Health check endpoints.

Provides Kubernetes-compatible health probes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request, Response


router = APIRouter(tags=["health"])


def check_database() -> dict[str, Any]:
    """Check database connectivity."""
    import os

    # Try to import and check database
    try:
        from sqlalchemy import create_engine, text
        from saw.db.config import DatabaseConfig

        config = DatabaseConfig.from_env()
        engine = create_engine(config.url)

        with engine.connect() as conn:
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
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe.

    Returns 200 if the process is alive.
    If this fails, Kubernetes will restart the container.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_check(response: Response):
    """Kubernetes readiness probe.

    Checks if the application is ready to serve traffic.
    Verifies database and Redis connectivity.
    """
    checks = {
        "database": check_database(),
        "redis": check_redis(),
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


@router.get("/metrics")
async def metrics(request: Request):
    """Prometheus-compatible metrics endpoint.

    Returns real counts: registered users, wiki pages, and claims. Each is
    best-effort — a missing component yields 0 rather than a 500.
    """
    from pathlib import Path

    saw_version = "2.0.0"

    # Claims total via the query engine's claims repo.
    claims_total = 0
    try:
        engine = getattr(request.app.state, "query", None)
        repo = (
            getattr(engine, "_claims_repo", None) or getattr(engine, "claims_repo", None)
            if engine is not None else None
        )
        if repo is not None:
            claims_total = int(repo.count())
    except Exception:
        claims_total = 0

    # Pages: count markdown files under the wiki root (cwd), matching the
    # dashboard-stats pattern.
    pages_total = 0
    try:
        pages_total = sum(1 for _ in Path(".").rglob("*.md"))
    except Exception:
        pass

    # Users: best-effort count. SQLAlchemyUserStore exposes a session factory;
    # InMemoryUserStore exposes ._users.
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

    return {
        "saw_users_total": users_total,
        "saw_pages_total": pages_total,
        "saw_claims_total": claims_total,
        "saw_version": saw_version,
    }

"""Health check endpoints for team deployment.

Phase 5: Team Deployment — Health checks.
Per TEAM-10: Health check endpoints.

Provides Kubernetes-compatible health probes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Response


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
async def metrics():
    """Prometheus-compatible metrics endpoint.

    Returns basic application metrics.
    """
    # In production, this would query the database for actual counts
    return {
        "saw_users_total": 0,
        "saw_vaults_total": 0,
        "saw_claims_total": 0,
        "saw_version": "2.0.0",
    }

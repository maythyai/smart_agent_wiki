"""Admin API endpoints — T-F-J-4 (AC-SEC-6).

POST /api/admin/policy/reload — hot-reload the Cedar policy file without a
restart. Admin-only (require_role("admin")). Mirrors the v1.5.0
``saw policy reload`` CLI for the Web surface (retro I4).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/policy/reload")
def reload_policy(request: Request) -> dict:
    """Hot-reload the Cedar policy (AC-SEC-6). Admin-only.

    Protection (get_current_user + require_role("admin")) is attached at the
    ``include_router`` call site in ``app.py`` so the security-matrix gate
    sees the auth_dep. Returns 404 when no Cedar policy is configured (RBAC
    still enforced by the in-process default); 200 with the backend otherwise.
    """
    cedar = getattr(request.app.state, "cedar", None)
    if cedar is None:
        raise HTTPException(
            status_code=404,
            detail="No Cedar policy engine configured (RBAC default still active).",
        )
    available = cedar.reload()
    backend = "cedar-python" if available else "Cedar CLI (hot per-call)"
    return {"reloaded": True, "backend": backend}

"""Per-request workspace contextvar injection (ADR-018, SPEC-F-W-1).

Adds ``X-Workspace-Id`` header / ``workspace_id`` query param support so a
single SAW server can scope queries/ingests/graph reads per request without
re-instantiating ``QueryEngine``. Additive, backward-compatible: absent
header/query leaves the contextvar unset and ``QueryEngine`` falls back to
its instance-level ``_workspace_id`` (matching v1.17.0 behaviour).
"""
from __future__ import annotations

import contextvars
import logging
import re

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# Per-request workspace scope. Default ``None`` (unset) signals "use the
# QueryEngine instance's ``_workspace_id``". Web requests set this to the
# value of ``X-Workspace-Id`` header / ``workspace_id`` query param.
# See ADR-018.
workspace_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "workspace_id", default=None
)


def get_current_workspace_id() -> str | None:
    """Return the per-request workspace id, or ``None`` if not in a request
    context (CLI, scripts, tests without middleware).

    Callers typically fall back to their engine's ``_workspace_id`` when
    this returns ``None``.
    """
    return workspace_id_var.get()


_WS_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


class WorkspaceContextMiddleware(BaseHTTPMiddleware):
    """Extract ``X-Workspace-Id`` header (or ``workspace_id`` query param)
    and set the per-request ``workspace_id_var`` contextvar.

    Priority: header > query param > ``None`` (unset, engine fallback).
    Invalid values → 400 ``INVALID_WORKSPACE_ID``.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        ws = request.headers.get("x-workspace-id") or request.query_params.get(
            "workspace_id"
        )
        if ws is not None and not _WS_RE.match(ws):
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "INVALID_WORKSPACE_ID",
                        "message": (
                            "workspace_id must be alphanumeric, hyphen or "
                            "underscore, max 64 chars"
                        ),
                    }
                },
            )
        token = workspace_id_var.set(ws)  # None if absent
        try:
            return await call_next(request)
        finally:
            workspace_id_var.reset(token)

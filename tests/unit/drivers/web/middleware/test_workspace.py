"""ADR-018: WorkspaceContextMiddleware + QueryEngine.effective_workspace_id.

Covers SPEC-F-W-1 AC-W-1..W-5: header injection, query param fallback,
validation (400), absent (None fallback), and engine contextvar precedence.
"""
from __future__ import annotations

import json

import pytest
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from saw.drivers.web.middleware.workspace import (
    WorkspaceContextMiddleware,
    get_current_workspace_id,
    workspace_id_var,
)


def _make_request(
    *, headers: dict | None = None, query_string: bytes = b""
) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [
            (k.lower().encode(), v.encode()) for k, v in (headers or {}).items()
        ],
        "query_string": query_string,
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_middleware_sets_contextvar_from_header():
    """AC-W-1: ``X-Workspace-Id`` header populates contextvar."""
    captured: dict = {}

    async def capture(scope):
        captured["ws"] = get_current_workspace_id()
        return PlainTextResponse("ok")

    middleware = WorkspaceContextMiddleware(app=capture)
    req = _make_request(headers={"x-workspace-id": "team-alpha"})
    await middleware.dispatch(req, capture)
    assert captured["ws"] == "team-alpha"


@pytest.mark.asyncio
async def test_middleware_query_param_fallback():
    """AC-W-2: ``workspace_id`` query param when header absent."""
    captured: dict = {}

    async def capture(scope):
        captured["ws"] = get_current_workspace_id()
        return PlainTextResponse("ok")

    middleware = WorkspaceContextMiddleware(app=capture)
    req = _make_request(query_string=b"workspace_id=team-beta")
    await middleware.dispatch(req, capture)
    assert captured["ws"] == "team-beta"


@pytest.mark.asyncio
async def test_middleware_header_overrides_query():
    """AC-W-2: header takes priority over query param."""
    captured: dict = {}

    async def capture(scope):
        captured["ws"] = get_current_workspace_id()
        return PlainTextResponse("ok")

    middleware = WorkspaceContextMiddleware(app=capture)
    req = _make_request(
        headers={"x-workspace-id": "from-header"},
        query_string=b"workspace_id=from-query",
    )
    await middleware.dispatch(req, capture)
    assert captured["ws"] == "from-header"


@pytest.mark.asyncio
async def test_middleware_absent_leaves_unset():
    """AC-W-4: no header/query → contextvar stays ``None`` (engine fallback)."""
    captured: dict = {}

    async def capture(scope):
        captured["ws"] = get_current_workspace_id()
        return PlainTextResponse("ok")

    middleware = WorkspaceContextMiddleware(app=capture)
    req = _make_request()
    await middleware.dispatch(req, capture)
    assert captured["ws"] is None


@pytest.mark.asyncio
async def test_middleware_invalid_workspace_returns_400():
    """AC-W-3: illegal chars / over-length → 400 INVALID_WORKSPACE_ID."""

    async def unreachable(scope):  # pragma: no cover — must not be called
        raise AssertionError("call_next must not run on invalid workspace_id")

    middleware = WorkspaceContextMiddleware(app=unreachable)

    # Invalid chars
    req = _make_request(headers={"x-workspace-id": "bad workspace!"})
    resp = await middleware.dispatch(req, unreachable)
    assert resp.status_code == 400
    body = json.loads(resp.body)
    assert body["error"]["code"] == "INVALID_WORKSPACE_ID"

    # Over length (65 chars)
    req = _make_request(headers={"x-workspace-id": "a" * 65})
    resp = await middleware.dispatch(req, unreachable)
    assert resp.status_code == 400
    body = json.loads(resp.body)
    assert body["error"]["code"] == "INVALID_WORKSPACE_ID"


def _make_engine(workspace_id: str = "default"):
    """Build a QueryEngine with all mocked deps (minimal fixture)."""
    from unittest.mock import MagicMock

    from saw.engines.query.engine import QueryEngine

    return QueryEngine(
        search=MagicMock(),
        compiler=MagicMock(),
        graph=MagicMock(),
        compare_engine=MagicMock(),
        tree_mode=MagicMock(),
        llm=None,
        claims_repo=MagicMock(),
        wiki_repo=MagicMock(),
        conn=MagicMock(),
        workspace_id=workspace_id,
    )


def test_engine_effective_workspace_fallback_no_contextvar():
    """AC-W-5: engine uses ``_workspace_id`` when contextvar unset."""
    token = workspace_id_var.set(None)
    try:
        engine = _make_engine(workspace_id="cli-scope")
        assert engine.effective_workspace_id == "cli-scope"
    finally:
        workspace_id_var.reset(token)


def test_engine_effective_workspace_reads_contextvar():
    """AC-W-5: engine prefers contextvar when set by middleware."""
    token = workspace_id_var.set("web-scope")
    try:
        engine = _make_engine(workspace_id="cli-scope")
        assert engine.effective_workspace_id == "web-scope"
    finally:
        workspace_id_var.reset(token)


def test_engine_effective_workspace_default_when_contextvar_unset():
    """AC-W-5: engine falls back to its configured default ``'default'``."""
    token = workspace_id_var.set(None)
    try:
        engine = _make_engine()  # default workspace_id="default"
        assert engine.effective_workspace_id == "default"
    finally:
        workspace_id_var.reset(token)

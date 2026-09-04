"""Agents REST endpoint test — T-F-M-3 (AC-API-1)."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_get_agents_returns_roster():
    """AC-API-1: GET /api/v1/agents returns the 6-role roster JSON."""
    from saw.api.routes.collaborate import router

    app = FastAPI()
    app.include_router(router)
    res = TestClient(app).get("/api/v1/agents")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 6
    names = {a["name"] for a in data["agents"]}
    assert {"Librarian", "Writer", "Critic", "Linker", "Scholar", "Guardian"} <= names
    guardian = next(a for a in data["agents"] if a["name"] == "Guardian")
    assert guardian["rule"] is True
    assert guardian["model_tier"] == "rule"

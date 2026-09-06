"""Agents REST endpoint test — T-F-M-3 (AC-API-1), F-T-1 (AC-A-4)."""
from __future__ import annotations

import os
from pathlib import Path

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
    # F-T-1: every built-in agent has custom=False
    for a in data["agents"]:
        assert a["custom"] is False


def test_ac_a_4_custom_agent_in_rest_response(tmp_path: Path):
    """AC-A-4: register MedicalExpert → GET /api/v1/agents → custom: true."""
    agents_dir = tmp_path / ".saw" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "expert.yaml").write_text(
        "name: MedicalExpert\n"
        "model_tier: sonnet\n"
        "system_prompt: Medical expert.\n"
        "tools_allowed: [search, read]\n",
        encoding="utf-8",
    )

    from saw.api.routes.collaborate import router

    app = FastAPI()
    app.include_router(router)

    prev = os.getcwd()
    os.chdir(tmp_path)
    try:
        res = TestClient(app).get("/api/v1/agents")
    finally:
        os.chdir(prev)

    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 7  # 6 built-in + 1 custom
    medical = next(a for a in data["agents"] if a["name"] == "MedicalExpert")
    assert medical["model_tier"] == "sonnet"
    assert medical["custom"] is True
    assert medical["tools_allowed"] == ["search", "read"]

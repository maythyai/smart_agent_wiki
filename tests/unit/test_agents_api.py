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


# ── F-T-3: agent activity REST endpoint ────────────────────────────

def test_ac_c_3_activity_404_for_unknown_agent():
    """AC-C-3: GET /api/v1/agents/NonExistent/activity → 404."""
    from saw.api.routes.collaborate import router

    app = FastAPI()
    app.include_router(router)
    res = TestClient(app).get("/api/v1/agents/NonExistent/activity")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_ac_c_3_activity_200_empty_for_known_agent():
    """AC-C-3: GET /api/v1/agents/Guardian/activity → 200 + empty activity
    (no tracker set up in test → calls=0)."""
    from saw.api.routes.collaborate import router

    app = FastAPI()
    app.include_router(router)
    res = TestClient(app).get("/api/v1/agents/Guardian/activity")
    assert res.status_code == 200
    data = res.json()
    assert data["agent"] == "Guardian"
    assert data["calls"] == 0
    assert data["failures"] == 0
    assert data["last_action"] is None
    assert data["last_active_at"] is None


def test_ac_c_4_agents_endpoint_includes_activity_summary():
    """AC-C-4: publish 3 Scholar events → GET /api/v1/agents → Scholar row
    contains activity_summary {calls: 3, ...}."""
    from saw.api.routes.collaborate import router
    from saw.drivers.web import app as app_module
    from saw.engines.collaborate.activity_tracker import AgentActivityTracker

    # Set up a tracker with 3 Scholar events
    tracker = AgentActivityTracker()
    for _ in range(3):
        tracker._handle_event({
            "type": "WorkflowStep",
            "step": "Scholar.synthesize",
            "status": "completed",
        })
    app_module.set_activity_tracker(tracker)

    try:
        app = FastAPI()
        app.include_router(router)
        res = TestClient(app).get("/api/v1/agents")
        assert res.status_code == 200
        data = res.json()
        scholar = next(
            a for a in data["agents"] if a["name"] == "Scholar"
        )
        assert scholar["activity_summary"] is not None
        assert scholar["activity_summary"]["calls"] == 3
        assert scholar["activity_summary"]["last_active_at"] is not None
        # Guardian has no activity → activity_summary is None
        guardian = next(
            a for a in data["agents"] if a["name"] == "Guardian"
        )
        assert guardian["activity_summary"] is None
    finally:
        app_module.set_activity_tracker(None)


def test_ac_c_4_activity_endpoint_returns_aggregated_data():
    """AC-C-4 (variant): GET /api/v1/agents/Scholar/activity returns
    aggregated calls/failures/last_action/last_active_at."""
    from saw.api.routes.collaborate import router
    from saw.drivers.web import app as app_module
    from saw.engines.collaborate.activity_tracker import AgentActivityTracker

    tracker = AgentActivityTracker()
    tracker._handle_event({
        "type": "WorkflowStep",
        "step": "Scholar.synthesize",
        "status": "completed",
    })
    tracker._handle_event({
        "type": "WorkflowStep",
        "step": "Scholar.review",
        "status": "failed",
    })
    app_module.set_activity_tracker(tracker)

    try:
        app = FastAPI()
        app.include_router(router)
        res = TestClient(app).get("/api/v1/agents/Scholar/activity")
        assert res.status_code == 200
        data = res.json()
        assert data["agent"] == "Scholar"
        assert data["calls"] == 1
        assert data["failures"] == 1
        assert data["last_action"] == "review"
        assert data["last_active_at"] is not None
    finally:
        app_module.set_activity_tracker(None)

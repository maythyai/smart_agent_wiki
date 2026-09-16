"""Tests for A4 deep research + C5b webhook (v1.30.0)."""
from __future__ import annotations

from types import SimpleNamespace

import saw.drivers.mcp.tools.agent_tools as at


def test_saw_deep_research_returns_report(monkeypatch):
    """A4: deep research returns a synthesis report from claims."""
    search = SimpleNamespace(search=lambda q, limit=10: SimpleNamespace(
        claim_uuids=["c1"], contents=["Login uses Argon2"], scores=[0.9],
    ))
    qe = SimpleNamespace(
        _claims_repo=SimpleNamespace(get_by_id=lambda u: None),
        _search=search,
        query=lambda *a, **k: SimpleNamespace(sources=[]),
    )
    monkeypatch.setattr(at, "_query_engine", qe)
    monkeypatch.setattr(at, "_wiki_repo", None)
    monkeypatch.setattr(at, "_code_graph_engine", None)
    monkeypatch.setattr(at, "_write_queue", None)
    import asyncio
    res = asyncio.run(at.saw_deep_research(query="how does login work", limit=5))
    assert res["mode"] == "writer-template"
    assert len(res["claims"]) == 1
    assert "Argon2" in res["report"]


def test_saw_deep_research_no_results(monkeypatch):
    search = SimpleNamespace(search=lambda q, limit=10: SimpleNamespace(
        claim_uuids=[], contents=[], scores=[],
    ))
    qe = SimpleNamespace(_claims_repo=SimpleNamespace(get_by_id=lambda u: None), _search=search,
                         query=lambda *a, **k: SimpleNamespace(sources=[]))
    monkeypatch.setattr(at, "_query_engine", qe)
    import asyncio
    res = asyncio.run(at.saw_deep_research(query="nonexistent"))
    assert res["mode"] == "no-results"


def test_saw_deep_research_no_engine(monkeypatch):
    monkeypatch.setattr(at, "_query_engine", None)
    import asyncio
    res = asyncio.run(at.saw_deep_research(query="x"))
    assert res["error"] == "query_engine_not_initialized"


def test_webhook_research_endpoint():
    """C5b: POST /api/research returns answer + sources."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from saw.api.research import router

    app = FastAPI()
    app.state.query = SimpleNamespace(
        query=lambda q, depth=3, mode="auto": SimpleNamespace(
            answer="Login uses Argon2", sources=[{"claim_uuid": "c1"}],
            coverage=90.0, mode="search", meta={},
        )
    )
    app.include_router(router, prefix="/api")
    client = TestClient(app)
    res = client.post("/api/research", json={"query": "how does login work"})
    assert res.status_code == 200
    data = res.json()
    assert data["answer"] == "Login uses Argon2"
    assert len(data["sources"]) == 1


def test_webhook_query_compact():
    """C5b: POST /api/webhook/query returns compact answer + sources_count."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from saw.api.research import router

    app = FastAPI()
    app.state.query = SimpleNamespace(
        query=lambda q, depth=3, mode="auto": SimpleNamespace(
            answer="42", sources=[{"c": 1}, {"c": 2}], coverage=50.0, mode="search", meta={},
        )
    )
    app.include_router(router, prefix="/api")
    client = TestClient(app)
    res = client.post("/api/webhook/query", json={"query": "what is the answer"})
    assert res.status_code == 200
    data = res.json()
    assert data["answer"] == "42"
    assert data["sources_count"] == 2

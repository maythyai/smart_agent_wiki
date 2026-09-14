"""Tests for A3 DRIFT search (v1.25.0) + B3 claim status axis."""
from __future__ import annotations

from types import SimpleNamespace

import saw.drivers.mcp.tools.query as q
from saw.domain.value_objects import (
    ClaimStatus,
    ConfidenceLevel,
    ResolutionStrategy,
    derive_claim_status,
)


# ── B3 derive_claim_status ──────────────────────────────────────────

def test_status_true_high_confidence_not_contradicted():
    assert derive_claim_status(ConfidenceLevel.HUMAN_VERIFIED) == ClaimStatus.TRUE
    assert derive_claim_status(ConfidenceLevel.CROSS_VALIDATED) == ClaimStatus.TRUE


def test_status_suspected_low_confidence():
    assert derive_claim_status(ConfidenceLevel.UNVERIFIED) == ClaimStatus.SUSPECTED
    assert derive_claim_status(ConfidenceLevel.SINGLE_SOURCE) == ClaimStatus.SUSPECTED


def test_status_false_when_superseded():
    assert derive_claim_status(
        ConfidenceLevel.HUMAN_VERIFIED, contradicted=True, resolution=ResolutionStrategy.SUPERSEDED
    ) == ClaimStatus.FALSE


def test_status_suspected_when_disputed_or_historical():
    assert derive_claim_status(
        ConfidenceLevel.CROSS_VALIDATED, contradicted=True, resolution=ResolutionStrategy.DISPUTED
    ) == ClaimStatus.SUSPECTED
    assert derive_claim_status(
        ConfidenceLevel.HUMAN_VERIFIED, contradicted=True, resolution=ResolutionStrategy.HISTORICAL
    ) == ClaimStatus.SUSPECTED


def test_claim_status_property():
    from saw.domain.claims import Claim
    c = Claim(uuid="x", content="x", source_uuid="s", content_hash="h",
              confidence=ConfidenceLevel.HUMAN_VERIFIED)
    assert c.status == ClaimStatus.TRUE
    c2 = Claim(uuid="y", content="y", source_uuid="s", content_hash="h",
               confidence=ConfidenceLevel.UNVERIFIED)
    assert c2.status == ClaimStatus.SUSPECTED


# ── A3 saw_drift_search ─────────────────────────────────────────────

def _set_qe(claims=None, sources=None):
    """Build a mock query_engine returning `sources` from query(mode=semantic)."""
    claims_repo = SimpleNamespace(get_by_id=lambda uid: claims.get(uid))
    qr = SimpleNamespace(sources=sources or [])
    qe = SimpleNamespace(
        _claims_repo=claims_repo,
        _search=SimpleNamespace(search=lambda *a, **k: SimpleNamespace(claim_uuids=[], contents=[], scores=[])),
        query=lambda *a, **k: qr,
    )
    return qe


def test_drift_search_returns_claims_with_status(monkeypatch):
    """saw_drift_search primer returns claims each carrying B3 status."""
    claim = SimpleNamespace(
        uuid="c1", content="rate limit login", confidence=ConfidenceLevel.HUMAN_VERIFIED,
        status=ClaimStatus.TRUE, entities=["LoginRateLimit"],
    )
    qe = _set_qe(
        claims={"c1": claim},
        sources=[{"claim_uuid": "c1", "content": "rate limit login", "confidence": "human_verified", "score": 0.9}],
    )
    monkeypatch.setattr(q, "_query_engine", qe)
    monkeypatch.setattr(q, "_graph", None)
    import asyncio
    res = asyncio.run(q.saw_drift_search(query="rate limit", depth=2, limit=5))
    assert res["mode"] == "drift"
    assert len(res["claims"]) == 1
    assert res["claims"][0]["status"] == "true"
    assert res["claims"][0]["uuid"] == "c1"


def test_drift_search_broad_community(monkeypatch):
    """When the graph is available, drift surfaces the top entity's community."""
    claim = SimpleNamespace(uuid="c1", content="x", confidence=ConfidenceLevel.CROSS_VALIDATED,
                            status=ClaimStatus.TRUE, entities=["Alpha"])
    qe = _set_qe(
        claims={"c1": claim},
        sources=[{"claim_uuid": "c1", "content": "x", "confidence": "cross_validated", "score": 0.8}],
    )
    graph = SimpleNamespace(
        community_of=lambda e: {"entity": e, "id": 0, "size": 3, "members": ["Alpha","Bravo","Charlie"]},
        traverse=lambda *a, **k: SimpleNamespace(nodes=[], edges=[], paths=[]),
    )
    monkeypatch.setattr(q, "_query_engine", qe)
    monkeypatch.setattr(q, "_graph", graph)
    import asyncio
    res = asyncio.run(q.saw_drift_search(query="x"))
    assert res["broad"] is not None
    assert res["broad"]["entity"] == "Alpha"
    assert "Bravo" in res["broad"]["members"]


def test_drift_search_no_query_engine(monkeypatch):
    monkeypatch.setattr(q, "_query_engine", None)
    import asyncio
    res = asyncio.run(q.saw_drift_search(query="x"))
    assert res["error"] == "query_engine_not_initialized"

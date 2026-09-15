"""Tests for B4 NLP noun-phrase + B5 auto-feedback + D3 heartbeat (v1.26.0)."""
from __future__ import annotations

from types import SimpleNamespace

import saw.drivers.mcp.tools.govern as g
from saw.engines.ingest.nlp_index import extract_noun_phrases
from saw.engines.govern.heartbeat import HeartbeatScheduler
from saw.domain.value_objects import ConfidenceLevel


# ── B4 NLP noun-phrase ──────────────────────────────────────────────

def test_nlp_latin_filters_stopwords():
    kws = extract_noun_phrases("rate limiting protects the login endpoint", top_k=10)
    assert "rate" in kws or "limiting" in kws
    assert "the" not in kws
    assert "login" in kws or "endpoint" in kws


def test_nlp_cjk_extracts_nouns():
    kws = extract_noun_phrases("限流保护登录接口", top_k=10)
    assert any(k for k in kws if k)  # at least one CJK noun
    assert "限流" in kws


def test_nlp_empty_text():
    assert extract_noun_phrases("") == []
    assert extract_noun_phrases("   ") == []


def test_saw_nlp_keywords_tool():
    import asyncio
    res = asyncio.run(g.saw_nlp_keywords(text="rate limiting login", top_k=5))
    assert res["mode"] == "nlp-no-llm"
    assert res["count"] == len(res["keywords"])
    assert res["count"] > 0


# ── B5 auto-feedback ────────────────────────────────────────────────

def _mock_governor(claim):
    """Governor with a claims_repo capturing update_confidence calls."""
    updated = []
    repo = SimpleNamespace(
        get_by_id=lambda uid: claim if uid == claim.uuid else None,
        update_confidence=lambda uuid, conf: updated.append((uuid, conf)),
    )
    gov = SimpleNamespace(claims_repo=repo)
    return gov, updated


def test_feedback_helpful_bumps_confidence(monkeypatch):
    claim = SimpleNamespace(uuid="c1", confidence=ConfidenceLevel.SINGLE_SOURCE)
    gov, updated = _mock_governor(claim)
    monkeypatch.setattr(g, "_governor", gov)
    import asyncio
    res = asyncio.run(g.saw_record_feedback(claim_uuid="c1", helpful=True))
    assert res["recorded"] is True
    assert res["helpful"] is True
    # SINGLE_SOURCE (2) -> CROSS_VALIDATED (3)
    assert res["new_confidence"] == "cross_validated"
    assert updated == [("c1", "cross_validated")]


def test_feedback_not_helpful_lowers_confidence(monkeypatch):
    claim = SimpleNamespace(uuid="c2", confidence=ConfidenceLevel.CROSS_VALIDATED)
    gov, updated = _mock_governor(claim)
    monkeypatch.setattr(g, "_governor", gov)
    import asyncio
    res = asyncio.run(g.saw_record_feedback(claim_uuid="c2", helpful=False))
    assert res["recorded"] is True
    # CROSS_VALIDATED (3) -> SINGLE_SOURCE (2)
    assert res["new_confidence"] == "single_source"


def test_feedback_claim_not_found(monkeypatch):
    claim = SimpleNamespace(uuid="c1", confidence=ConfidenceLevel.UNVERIFIED)
    gov, _ = _mock_governor(claim)
    monkeypatch.setattr(g, "_governor", gov)
    import asyncio
    res = asyncio.run(g.saw_record_feedback(claim_uuid="nope", helpful=True))
    assert res["error"] == "claim_not_found"


def test_feedback_no_governor(monkeypatch):
    monkeypatch.setattr(g, "_governor", None)
    import asyncio
    res = asyncio.run(g.saw_record_feedback(claim_uuid="x", helpful=True))
    assert res["error"] == "governor_not_initialized"


# ── D3 heartbeat ────────────────────────────────────────────────────

def test_heartbeat_disabled_without_governor():
    hb = HeartbeatScheduler(governor=None, interval_seconds=300)
    assert hb.start() is False
    assert hb.last_run["status"] == "disabled"


def test_heartbeat_disabled_zero_interval():
    gov = SimpleNamespace(get_freshness_report=lambda: SimpleNamespace(stale_count=2))
    hb = HeartbeatScheduler(governor=gov, interval_seconds=0)
    assert hb.start() is False
    assert hb.last_run["status"] == "disabled"


def test_heartbeat_patrol_sets_last_run():
    gov = SimpleNamespace(get_freshness_report=lambda: SimpleNamespace(stale_count=3))
    det = SimpleNamespace(get_unresolved_contradictions=lambda: [1, 2])
    hb = HeartbeatScheduler(governor=gov, detector=det, interval_seconds=300)
    hb._patrol()  # one tick without the scheduler
    assert hb.last_run["status"] == "ok"
    assert hb.last_run["stale_count"] == 3
    assert hb.last_run["unresolved_contradictions"] == 2
    assert "ran_at" in hb.last_run


def test_saw_heartbeat_status_no_heartbeat(monkeypatch):
    monkeypatch.setattr(g, "_heartbeat", None)
    import asyncio
    res = asyncio.run(g.saw_heartbeat_status())
    assert res["status"] == "disabled"


def test_saw_heartbeat_status_with_heartbeat(monkeypatch):
    hb = HeartbeatScheduler(governor=SimpleNamespace(get_freshness_report=lambda: None),
                            detector=None, interval_seconds=0)
    hb._patrol()
    monkeypatch.setattr(g, "_heartbeat", hb)
    import asyncio
    res = asyncio.run(g.saw_heartbeat_status())
    assert res["status"] == "ok"

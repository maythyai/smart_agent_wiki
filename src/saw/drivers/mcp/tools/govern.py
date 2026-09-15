"""MCP tools for governance operations.

Per 02-03 Task 2: Govern tools (7 tools: saw_lint, saw_conflicts, saw_verify,
saw_freshness, saw_review, saw_audit, saw_blast_radius).
"""
from __future__ import annotations

from typing import Any

from saw.drivers.mcp.server import mcp

# Global references (set during initialization)
_governor = None
_detector = None
_blast_radius = None
_audit = None


def init_govern_tools(
    governor,
    detector,
    blast_radius,
    audit,
) -> None:
    """Initialize govern tools with references.

    Args:
        governor: Governor instance.
        detector: ContradictionDetector instance.
        blast_radius: BlastRadiusAnalyzer instance.
        audit: AuditTrail instance.
    """
    global _governor, _detector, _blast_radius, _audit
    _governor = governor
    _detector = detector
    _blast_radius = blast_radius
    _audit = audit


@mcp.tool
async def saw_lint(full: bool = False) -> dict[str, Any]:
    """Run health check on the knowledge base.

    Args:
        full: Whether to run full lint (including deep checks).

    Returns:
        Health report with health_score, orphan_pages, broken_links, etc.
    """
    result = {
        "health_score": 0,
        "orphan_pages": 0,
        "broken_links": 0,
        "stale_claims": 0,
        "missing_metadata": 0,
        "contradictions": 0,
        "version": "1.0.0",
    }

    if _governor is None:
        result["error"] = "Governor not initialized"
        return result

    try:
        report = _governor.lint()
        result["health_score"] = report.health_score
        result["orphan_pages"] = len(report.orphan_pages)
        result["broken_links"] = len(report.broken_links)
        result["stale_claims"] = len(report.stale_claims)
        result["missing_metadata"] = len(report.missing_metadata)
        if _detector:
            contradictions = _detector.get_all_contradictions()
            result["contradictions"] = len(contradictions)
    except Exception as e:
        result["error"] = str(e)

    return result


@mcp.tool
async def saw_conflicts(unresolved_only: bool = False) -> list[dict]:
    """List detected contradictions.

    Args:
        unresolved_only: Whether to filter to unresolved conflicts only.

    Returns:
        List of contradictions with type and resolution status.
    """
    results = []

    if _detector is None:
        return [{"error": "Detector not initialized"}]

    try:
        contradictions = _detector.get_all_contradictions()
        for c in contradictions:
            if unresolved_only and c.resolved_at is not None:
                continue
            results.append({
                "uuid": c.uuid,
                "type": c.contradiction_type.name.lower() if c.contradiction_type else "unknown",
                "claim_a": c.claim_a_uuid,
                "claim_b": c.claim_b_uuid,
                # B1: 4-level confidence of both claims so an agent/reader
                # can judge how much to trust each side of the contradiction.
                "claim_a_confidence": getattr(c, "claim_a_confidence", "unverified"),
                "claim_b_confidence": getattr(c, "claim_b_confidence", "unverified"),
                "resolved": c.resolved_at is not None,
                "strategy": c.resolution.name.lower() if c.resolution else None,
                "receipt": getattr(c, "receipt", None),
                "version": "1.21.0",
            })
    except Exception as e:
        results = [{"error": str(e)}]

    return results


@mcp.tool
async def saw_verify(claim_uuid: str) -> dict[str, Any]:
    """Verify a specific claim's provenance.

    Args:
        claim_uuid: UUID of the claim to verify.

    Returns:
        Provenance chain with source details.
    """
    result = {
        "claim_uuid": claim_uuid,
        "verified": False,
        "provenance": None,
        "version": "1.0.0",
    }

    if _governor is None:
        result["error"] = "Governor not initialized"
        return result

    try:
        chain = _governor.verify_claim(claim_uuid)
        if chain:
            result["verified"] = True
            result["provenance"] = {
                "claim_content": chain.claim_content,
                "source_type": chain.source_type,
                "source_uuid": chain.source_uuid,
                "page_location": chain.page_location,
                "confidence": chain.confidence,
                "confidence_reason": chain.confidence_reason,
            }
    except Exception as e:
        result["error"] = str(e)

    return result


@mcp.tool
async def saw_freshness() -> dict[str, Any]:
    """Get freshness distribution report.

    Returns:
        Freshness distribution by level and color.
    """
    result = {
        "distribution": {},
        "color_summary": {},
        "version": "1.0.0",
    }

    if _governor is None:
        result["error"] = "Governor not initialized"
        return result

    try:
        report = _governor.get_freshness_report()
        result["distribution"] = {str(k): v for k, v in report.distribution.items()}
        result["color_summary"] = report.color_summary
    except Exception as e:
        result["error"] = str(e)

    return result


@mcp.tool
async def saw_review(claim_uuids: list[str]) -> dict[str, Any]:
    """Trigger human review workflow.

    Args:
        claim_uuids: List of claim UUIDs needing review.

    Returns:
        Review submission result.
    """
    result = {
        "submitted": 0,
        "claim_uuids": claim_uuids,
        "version": "1.0.0",
    }

    if _governor is None:
        result["error"] = "Governor not initialized"
        return result

    try:
        _governor.trigger_review(claim_uuids)
        result["submitted"] = len(claim_uuids)
    except Exception as e:
        result["error"] = str(e)

    return result


@mcp.tool
async def saw_audit(export_path: str | None = None) -> dict[str, Any]:
    """Verify Ed25519 receipt chain integrity.

    Args:
        export_path: Optional path to export receipt chain for offline verification.

    Returns:
        Audit summary with chain status.
    """
    result = {
        "chain_valid": False,
        "receipt_count": 0,
        "last_receipt": None,
        "exported": False,
        "version": "1.0.0",
    }

    if _audit is None:
        result["error"] = "Audit trail not initialized"
        return result

    try:
        summary = _audit.verify_chain()
        result["chain_valid"] = summary.is_valid
        result["receipt_count"] = summary.total_receipts
        result["last_receipt"] = summary.last_receipt_id

        if export_path:
            _audit.export_chain(export_path)
            result["exported"] = True
            result["export_path"] = export_path
    except Exception as e:
        result["error"] = str(e)

    return result


@mcp.tool
async def saw_blast_radius(claim_uuid: str) -> dict[str, Any]:
    """Analyze downstream impact before editing.

    Args:
        claim_uuid: UUID of the claim to analyze.

    Returns:
        Blast radius analysis with affected entities and risk score.
    """
    result = {
        "claim_uuid": claim_uuid,
        "affected_claims": [],
        "affected_pages": [],
        "affected_entities": [],
        "risk_score": 0,
        "recommendation": "unknown",
        "version": "1.0.0",
    }

    if _blast_radius is None:
        result["error"] = "Blast radius analyzer not initialized"
        return result

    try:
        report = _blast_radius.analyze(claim_uuid)
        result["affected_claims"] = [c.uuid for c in report.affected_claims]
        result["affected_pages"] = report.affected_pages
        result["affected_entities"] = [e.name for e in report.affected_entities]
        result["risk_score"] = report.risk_score
        result["recommendation"] = report.recommendation
    except Exception as e:
        result["error"] = str(e)

    return result

# ── D3 (v1.26.0): heartbeat proactive patrol ───────────────────────
_heartbeat = None


def init_heartbeat_tools(heartbeat) -> None:
    """Inject the HeartbeatScheduler instance (D3)."""
    global _heartbeat
    _heartbeat = heartbeat


@mcp.tool
async def saw_heartbeat_status() -> dict[str, Any]:
    """D3: report the last proactive patrol run (freshness + contradictions).

    The heartbeat (if started) periodically runs a freshness + unresolved-
    contradiction scan in the background (Letta-inspired proactive patrol),
    so stale claims and open contradictions surface without a user trigger.

    Returns:
        ``{status, ran_at, interval_seconds, stale_count,
        unresolved_contradictions}`` or ``{status: "disabled", reason}``.
    """
    if _heartbeat is None:
        return {"status": "disabled", "reason": "heartbeat not configured"}
    return _heartbeat.last_run or {"status": "not-yet-run"}


# ── B5 (v1.26.0): auto-feedback (Cognee-inspired) ───────────────────

@mcp.tool
async def saw_record_feedback(claim_uuid: str, helpful: bool) -> dict[str, Any]:
    """D3/B5: record per-turn feedback on a claim, adjusting its confidence.

    Cognee-inspired auto-feedback self-tuning: a user/agent signals whether a
    claim was useful, and the claim's 4-level confidence is bumped (helpful) or
    lowered (not helpful). This lets retrieval weighting drift toward claims
    the agent community found useful — without re-ingesting.

    Args:
        claim_uuid: UUID of the claim.
        helpful: True = useful (bump confidence toward HUMAN_VERIFIED);
            False = not useful (lower toward UNVERIFIED, mark for re-review).

    Returns:
        ``{recorded, claim_uuid, helpful, new_confidence, status}``.
    """
    if _governor is None:
        return {"error": "governor_not_initialized"}
    claims_repo = getattr(_governor, "claims_repo", None) or getattr(_governor, "_claims_repo", None)
    if claims_repo is None or not hasattr(claims_repo, "update_confidence"):
        return {"error": "claims_repo_not_available"}
    claim = claims_repo.get_by_id(claim_uuid)
    if claim is None:
        return {"error": "claim_not_found", "claim_uuid": claim_uuid}
    from saw.domain.value_objects import ConfidenceLevel, derive_claim_status
    levels = sorted(ConfidenceLevel, key=lambda c: int(c))
    cur = int(claim.confidence)
    if helpful:
        new = min(c for c in levels if int(c) > cur) if any(int(c) > cur for c in levels) else cur
    else:
        new = max(c for c in levels if int(c) < cur) if any(int(c) < cur for c in levels) else cur
    new_conf = new.name.lower()
    try:
        claims_repo.update_confidence(claim_uuid, new_conf)
    except Exception as e:
        return {"error": "update_failed", "message": str(e)}
    status = derive_claim_status(new).name.lower()
    return {"recorded": True, "claim_uuid": claim_uuid, "helpful": helpful,
            "new_confidence": new_conf, "status": status}


# ── B4 (v1.26.0): NLP noun-phrase cost-reduction tier ───────────────

@mcp.tool
async def saw_nlp_keywords(text: str, top_k: int = 20) -> dict[str, Any]:
    """B4: cheap NLP noun-phrase extraction (no LLM, no network).

    FastGraphRAG-inspired cost-reduction pre-index: extracts noun-phrase
    candidates (jieba for CJK, regex for Latin) so ingest can run a cheap first
    pass before the (expensive) LLM claim extraction, and degrade to NLP-only
    on OFFLINE tier. Pure-Python + jieba (a SAW dep for CJK FTS5).

    Args:
        text: Source text to extract noun-phrases from.
        top_k: Max phrases to return (1-100).

    Returns:
        ``{keywords: [...], count, mode: "nlp-no-llm"}``.
    """
    from saw.engines.ingest.nlp_index import extract_noun_phrases
    kws = extract_noun_phrases(text, top_k=top_k)
    return {"keywords": kws, "count": len(kws), "mode": "nlp-no-llm"}

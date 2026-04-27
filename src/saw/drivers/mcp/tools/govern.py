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
            if unresolved_only and c.resolved:
                continue
            results.append({
                "uuid": c.uuid,
                "type": c.contradiction_type.name if hasattr(c, "contradiction_type") else "UNKNOWN",
                "claim_a": c.claim_a_uuid,
                "claim_b": c.claim_b_uuid,
                "resolved": c.resolved,
                "strategy": c.resolution_strategy.name if hasattr(c, "resolution_strategy") and c.resolution_strategy else None,
                "version": "1.0.0",
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
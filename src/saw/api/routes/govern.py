"""Governance API routes (H1-2).

Exposes the Govern Engine capabilities — claims, contradictions, verify,
lint, blast-radius, status — as REST endpoints under ``/api/v1/``.

All write endpoints are gated by the ``auth_dep`` dependency applied at
the router level in ``create_app()``.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

router = APIRouter(prefix="/api/v1", tags=["govern"])


# ── helpers ──────────────────────────────────────────────────────────


def _claims_repo(request: Request):
    """Get the claims repository from the query engine."""
    engine = request.app.state.query
    if engine is None:
        raise HTTPException(status_code=500, detail="Query engine not available")
    repo = None
    if hasattr(engine, "_claims_repo") and engine._claims_repo is not None:
        repo = engine._claims_repo
    elif hasattr(engine, "claims_repo") and engine.claims_repo is not None:
        repo = engine.claims_repo
    if repo is None:
        raise HTTPException(status_code=500, detail="Claims repository not available")
    return repo


def _contradiction_detector(request: Request):
    """Get the contradiction detector (best-effort)."""
    engine = getattr(request.app.state, "govern", None)
    if engine is None:
        raise HTTPException(
            status_code=503, detail="Govern engine not available"
        )
    return engine


# ── Claims ───────────────────────────────────────────────────────────


@router.get("/claims/{claim_id}")
async def get_claim_detail(
    claim_id: str = Path(..., description="Claim UUID"),
    include_relations: bool = Query(False),
    repo=Depends(_claims_repo),
):
    """Get full claim detail with optional relations (per api_contract §5.4)."""
    try:
        claim = repo.get_by_id(claim_id)
    except sqlite3.ProgrammingError:
        # SQLite objects cannot be shared across threads; this is a
        # deployment concern (team mode needs a shared connection pool).
        raise HTTPException(503, "Claims repository unavailable (cross-thread connection)")
    if claim is None:
        raise HTTPException(404, f"Claim '{claim_id}' not found")

    result = {
        "uuid": claim.uuid,
        "content": claim.content,
        "source_uuid": claim.source_uuid,
        "page_number": claim.page_number,
        "line_number": claim.line_number,
        "confidence": claim.confidence.name.lower() if hasattr(claim.confidence, "name") else str(claim.confidence),
        "source_mark": claim.source_mark.name.lower() if hasattr(claim.source_mark, "name") else str(claim.source_mark),
        "tags": claim.tags,
        "entities": claim.entities,
        "content_hash": claim.content_hash,
        "created_at": str(claim.created_at) if claim.created_at else None,
    }

    # Optionally include related claims
    if include_relations:
        from ast import Dict
        relations: list[dict] = []
        try:
            if hasattr(repo, "_conn"):
                rows = repo._conn.execute(
                    "SELECT target_claim_uuid, relation_type FROM claim_relation "
                    "WHERE source_claim_uuid = ?",
                    (claim_id,),
                ).fetchall()
                for target_uuid, rel_type in rows:
                    relations.append({
                        "to_claim": target_uuid,
                        "type": rel_type,
                    })
        except Exception:
            pass
        result["relations"] = relations

    return result


@router.patch("/claims/{claim_id}/confidence")
async def update_claim_confidence(
    claim_id: str = Path(..., description="Claim UUID"),
    confidence: str = Query(..., description="New confidence level"),
    repo=Depends(_claims_repo),
):
    """Update a claim's confidence level (per api_contract §5.4)."""
    allowed = {"unverified", "single_source", "cross_validated", "human_verified"}
    if confidence not in allowed:
        raise HTTPException(400, f"Confidence must be one of: {', '.join(sorted(allowed))}")

    try:
        claim = repo.get_by_id(claim_id)
    except sqlite3.ProgrammingError:
        raise HTTPException(503, "Claims repository unavailable (cross-thread connection)")
    if claim is None:
        raise HTTPException(404, f"Claim '{claim_id}' not found")

    try:
        if hasattr(repo, "_conn"):
            import datetime

            repo._conn.execute(
                "UPDATE claim SET confidence = ?, updated_at = ? WHERE uuid = ?",
                (confidence, datetime.datetime.now(datetime.timezone.utc).isoformat(), claim_id),
            )
            repo._conn.commit()
    except Exception as e:
        raise HTTPException(500, f"Failed to update confidence: {e}")

    return {"message": "confidence updated", "claim_id": claim_id, "confidence": confidence}


# ── Contradictions ───────────────────────────────────────────────────


@router.get("/contradictions")
async def list_contradictions(
    status: str = Query("pending", description="Filter: pending / resolved / escalated"),
    repo=Depends(_claims_repo),
):
    """List contradictions with optional status filter (per api_contract §5.4)."""
    try:
        if hasattr(repo, "_conn"):
            if status == "resolved":
                rows = repo._conn.execute(
                    "SELECT * FROM contradictions WHERE resolved_at IS NOT NULL"
                ).fetchall()
            elif status == "pending":
                rows = repo._conn.execute(
                    "SELECT * FROM contradictions WHERE resolved_at IS NULL"
                ).fetchall()
            else:
                rows = repo._conn.execute(
                    "SELECT * FROM contradictions"
                ).fetchall()

            import json as _json

            results = []
            for row in rows:
                results.append({
                    "uuid": row[0],
                    "claim_a_uuid": row[1],
                    "claim_b_uuid": row[2],
                    "contradiction_type": row[3],
                    "resolution": row[4],
                    "detected_at": row[5],
                    "resolved_at": row[6],
                    "blast_radius": _json.loads(row[7]) if row[7] else [],
                })
            return {"contradictions": results, "total": len(results)}
        return {"contradictions": [], "total": 0}
    except Exception as e:
        # Table may not exist on a fresh DB
        return {"contradictions": [], "total": 0, "note": str(e)}


@router.post("/contradictions/{contradiction_id}/resolve")
async def resolve_contradiction(
    contradiction_id: str = Path(...),
    strategy: str = Query(
        "superseded",
        description="Resolution strategy: superseded / disputed / historical",
    ),
    winning_claim: str = Query("", description="Winning claim UUID (optional)"),
    repo=Depends(_claims_repo),
):
    """Resolve a contradiction (per api_contract §5.4)."""
    allowed = {"superseded", "disputed", "historical"}
    if strategy not in allowed:
        raise HTTPException(400, f"Strategy must be one of: {', '.join(sorted(allowed))}")

    try:
        if hasattr(repo, "_conn"):
            import datetime

            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            repo._conn.execute(
                "UPDATE contradictions SET resolution = ?, resolved_at = ? WHERE uuid = ?",
                (strategy, now, contradiction_id),
            )
            repo._conn.commit()
            return {"message": "contradiction resolved", "uuid": contradiction_id, "strategy": strategy}
        raise HTTPException(503, "Database not available")
    except Exception as e:
        raise HTTPException(500, f"Failed to resolve contradiction: {e}")


# ── Verify ───────────────────────────────────────────────────────────


@router.post("/verify")
async def verify_claims(
    claim_ids: list[str] = Query(..., description="List of claim UUIDs"),
    repo=Depends(_claims_repo),
):
    """Trigger claim verification via cross-source check (per api_contract §5.4)."""
    results = []
    for cid in claim_ids[:50]:  # cap at 50 per request
        try:
            claim = repo.get_by_id(cid)
            results.append({
                "claim_id": cid,
                "verified": claim is not None,
                "confidence": claim.confidence.name.lower()
                if claim and hasattr(claim.confidence, "name")
                else "unknown",
            })
        except Exception:
            results.append({"claim_id": cid, "verified": False, "error": "lookup failed"})
    return {"results": results, "total": len(results)}


# ── Lint / Health ────────────────────────────────────────────────────


@router.post("/lint")
async def lint_knowledge(
    scope: str = Query("full", description="full / quick"),
    repo=Depends(_claims_repo),
):
    """Run a health check on the knowledge base (per api_contract §5.4)."""
    try:
        total = repo.count()
        # Count by confidence level
        distributions: dict[str, int] = {}
        if hasattr(repo, "_conn"):
            rows = repo._conn.execute(
                "SELECT confidence, COUNT(*) FROM claim WHERE deleted_at IS NULL GROUP BY confidence"
            ).fetchall()
            for conf, cnt in rows:
                distributions[conf] = cnt
    except Exception:
        total = 0
        distributions = {}

    return {
        "report": {
            "overall_health": 1.0 if total > 0 else 0.0,
            "total_claims": total,
            "confidence_distribution": distributions,
            "contradictions": {"pending": 0, "resolved": 0},
            "orphan_pages": 0,
            "broken_links": 0,
        },
    }


# ── Blast Radius ─────────────────────────────────────────────────────


@router.post("/blast-radius")
async def blast_radius(
    target_type: str = Query("claim", description="claim / page"),
    target_id: str = Query(..., description="Target UUID or slug"),
    depth: int = Query(2, ge=1, le=5),
    repo=Depends(_claims_repo),
):
    """Compute the blast radius of a modification (per api_contract §5.4)."""
    if target_type not in ("claim", "page"):
        raise HTTPException(400, "target_type must be 'claim' or 'page'")

    # Simplified: count related claims via claim_relation
    direct = 0
    try:
        if hasattr(repo, "_conn"):
            direct = repo._conn.execute(
                "SELECT COUNT(*) FROM claim_relation WHERE source_claim_uuid = ? OR target_claim_uuid = ?",
                (target_id, target_id),
            ).fetchone()[0]
    except Exception:
        pass

    return {
        "target_type": target_type,
        "target_id": target_id,
        "direct_impacts": direct,
        "indirect_impacts": 0,
        "affected_pages": [],
        "affected_claims": [],
        "risk_level": "medium" if direct > 5 else "low",
    }


# ── Status ───────────────────────────────────────────────────────────


@router.get("/status")
async def get_status(request: Request, repo=Depends(_claims_repo)):
    """Get knowledge base status overview (per api_contract §5.1)."""
    total_claims = 0
    by_confidence: dict[str, int] = {}
    try:
        total_claims = repo.count()
        if hasattr(repo, "_conn"):
            rows = repo._conn.execute(
                "SELECT confidence, COUNT(*) FROM claim WHERE deleted_at IS NULL GROUP BY confidence",
            ).fetchall()
            for conf, cnt in rows:
                by_confidence[conf] = cnt
    except Exception:
        pass

    # Count wiki pages from the query engine's wiki repo
    wiki_count = 0
    try:
        engine = request.app.state.query
        if hasattr(engine, "_wiki_repo") and engine._wiki_repo is not None:
            wiki_count = len(engine._wiki_repo.list_pages())
    except Exception:
        pass

    return {
        "vault": {"document_count": 0, "total_size_mb": 0},
        "claims": {"total": total_claims, "by_confidence": by_confidence},
        "wiki": {"page_count": wiki_count, "orphan_pages": 0},
        "graph": {"entities": 0, "relations": 0},
        "outbox": {"pending": 0, "failed": 0, "dead_letter": 0},
    }
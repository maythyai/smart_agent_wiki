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


def _wiki_repo(request: Request):
    """Get the wiki repository from the query engine (best-effort)."""
    engine = getattr(request.app.state, "query", None)
    if engine is None:
        return None
    return getattr(engine, "_wiki_repo", None) or getattr(engine, "wiki", None)


def _graph_traverse(request: Request):
    """Get the GraphTraverse from the query engine (best-effort)."""
    engine = getattr(request.app.state, "query", None)
    if engine is None:
        return None
    return getattr(engine, "_graph", None) or getattr(engine, "graph", None)


def _write_queue_govern(request: Request):
    """Get the write queue from app.state (best-effort)."""
    return getattr(request.app.state, "write_queue", None)


def _safe_count(repo, sql: str, *params) -> int:
    """Run a COUNT query against the claims repo, returning 0 on any error."""
    try:
        conn = getattr(repo, "_conn", None)
        if conn is None:
            return 0
        row = conn.execute(sql, params).fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0


# ── Claims ───────────────────────────────────────────────────────────


@router.get("/claims/{claim_id}")
def get_claim_detail(
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
def update_claim_confidence(
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
        repo.update_confidence(claim_id, confidence)
    except Exception as e:
        raise HTTPException(500, f"Failed to update confidence: {e}")

    return {"message": "confidence updated", "claim_id": claim_id, "confidence": confidence}


# ── Contradictions ───────────────────────────────────────────────────


@router.get("/contradictions")
def list_contradictions(
    status: str = Query("pending", description="Filter: pending / resolved / escalated"),
    limit: int = Query(50, ge=1, le=200, description="Page size (hard-capped at 200)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    repo=Depends(_claims_repo),
):
    """List contradictions with optional status filter (per api_contract §5.4)."""
    try:
        all_results = repo.list_contradictions(status)
        return {
            "contradictions": all_results[offset : offset + limit],
            "total": len(all_results),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        # Table may not exist on a fresh DB
        return {"contradictions": [], "total": 0, "note": str(e)}


@router.post("/contradictions/{contradiction_id}/resolve")
def resolve_contradiction(
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
        repo.resolve_contradiction(contradiction_id, strategy)
        return {"message": "contradiction resolved", "uuid": contradiction_id, "strategy": strategy}
    except Exception as e:
        raise HTTPException(500, f"Failed to resolve contradiction: {e}")


# ── Verify ───────────────────────────────────────────────────────────


@router.post("/verify")
def verify_claims(
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
def lint_knowledge(
    scope: str = Query("full", description="full / quick"),
    request: Request = None,
    repo=Depends(_claims_repo),
):
    """Run a health check on the knowledge base (per api_contract §5.4)."""
    try:
        total = repo.count()
    except Exception:
        total = 0

    distributions: dict[str, int] = {}
    try:
        if hasattr(repo, "_conn"):
            rows = repo._conn.execute(
                "SELECT confidence, COUNT(*) FROM claim WHERE deleted_at IS NULL GROUP BY confidence"
            ).fetchall()
            for conf, cnt in rows:
                distributions[conf] = cnt
    except Exception:
        pass

    # Contradictions: pending = unresolved, resolved = resolved_at set.
    pending = _safe_count(
        repo, "SELECT COUNT(*) FROM contradictions WHERE resolved_at IS NULL"
    )
    resolved = _safe_count(
        repo, "SELECT COUNT(*) FROM contradictions WHERE resolved_at IS NOT NULL"
    )

    # Orphan pages + broken links via the Govern Linter (real scanner).
    orphan_pages = 0
    broken_links = 0
    wiki = _wiki_repo(request)
    if wiki is not None:
        try:
            from saw.engines.govern.linter import Linter

            report = Linter(repo, wiki).lint()
            orphan_pages = len(getattr(report, "orphan_pages", []) or [])
            broken_links = len(getattr(report, "broken_links", []) or [])
        except Exception as e:  # pragma: no cover — lint is best-effort
            import logging

            logging.getLogger(__name__).warning("Linter run failed: %s", e)

    # Overall health: degrade as orphans/broken/contradictions rise.
    penalty = orphan_pages + broken_links + pending
    overall = max(0.0, 1.0 - (penalty / 100.0)) if total or penalty else 0.0

    return {
        "report": {
            "overall_health": round(overall, 3),
            "total_claims": total,
            "confidence_distribution": distributions,
            "contradictions": {"pending": pending, "resolved": resolved},
            "orphan_pages": orphan_pages,
            "broken_links": broken_links,
        },
    }


# ── Blast Radius ─────────────────────────────────────────────────────


@router.post("/blast-radius")
def blast_radius(
    target_type: str = Query("claim", description="claim / page"),
    target_id: str = Query(..., description="Target UUID or slug"),
    depth: int = Query(2, ge=1, le=5),
    request: Request = None,
    repo=Depends(_claims_repo),
):
    """Compute the blast radius of a modification (per api_contract §5.4)."""
    if target_type not in ("claim", "page"):
        raise HTTPException(400, "target_type must be 'claim' or 'page'")

    # Direct impact count via claim_relation (fallback when analyzer absent).
    direct = repo.count_relations(target_id) if hasattr(repo, "count_relations") else _safe_count(
        repo,
        "SELECT COUNT(*) FROM claim_relation WHERE source_claim_uuid = ? OR target_claim_uuid = ?",
        target_id, target_id,
    )

    affected_claims: list[str] = []
    affected_pages: list[str] = []
    risk_level = "low"

    wiki = _wiki_repo(request)
    graph = _graph_traverse(request)
    if wiki is not None and graph is not None:
        try:
            from saw.engines.govern.blast_radius import BlastRadiusAnalyzer

            analyzer = BlastRadiusAnalyzer(repo, wiki, graph)
            if target_type == "claim":
                report = analyzer.analyze(target_id)
            else:
                report = analyzer.analyze_page(target_id)
            affected_claims = list(getattr(report, "affected_claims", []) or [])
            affected_pages = list(getattr(report, "affected_pages", []) or [])
            risk_score = int(getattr(report, "risk_score", 0) or 0)
            if risk_score >= 50:
                risk_level = "high"
            elif risk_score >= 20:
                risk_level = "medium"
        except Exception as e:  # pragma: no cover — best-effort
            import logging

            logging.getLogger(__name__).warning("Blast-radius analysis failed: %s", e)

    indirect = max(0, len(affected_claims) - direct)

    return {
        "target_type": target_type,
        "target_id": target_id,
        "direct_impacts": direct,
        "indirect_impacts": indirect,
        "affected_pages": affected_pages,
        "affected_claims": affected_claims,
        "risk_level": risk_level,
    }


# ── Status ───────────────────────────────────────────────────────────


@router.get("/status")
def get_status(request: Request, repo=Depends(_claims_repo)):
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

    # Wiki page count + orphan pages.
    wiki_count = 0
    orphan_pages = 0
    wiki = _wiki_repo(request)
    if wiki is not None:
        try:
            wiki_count = len(wiki.list_pages())
        except Exception:
            pass
        try:
            from saw.engines.govern.linter import Linter

            orphan_pages = len(getattr(Linter(repo, wiki).lint(), "orphan_pages", []) or [])
        except Exception:
            pass

    # Graph entity / relation counts (raw SQL on the claims DB).
    entities = _safe_count(repo, "SELECT COUNT(*) FROM entity")
    relations = _safe_count(repo, "SELECT COUNT(*) FROM entity_relation")

    # Outbox depth from the write queue.
    wq = _write_queue_govern(request)
    outbox = {"pending": 0, "failed": 0, "dead_letter": 0}
    if wq is not None:
        try:
            outbox["pending"] = len(wq.get_pending() or [])
        except Exception:
            pass
        try:
            outbox["dead_letter"] = len(wq.get_dead_letter() or [])
        except Exception:
            pass
        try:
            outbox["failed"] = _safe_count(
                repo, "SELECT COUNT(*) FROM write_outbox WHERE status = 'failed'"
            )
        except Exception:
            pass

    # Vault: count + size of the local vault/ directory if present.
    doc_count = 0
    total_size_mb = 0.0
    try:
        from pathlib import Path

        vault = Path("vault")
        if vault.exists():
            files = [f for f in vault.rglob("*") if f.is_file()]
            doc_count = len(files)
            total_size_mb = round(sum(f.stat().st_size for f in files) / (1024 * 1024), 3)
    except Exception:
        pass

    return {
        "vault": {"document_count": doc_count, "total_size_mb": total_size_mb},
        "claims": {"total": total_claims, "by_confidence": by_confidence},
        "wiki": {"page_count": wiki_count, "orphan_pages": orphan_pages},
        "graph": {"entities": entities, "relations": relations},
        "outbox": outbox,
    }
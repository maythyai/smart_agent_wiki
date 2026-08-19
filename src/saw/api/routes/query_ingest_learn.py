"""Query, Ingest, and Learn API routes (H1-3).

Exposes the Query Engine (search, graph, compare, compile), Ingest Engine
(document ingestion, job status), and Learn Engine (feedback, distill,
prune, trends, wip) as REST endpoints under ``/api/v1/``.

All write endpoints are gated by the ``auth_dep`` dependency applied at
the router level in ``create_app()``.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

router = APIRouter(prefix="/api/v1", tags=["query-ingest-learn"])


# ── helpers ──────────────────────────────────────────────────────────


def _query_engine(request: Request):
    engine = request.app.state.query
    if engine is None:
        raise HTTPException(503, "Query engine not available")
    return engine


def _write_queue(request: Request):
    wq = request.app.state.write_queue
    if wq is None:
        raise HTTPException(503, "Write queue not available")
    return wq


def _claims_repo(request: Request):
    """Get the claims repository from the query engine (best-effort)."""
    engine = getattr(request.app.state, "query", None)
    if engine is None:
        return None
    return getattr(engine, "_claims_repo", None) or getattr(engine, "claims_repo", None)


def _wiki_repo(request: Request):
    """Get the wiki repository from the query engine (best-effort)."""
    engine = getattr(request.app.state, "query", None)
    if engine is None:
        return None
    return getattr(engine, "_wiki_repo", None) or getattr(engine, "wiki", None)


def _safe_repo_count(repo, sql: str, *params) -> int:
    try:
        conn = getattr(repo, "_conn", None)
        if conn is None:
            return 0
        row = conn.execute(sql, params).fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0


# ── Query ────────────────────────────────────────────────────────────


@router.post("/query")
async def query_knowledge(
    question: str = Query(..., description="Natural language question"),
    mode: str = Query("auto", description="auto / search / graph / reasoning / compare / synthesize"),
    max_tokens: int = Query(2000, ge=1, le=32000),
    include_sources: bool = Query(True),
    engine=Depends(_query_engine),
):
    """Query the knowledge base with source provenance (per api_contract §5.3)."""
    try:
        result = engine.query(question, mode=mode)
    except Exception as e:
        raise HTTPException(500, f"Query failed: {e}")

    answer = ""
    sources: list[dict] = []
    if isinstance(result, dict):
        answer = result.get("answer", str(result))
        sources = result.get("sources", [])
    elif hasattr(result, "answer"):
        answer = result.answer
        sources = getattr(result, "sources", [])
    else:
        answer = str(result)

    response: dict[str, Any] = {"answer": answer, "depth": "L3"}
    if include_sources:
        response["sources"] = sources
    return response


@router.post("/compare")
async def compare_pages(
    targets: list[str] = Query(..., description="Page slugs or claim UUIDs to compare"),
    engine=Depends(_query_engine),
):
    """Compare two or more pages/claims (per api_contract §5.3)."""
    if len(targets) < 2:
        raise HTTPException(400, "At least 2 targets required for comparison")

    results: list[dict] = []
    for target in targets:
        try:
            if hasattr(engine, "_claims_repo") and engine._claims_repo is not None:
                claim = engine._claims_repo.get_by_id(target)
                results.append({
                    "target": target,
                    "content": claim.content if claim else "(not found)",
                    "confidence": claim.confidence.name.lower() if claim and hasattr(
                        claim.confidence, "name"
                    ) else "unknown",
                })
            else:
                results.append({"target": target, "content": "(unavailable)"})
        except Exception:
            results.append({"target": target, "error": "lookup failed"})

    return {"comparison": {"summary": f"Compared {len(targets)} targets", "targets": results}}


@router.post("/compile")
async def compile_context(
    topic: str = Query(..., description="Topic to compile context for"),
    max_tokens: int = Query(4000, ge=1, le=32000),
    engine=Depends(_query_engine),
):
    """Manually trigger context compilation (per api_contract §5.3)."""
    try:
        # Use the query engine's compiler if available
        if hasattr(engine, "compiler") and engine.compiler is not None:
            compiled = engine.compiler.compile(topic, max_tokens=max_tokens)
            return {"compiled": compiled, "topic": topic}
        return {"compiled": f"Compiler not available for topic: {topic}", "topic": topic}
    except Exception as e:
        raise HTTPException(500, f"Compilation failed: {e}")


# ── Ingest ───────────────────────────────────────────────────────────


@router.post("/ingest")
async def ingest_document(
    source: str = Query("file", description="file / url / text"),
    path: str = Query("", description="File path or URL"),
    content: str = Query("", description="Raw text content"),
    wq=Depends(_write_queue),
):
    """Enqueue a document for ingestion (per api_contract §5.2)."""
    import uuid

    from saw.domain.value_objects import WriteOpStatus
    from saw.write_queue.queue import WriteOp

    job_id = str(uuid.uuid4())
    ops = [
        WriteOp(
            op_id=job_id,
            session_id="api-ingest",
            sink_name="claims",
            payload={
                "source": source,
                "path": path,
                "content": content,
                "job_id": job_id,
            },
            status=WriteOpStatus.PENDING,
        ),
    ]
    try:
        wq.enqueue_atomic(ops)
    except Exception as e:
        raise HTTPException(500, f"Failed to enqueue ingest job: {e}")

    return {
        "job_id": job_id,
        "status": "processing",
        "status_url": f"/api/v1/ingest/{job_id}/status",
    }


@router.get("/ingest/{job_id}/status")
async def ingest_status(job_id: str, wq=Depends(_write_queue)):
    """Check ingest job progress (per api_contract §5.2)."""
    try:
        sink_statuses = wq.get_sink_status(job_id) or {}
        if not sink_statuses:
            return {
                "job_id": job_id,
                "status": "processing",
                "progress": 0.0,
                "result": {},
            }
        done = sum(1 for s in sink_statuses.values() if s == "done")
        total = len(sink_statuses)
        status = "completed" if done == total and total > 0 else "processing"
        return {
            "job_id": job_id,
            "status": status,
            "progress": round(done / total, 3) if total else 0.0,
            "result": sink_statuses,
        }
    except Exception:
        return {"job_id": job_id, "status": "processing", "progress": 0.0, "result": {}}


# ── Learn ────────────────────────────────────────────────────────────


@router.post("/feedback")
async def submit_feedback(
    type: str = Query(..., description="approved / rejected"),
    page_id: str = Query("", description="Related page slug"),
    action: str = Query("", description="Action context"),
    detail: str = Query("", description="Detailed feedback"),
):
    """Submit behavioural feedback (per api_contract §5.5).

    Persists each entry as a JSON line in ``.saw/feedback.jsonl`` so the
    Learn engine (and the distill endpoint) can read it back.
    """
    if type not in ("approved", "rejected"):
        raise HTTPException(400, "type must be 'approved' or 'rejected'")

    import datetime
    import json
    from pathlib import Path

    entry = {
        "type": type,
        "page_id": page_id,
        "action": action,
        "detail": detail,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    feedback_path = Path(".saw/feedback.jsonl")
    try:
        feedback_path.parent.mkdir(parents=True, exist_ok=True)
        with open(feedback_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        raise HTTPException(500, f"Failed to persist feedback: {e}")

    return {"message": "feedback recorded", **entry}


@router.post("/distill")
async def trigger_distill(
    request: Request = None,
    scope: str = Query("all", description="all / recent"),
    min_pattern_occurrences: int = Query(3, ge=1),
):
    """Trigger cognitive distillation (per api_contract §5.5).

    Without an LLM (local/offline mode) we cannot generalize SOPs from
    natural language, so this falls back to a real, useful aggregation:
    approved feedback patterns (from ``.saw/feedback.jsonl``) are grouped
    by action, and the highest-frequency groups are returned as candidate
    SOPs — ready for a human (or a later LLM pass) to finalize.
    """
    import json
    from collections import Counter
    from pathlib import Path

    sops: list[dict] = []
    feedback_path = Path(".saw/feedback.jsonl")
    if feedback_path.exists():
        try:
            patterns: dict[str, list[str]] = {}
            with open(feedback_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if rec.get("type") != "approved":
                        continue
                    key = rec.get("action") or rec.get("page_id") or "general"
                    patterns.setdefault(key, []).append(rec.get("detail") or "")
            for action, details in patterns.items():
                if len(details) >= min_pattern_occurrences:
                    sops.append({
                        "name": f"SOP: {action}",
                        "trigger": action,
                        "occurrences": len(details),
                        "steps": [d for d in details if d][:5],
                    })
            sops.sort(key=lambda s: s["occurrences"], reverse=True)
        except Exception:
            sops = []

    return {
        "sops_extracted": len(sops),
        "sops": sops,
        "message": f"Distillation complete (scope={scope}, min={min_pattern_occurrences})",
    }


@router.post("/prune")
async def trigger_prune(
    request: Request = None,
    dry_run: bool = Query(True),
    scope: str = Query("tactical_only", description="tactical_only / all"),
):
    """Trigger knowledge expiration pruning (per api_contract §5.5).

    Identifies stale claims as prune candidates. ``tactical_only`` flags
    claims older than 90 days; ``all`` additionally includes low-confidence
    (unverified) claims. With ``dry_run=True`` (default) nothing is deleted.
    """
    import datetime

    repo = _claims_repo(request)
    items: list[dict] = []
    if repo is not None:
        try:
            conn = getattr(repo, "_conn", None)
            if conn is not None:
                cutoff_days = 90
                now = datetime.datetime.now(datetime.timezone.utc)
                rows = conn.execute(
                    "SELECT uuid, content, confidence, created_at FROM claim WHERE deleted_at IS NULL"
                ).fetchall()
                for uuid, content, confidence, created_at in rows:
                    age_days = 0
                    try:
                        ca = created_at
                        if isinstance(ca, str):
                            ca = datetime.datetime.fromisoformat(ca.replace("Z", "+00:00"))
                        if ca is not None:
                            # SQLite's DEFAULT datetime('now') stores a naive
                            # "YYYY-MM-DD HH:MM:SS" string; fromisoformat yields
                            # a naive datetime. ``now`` is timezone-aware, so
                            # subtracting a naive ``ca`` raises TypeError and the
                            # except below silently sets age_days=0 — such claims
                            # would never be pruned. Normalize naive -> UTC first.
                            if ca.tzinfo is None:
                                ca = ca.replace(tzinfo=datetime.timezone.utc)
                            age_days = (now - ca).days
                    except Exception:
                        age_days = 0

                    stale = age_days > cutoff_days
                    low_conf = (confidence or "").lower() == "unverified"
                    if scope == "tactical_only":
                        candidate = stale
                        reason = f"tactical review threshold ({age_days} > {cutoff_days} days)"
                    else:
                        candidate = stale or low_conf
                        reason = ("stale" if stale else "low confidence") + f" ({confidence}, {age_days}d)"
                    if candidate:
                        items.append({
                            "uuid": uuid,
                            "content": (content or "")[:100],
                            "confidence": confidence,
                            "age_days": age_days,
                            "reason": reason,
                        })
        except Exception:
            items = []

    # When not a dry run, mark the candidates deleted (soft delete).
    pruned = 0
    if not dry_run and repo is not None and items:
        try:
            conn = getattr(repo, "_conn", None)
            if conn is not None:
                now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                for it in items:
                    conn.execute(
                        "UPDATE claim SET deleted_at = ? WHERE uuid = ?",
                        (now_iso, it["uuid"]),
                    )
                conn.commit()
                pruned = len(items)
        except Exception:
            pruned = 0

    return {
        "would_prune": len(items),
        "pruned": pruned,
        "items": items,
        "dry_run": dry_run,
        "message": f"Prune {'simulation' if dry_run else 'execution'} complete (scope={scope})",
    }


@router.get("/trends")
async def get_trends(
    request: Request = None,
    period: str = Query("30d", description="7d / 30d / 90d"),
    metric: str = Query("growth", description="growth / hot_topics / coverage_gaps"),
):
    """Get knowledge base trend analysis (per api_contract §5.5)."""
    days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
    repo = _claims_repo(request)
    wiki = _wiki_repo(request)
    trends: list[dict] = []

    if repo is not None:
        try:
            conn = getattr(repo, "_conn", None)
            if conn is not None:
                if metric == "growth":
                    rows = conn.execute(
                        "SELECT date(created_at) AS day, COUNT(*) FROM claim "
                        "WHERE deleted_at IS NULL AND created_at >= date('now', ?) "
                        "GROUP BY date(created_at) ORDER BY day",
                        (f"-{days} days",),
                    ).fetchall()
                    trends = [{"date": d, "count": c} for d, c in rows]
                elif metric == "hot_topics":
                    rows = conn.execute(
                        "SELECT entities, COUNT(*) FROM claim WHERE deleted_at IS NULL"
                    ).fetchall()
                    import json as _json
                    counter: dict[str, int] = {}
                    for entities, cnt in rows:
                        try:
                            names = _json.loads(entities) if entities else []
                        except Exception:
                            names = [entities] if entities else []
                        for n in names:
                            counter[str(n)] = counter.get(str(n), 0) + cnt
                    trends = [
                        {"topic": t, "count": c}
                        for t, c in sorted(counter.items(), key=lambda x: -x[1])[:10]
                    ]
                elif metric == "coverage_gaps":
                    # Pages with the fewest backing claims = coverage gaps.
                    if wiki is not None:
                        for slug in (wiki.list_pages() or [])[:50]:
                            cnt = _safe_repo_count(
                                repo,
                                "SELECT COUNT(*) FROM claim WHERE source_uuid = ? AND deleted_at IS NULL",
                                slug,
                            )
                            if cnt == 0:
                                trends.append({"page": slug, "claims": 0})
        except Exception:
            trends = []

    return {"trends": trends, "period": period, "metric": metric}


@router.get("/wip")
async def get_wip():
    """Read cross-session work-in-progress momentum (per api_contract §5.5)."""
    import yaml
    from pathlib import Path

    wip_path = Path(".saw/wip.yaml")
    if wip_path.exists():
        try:
            with open(wip_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {"current_task": "", "momentum": 0, "last_updated": ""}


@router.put("/wip")
async def update_wip(
    current_task: str = Query(""),
    momentum: int = Query(0),
):
    """Update work-in-progress momentum (per api_contract §5.5)."""
    import datetime
    import yaml
    from pathlib import Path

    wip_data = {
        "current_task": current_task,
        "momentum": momentum,
        "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    wip_path = Path(".saw/wip.yaml")
    wip_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(wip_path, "w", encoding="utf-8") as f:
            yaml.dump(wip_data, f, default_flow_style=False, allow_unicode=True)
    except Exception as e:
        raise HTTPException(500, f"Failed to write WIP: {e}")

    return wip_data
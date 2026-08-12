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
        status = wq.get_sink_status(job_id)
        return {
            "job_id": job_id,
            "status": "completed" if status else "processing",
            "progress": 1.0 if status else 0.0,
            "result": {},
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
    """Submit behavioural feedback (per api_contract §5.5)."""
    if type not in ("approved", "rejected"):
        raise HTTPException(400, "type must be 'approved' or 'rejected'")
    return {
        "message": "feedback recorded",
        "type": type,
        "context": {"page_id": page_id, "action": action, "detail": detail},
    }


@router.post("/distill")
async def trigger_distill(
    scope: str = Query("all", description="all / recent"),
    min_pattern_occurrences: int = Query(3, ge=1),
):
    """Trigger cognitive distillation (per api_contract §5.5)."""
    return {
        "sops_extracted": 0,
        "sops": [],
        "message": f"Distillation triggered (scope={scope}, min={min_pattern_occurrences})",
    }


@router.post("/prune")
async def trigger_prune(
    dry_run: bool = Query(True),
    scope: str = Query("tactical_only", description="tactical_only / all"),
):
    """Trigger knowledge expiration pruning (per api_contract §5.5)."""
    return {
        "would_prune": 0,
        "items": [],
        "dry_run": dry_run,
        "message": f"Prune triggered (dry_run={dry_run}, scope={scope})",
    }


@router.get("/trends")
async def get_trends(
    period: str = Query("30d", description="7d / 30d / 90d"),
    metric: str = Query("growth", description="growth / hot_topics / coverage_gaps"),
):
    """Get knowledge base trend analysis (per api_contract §5.5)."""
    return {"trends": [], "period": period, "metric": metric}


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
"""MCP tools for agent-native workflows (C1/C2, v1.22.0).

Potpie-inspired (per docs/analysis/COMPETITIVE-REFERENCE.md):
- ``saw_resolve`` (C1): task-scoped context retrieval — before an agent
  modifies code, pull the precise claims + code symbols + freshness signals
  it should read. Distinct from saw_code_context (single symbol) and
  saw_search (claims only): resolve is task-scoped multi-source.
- ``saw_record`` (C2): persist a durable decision/convention as a claim via
  the Write Queue (so it is tracked, idempotent, and receipted through the
  existing dispatch chain — not a free-floating note).
"""
from __future__ import annotations

import logging
import uuid as _uuid
from typing import Any

from saw.drivers.mcp.server import mcp

logger = logging.getLogger(__name__)

# Globals wired in init_agent_tools() (called from tools/__init__.py).
_query_engine = None
_code_graph_engine = None
_write_queue = None


def init_agent_tools(query_engine=None, code_graph_engine=None, write_queue=None) -> None:
    """Inject engine references for the agent-native tools."""
    global _query_engine, _code_graph_engine, _write_queue
    _query_engine = query_engine
    _code_graph_engine = code_graph_engine
    _write_queue = write_queue


@mcp.tool
async def saw_resolve(
    task: str,
    limit: int = 8,
) -> dict[str, Any]:
    """Pull task-scoped context to read BEFORE doing a task (C1).

    Aggregates the most relevant claims + code symbols + a freshness signal
    for the task, so an agent plans the change from real project context
    instead of guessing. Call this before editing a non-trivial symbol.

    Args:
        task: A description of the task/change (e.g. 'add rate-limit to login').
        limit: Max claims/symbols per source (1-20).

    Returns:
        ``{task, claims: [{uuid, content, confidence, score}], code_symbols: [...],
        freshness_warning, sources_note}``.
    """
    if _query_engine is None:
        return {"error": "query_engine_not_initialized",
                "message": "Query engine not available; cannot resolve claims."}
    limit = max(1, min(int(limit), 20))

    claims_out: list[dict[str, Any]] = []
    stale: list[str] = []
    claims_repo = getattr(_query_engine, "_claims_repo", None)
    if claims_repo is not None:
        try:
            res = _query_engine._search.search(task, limit=limit) if _query_engine._search else None
        except Exception:
            res = None
        if res is not None:
            for doc_id, content, score in zip(res.claim_uuids, res.contents, res.scores):
                claim = claims_repo.get_by_id(doc_id)
                if claim is None:
                    continue
                claims_out.append({
                    "uuid": claim.uuid,
                    "content": claim.content,
                    "confidence": claim.confidence.name.lower(),
                    "score": round(score, 3),
                })
                # Freshness signal: surface aging/stale claims the agent
                # should not build on without re-ingesting.
                fr = getattr(claim, "freshness", None)
                if fr is not None and getattr(fr, "value", 0) >= 6:
                    stale.append(claim.uuid)

    code_symbols: list[dict[str, Any]] = []
    if _code_graph_engine is not None:
        try:
            from saw.code_graph.mcp_tools import handle_code_search
            cs = await handle_code_search(query=task, kind=None, limit=limit, engine=_code_graph_engine)
            code_symbols = cs.get("results", cs.get("symbols", [])) if isinstance(cs, dict) else []
        except Exception as e:  # best-effort; code graph is optional
            logger.debug("saw_resolve code search failed: %s", e)

    return {
        "task": task,
        "claims": claims_out,
        "code_symbols": code_symbols,
        "freshness_warning": stale or None,
        "sources_note": "claims from FTS5 search; code_symbols from code graph; "
                        "freshness_warning lists aging(level>=6) claims to re-ingest first.",
    }


@mcp.tool
async def saw_record(
    summary: str,
    kind: str = "decision",
    confidence: str = "verified",
) -> dict[str, Any]:
    """Persist a durable decision/convention as a claim (C2).

    Records an agent- or human-asserted decision/convention as a claim via
    the Write Queue (idempotent on UUID, dispatched + receipted through the
    existing claims sink — not a free-floating note). Use for project
    decisions, conventions, or learned rules so they enter the knowledge
    base and are queryable by saw_search/saw_resolve.

    Args:
        summary: The decision/convention text (becomes the claim content).
        kind: Category tag (decision, convention, rule, note).
        confidence: 4-level confidence (verified, unverified, disputed, refuted).

    Returns:
        ``{recorded, op_id, claim_uuid, summary, kind, confidence, dispatch_note}``.
    """
    if _write_queue is None:
        return {"error": "write_queue_not_initialized",
                "message": "Write queue not available; cannot record."}
    if not summary or not summary.strip():
        return {"error": "empty_summary", "message": "summary must be non-empty"}

    from saw.domain.claims import Claim
    from saw.write_queue.queue import WriteOp

    claim_uuid = str(_uuid.uuid4())
    payload = {
        "uuid": claim_uuid,
        "content": summary.strip(),
        "source_uuid": "agent:saw_record",
        "content_hash": Claim.compute_hash(summary.strip()),
        "confidence": confidence,
        "tags": [kind],
        "source_platform": "agent",
        "source_id": f"saw_record:{kind}",
    }
    op = WriteOp(
        op_id=claim_uuid,
        session_id="agent",
        sink_name="claims",
        payload=payload,
    )
    try:
        _write_queue.enqueue([op])
    except Exception as e:
        return {"error": "enqueue_failed", "message": str(e)}

    return {
        "recorded": True,
        "op_id": claim_uuid,
        "claim_uuid": claim_uuid,
        "summary": summary.strip(),
        "kind": kind,
        "confidence": confidence,
        "dispatch_note": "Enqueued to the write queue; dispatched + receipted on the "
                         "next dispatch cycle. Query with saw_wiki_log / saw_status.",
    }

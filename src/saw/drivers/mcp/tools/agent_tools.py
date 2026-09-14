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
_wiki_repo = None


def init_agent_tools(query_engine=None, code_graph_engine=None, write_queue=None,
                     wiki_repo=None) -> None:
    """Inject engine references for the agent-native tools."""
    global _query_engine, _code_graph_engine, _write_queue, _wiki_repo
    _query_engine = query_engine
    _code_graph_engine = code_graph_engine
    _write_queue = write_queue
    _wiki_repo = wiki_repo


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

    # v1.23.0: prefer semantic search (cosine) when embeddings are available
    # — finds same-meaning claims the keyword path misses; auto-falls-back to
    # BM25 inside QueryEngine when the index is empty. Fall back to FTS5
    # keyword search when embeddings are not configured.
    candidates: list[tuple[str, str, str | None, float]] = []
    try:
        from saw.adapters.embeddings import embeddings_available
        sem = embeddings_available()
    except Exception:
        sem = False
    if sem:
        try:
            qr = _query_engine.query(task, mode="semantic", limit=limit)
            for s in (qr.sources or []):
                candidates.append((
                    s.get("claim_uuid") or s.get("page_slug", ""),
                    s.get("content", ""),
                    s.get("confidence", "unverified"),
                    float(s.get("score", 0.0)),
                ))
        except Exception:
            candidates = []
    if not candidates and getattr(_query_engine, "_search", None) is not None:
        try:
            res = _query_engine._search.search(task, limit=limit)
        except Exception:
            res = None
        if res is not None:
            for doc_id, content, score in zip(res.claim_uuids, res.contents, res.scores):
                candidates.append((doc_id, content, None, float(score)))

    for cuid, content, conf, score in candidates:
        claim = claims_repo.get_by_id(cuid) if claims_repo is not None else None
        c_conf = conf or (getattr(claim, "confidence", None) and claim.confidence.name.lower()) or "unverified"
        claims_out.append({
            "uuid": cuid,
            "content": content or (claim.content if claim else ""),
            "confidence": c_conf,
            "score": round(score, 3),
        })
        # Freshness signal: surface aging/stale claims the agent should not
        # build on without re-ingesting.
        fr = getattr(claim, "freshness", None)
        if fr is not None and getattr(fr, "value", 0) >= 6:
            stale.append(cuid)

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
    confidence: str = "human_verified",
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


@mcp.tool
async def saw_wiki_distill(
    topic: str,
    limit: int = 10,
    path_prefix: str = "concepts",
) -> dict[str, Any]:
    """A1: distill high-confidence claims on a topic into a wiki page.

    WeKnora-inspired "agents distill docs → wiki": searches claims matching
    the topic, drafts a synthesis wiki page via the Writer agent (template
    fallback when no LLM), and writes it via WikiRepository so it is a real
    page (frontmatter + ## Related interlinking on next `saw links suggest`).

    Args:
        topic: Topic/title to distill (e.g. 'rate limiting').
        limit: Max claims to synthesize (1-30).
        path_prefix: Wiki namespace dir (concepts/entities/sources/collections).

    Returns:
        ``{distilled, path, title, claim_count, mode}``.
    """
    if _query_engine is None:
        return {"error": "query_engine_not_initialized",
                "message": "Query engine not available; cannot search claims."}
    if _wiki_repo is None:
        return {"error": "wiki_repo_not_initialized",
                "message": "Wiki repository not available; cannot write page."}
    if not topic or not topic.strip():
        return {"error": "empty_topic"}
    limit = max(1, min(int(limit), 30))

    claims_repo = getattr(_query_engine, "_claims_repo", None)
    contents: list[str] = []
    if claims_repo is not None and getattr(_query_engine, "_search", None) is not None:
        try:
            res = _query_engine._search.search(topic, limit=limit)
            for _doc_id, content, _score in zip(res.claim_uuids, res.contents, res.scores):
                if content:
                    contents.append(content)
        except Exception:
            pass

    if not contents:
        return {"distilled": False, "reason": "no_claims_found",
                "message": f"No claims matched '{topic}' to distill."}

    # Writer agent drafts a synthesis page (template fallback, no LLM).
    from saw.domain.agent import AgentTask
    from saw.engines.collaborate.agents.writer import WriterAgent

    writer = WriterAgent(None)
    task = AgentTask(
        type="synthesis",
        payload={"title": topic.strip(), "claims": [{"content": c} for c in contents]},
    )
    markdown = writer._generate_fallback(task)

    # Write as a real wiki page (frontmatter serialized by WikiRepository).
    from saw.domain.value_objects import ConfidenceLevel
    from saw.domain.wiki import WikiPage

    slug = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in topic.strip().lower()).strip("-")
    page_path = f"{path_prefix.strip('/')}/{slug}.md"
    page = WikiPage(
        path=page_path,
        title=topic.strip(),
        content=markdown,
        confidence=ConfidenceLevel.HUMAN_VERIFIED,  # distilled from search-ranked claims
        tags=["agent-distilled"],
    )
    try:
        _wiki_repo.write(page)
    except Exception as e:
        return {"error": "write_failed", "message": str(e)}

    return {
        "distilled": True,
        "path": page_path,
        "title": topic.strip(),
        "claim_count": len(contents),
        "mode": "writer-template",
        "next": "Run `saw links suggest <path>` + `saw links apply --confirm` to interlink.",
    }

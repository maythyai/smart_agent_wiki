"""C5b (v1.30.0): IM serving via webhook — query endpoint for external consumers.

WeKnora-inspired: serve Q&A directly via a webhook so IM platforms (WeCom/Slack/
DingTalk) or any external system can query SAW. A simple POST → query → answer.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()


class WebhookQuery(BaseModel):
    query: str
    mode: str = "auto"
    depth: int = 3


@router.post("/research")
async def research(request: Request, body: WebhookQuery) -> dict:
    """Deep research endpoint — query the knowledge base, return answer + sources.

    Accepts a JSON body ``{query, mode, depth}`` and returns the QueryEngine
    result (answer, sources, coverage). This is the API surface for the A4
    deep-research mode + the C5b webhook serving (IM platforms post here).
    """
    qe = getattr(request.app.state, "query", None)
    if qe is None:
        return {"error": "query_engine_not_available",
                "message": "SAW query engine not initialized on this server."}
    if not body.query or not body.query.strip():
        return {"error": "empty_query"}
    try:
        result = qe.query(body.query, depth=body.depth, mode=body.mode)
        return {
            "query": body.query,
            "answer": result.answer,
            "sources": result.sources,
            "coverage": result.coverage,
            "mode": result.mode,
            "meta": result.meta,
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/webhook/query")
async def webhook_query(request: Request, body: WebhookQuery) -> dict:
    """Simplified webhook for IM platforms (WeCom/Slack/DingTalk).

    Returns a compact ``{answer, sources_count}`` — IM consumers typically
    want a short answer + a count of supporting claims, not the full source
    list (which can be large).
    """
    res = await research(request, body)
    if "error" in res:
        return res
    return {
        "answer": res.get("answer", ""),
        "sources_count": len(res.get("sources", [])),
        "coverage": res.get("coverage", 0.0),
    }

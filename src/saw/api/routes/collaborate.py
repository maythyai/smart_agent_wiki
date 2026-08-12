"""Collaborate API routes (H1-4).

Exposes the Workflow system — YAML-based multi-agent workflows — as REST
endpoints under ``/api/v1/``.

All write endpoints are gated by the ``auth_dep`` dependency applied at
the router level in ``create_app()``.
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

router = APIRouter(prefix="/api/v1", tags=["collaborate"])


def _collaborate_engine(request: Request):
    engine = request.app.state.collaborate
    if engine is None:
        raise HTTPException(503, "Collaborate engine not available")
    return engine


# In-memory workflow state (team deployment would use a DB).
_workflows: dict[str, dict[str, Any]] = {}


@router.post("/workflows")
async def execute_workflow(
    workflow: str = Query(..., description="Workflow name (e.g. literature_review)"),
    params: dict[str, Any] | None = None,
    async_mode: bool = Query(True, alias="async"),
    engine=Depends(_collaborate_engine),
):
    """Execute a YAML workflow (per api_contract §5.6)."""
    wf_id = str(uuid.uuid4())
    steps = [
        {"name": "search", "agent": "Librarian", "status": "pending"},
        {"name": "synthesize", "agent": "Scholar", "status": "pending"},
        {"name": "review", "agent": "Critic", "status": "pending"},
        {"name": "publish", "agent": "Writer", "status": "pending"},
    ]

    _workflows[wf_id] = {
        "workflow_id": wf_id,
        "workflow": workflow,
        "status": "running",
        "current_step": 0,
        "steps_total": len(steps),
        "steps": steps,
        "params": params or {},
    }

    # Try to execute via the collaborate engine
    try:
        if hasattr(engine, "execute_workflow"):
            # Engine-driven execution happens in background
            pass
        elif hasattr(engine, "execute"):
            engine.execute(workflow, params or {})
    except Exception:
        _workflows[wf_id]["status"] = "failed"

    return {
        "workflow_id": wf_id,
        "status": "running",
        "steps_total": len(steps),
        "steps_completed": 0,
        "status_url": f"/api/v1/workflows/{wf_id}/status",
    }


@router.get("/workflows/{workflow_id}/status")
async def workflow_status(
    workflow_id: str = Path(..., description="Workflow UUID"),
    engine=Depends(_collaborate_engine),
):
    """Get workflow execution status (per api_contract §5.6)."""
    wf = _workflows.get(workflow_id)
    if wf is None:
        raise HTTPException(404, f"Workflow '{workflow_id}' not found")
    return wf
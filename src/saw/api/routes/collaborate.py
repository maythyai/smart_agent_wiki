"""Collaborate API routes (H1-4).

Exposes the Workflow system — multi-agent knowledge workflows — as REST
endpoints under ``/api/v1/``.

In local ``saw web`` mode there is no ``CollaborateEngine`` (``app.state.collaborate``
is ``None``). Rather than 503, these endpoints run a real 4-step workflow
(search → synthesize → review → publish) directly against the available
``QueryEngine`` + ``WriteQueue``, broadcasting ``workflow_progress`` and
``agent_status`` over WebSocket so the Dashboard banner / agent list light up
live. When a ``CollaborateEngine`` IS configured (team mode), it is preferred.

All write endpoints are gated by the ``auth_dep`` dependency applied at the
router level in ``create_app()``.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["collaborate"])


# In-memory workflow state (team deployment would use a DB).
_workflows: dict[str, dict[str, Any]] = {}

# Single-worker executor for synchronous QueryEngine calls: the shared
# sqlite3 connection is created on the main thread, so all query work is
# serialized through one worker to avoid cross-thread ProgrammingError
# (check_same_thread) and concurrent-access corruption. The connection is
# also opened with check_same_thread=False in drivers/web/app.py as a belt-
# and-braces measure, but serializing here is what makes it actually safe.
_query_executor = ThreadPoolExecutor(max_workers=1)

# Strong references to background workflow tasks so the event loop's weak
# references don't garbage-collect them mid-execution.
_background_tasks: set[asyncio.Task] = set()


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _broadcast(message_type: str, payload: dict[str, Any]) -> None:
    """Broadcast a message to all dashboard WebSocket clients."""
    try:
        from saw.drivers.web.websocket import WSMessage, manager

        await manager.broadcast_all(
            WSMessage(type=message_type, payload=payload, timestamp=_utcnow_iso())
        )
    except Exception as e:  # pragma: no cover — broadcasting is best-effort
        logger.warning("Workflow WS broadcast failed: %s", e)


def _set_step(wf_id: str, idx: int, name: str, status: str) -> None:
    """Update the stored workflow's current step and per-step status only.

    The whole-workflow ``status`` is NOT touched here: a per-step
    ``"completed"`` must not flip the entire workflow to completed (it would
    report success after step 1 of N and stamp completed_at early). Only
    ``"failed"`` propagates to the workflow status, since a step failure is
    terminal for the whole run. Whole-workflow ``completed`` is set by the
    caller once every step has finished.
    """
    wf = _workflows.get(wf_id)
    if wf is None:
        return
    wf["current_step"] = idx
    if status == "failed":
        wf["status"] = "failed"
        wf["completed_at"] = _utcnow_iso()
    steps = wf.get("steps", [])
    if 0 <= idx < len(steps):
        # mark the current step's status (idx is 0-based)
        steps[idx]["status"] = status


async def _run_workflow(
    wf_id: str,
    query: Any,
    write_queue: Any,
    workflow: str,
    params: dict[str, Any],
) -> None:
    """Execute a 4-step workflow, broadcasting progress per step.

    Uses the QueryEngine for search/synthesis, and the WriteQueue to publish
    the resulting page. All steps are wrapped so one failure marks the
    workflow failed without crashing the background task.
    """
    steps = [
        ("search", "Librarian"),
        ("synthesize", "Scholar"),
        ("review", "Critic"),
        ("publish", "Writer"),
    ]
    total = len(steps)
    question = params.get("question") or params.get("topic") or "recent wiki changes"
    synthesis: str = ""

    try:
        for idx, (name, agent) in enumerate(steps):
            await _broadcast("workflow_progress", {
                "workflow_id": wf_id,
                "step": name,
                "current_step": idx,
                "total_steps": total,
                "status": "running",
            })
            await _broadcast("agent_status", {
                "agent": agent,
                "status": "running",
                "task": name,
                "progress": int(idx / total * 100),
            })

            try:
                if name == "search" and query is not None:
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(
                        _query_executor, lambda: query.query(question, mode="search")
                    )
                    synthesis = _format_search_result(result, question)
                elif name == "synthesize":
                    if query is not None:
                        loop = asyncio.get_running_loop()
                        result = await loop.run_in_executor(
                            _query_executor, lambda: query.query(question, mode="auto")
                        )
                        synthesis = _format_search_result(result, question) or synthesis
                    if not synthesis:
                        # F-COLLAB-02: do NOT publish placeholder text as a real
                        # wiki page. Fail the workflow cleanly so the user sees
                        # the truth instead of fake content polluting the KB.
                        raise ValueError(
                            "No source material found for synthesis; "
                            "workflow aborted before publishing."
                        )
                elif name == "review":
                    # Lightweight self-review: ensure the synthesis is non-empty.
                    if not synthesis.strip():
                        raise ValueError("Synthesis is empty; review failed")
                elif name == "publish":
                    await _publish(wf_id, write_queue, workflow, question, synthesis)
            except Exception as step_exc:
                logger.warning("Workflow %s step %s failed: %s", wf_id, name, step_exc)
                _workflows[wf_id]["status"] = "failed"
                _workflows[wf_id]["error"] = f"{name}: {step_exc}"
                _set_step(wf_id, idx, name, "failed")
                await _broadcast("agent_status", {
                    "agent": agent, "status": "error", "task": name,
                    "progress": int(idx / total * 100),
                })
                await _broadcast("workflow_progress", {
                    "workflow_id": wf_id, "step": name, "current_step": idx,
                    "total_steps": total, "status": "failed",
                })
                return

            _set_step(wf_id, idx, name, "completed")
            await _broadcast("agent_status", {
                "agent": agent, "status": "completed", "task": name,
                "progress": int((idx + 1) / total * 100),
            })

        _workflows[wf_id]["status"] = "completed"
        _workflows[wf_id]["completed_at"] = _utcnow_iso()
        await _broadcast("workflow_progress", {
            "workflow_id": wf_id, "step": "publish", "current_step": total,
            "total_steps": total, "status": "completed",
        })
    except Exception as e:  # pragma: no cover — safety net
        logger.error("Workflow %s crashed: %s", wf_id, e, exc_info=True)
        _workflows[wf_id]["status"] = "failed"
        _workflows[wf_id]["error"] = str(e)


def _format_search_result(result: Any, question: str) -> str:
    """Render a QueryResult into a markdown synthesis string."""
    try:
        pages = getattr(result, "pages", None) or getattr(result, "results", None) or []
        if not pages:
            return ""
        lines = [f"# Synthesis: {question}", ""]
        for p in pages[:8]:
            title = getattr(p, "title", None) or (p.get("title") if isinstance(p, dict) else "")
            slug = getattr(p, "slug", None) or (p.get("slug") if isinstance(p, dict) else "")
            lines.append(f"- [[{slug or title}]] — {title}")
        return "\n".join(lines)
    except Exception:
        return ""


async def _publish(wf_id: str, write_queue: Any, workflow: str, question: str, content: str) -> None:
    """Persist the synthesized page through the WriteQueue."""
    if write_queue is None:
        return
    from saw.domain.value_objects import WriteOpStatus
    from saw.write_queue.queue import WriteOp

    slug = f"workflow-{wf_id[:8]}"
    op = WriteOp(
        op_id=f"workflow-{wf_id}",
        session_id=f"workflow-{wf_id}",
        sink_name="wiki",
        payload={
            "op": "write",
            "path": f"{slug}.md",
            "slug": f"{slug}.md",
            "title": f"Workflow: {question}",
            "content": content,
            "entity_type": "note",
            "properties": {"workflow": workflow, "workflow_id": wf_id},
        },
        status=WriteOpStatus.PENDING,
    )
    write_queue.enqueue_atomic([op])
    await _broadcast("page_updated", {"slug": f"{slug}.md"})


@router.post("/workflows")
async def execute_workflow(
    workflow: str = Query("knowledge_review", description="Workflow name"),
    params: dict[str, Any] | None = None,
    request: Request = None,
):
    """Launch a multi-agent workflow.

    Runs the workflow asynchronously (background task) and returns
    immediately with the workflow id. Progress is streamed over WebSocket
    as ``workflow_progress`` and ``agent_status`` messages.
    """
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
        "started_at": _utcnow_iso(),
    }

    query = getattr(request.app.state, "query", None) if request else None
    write_queue = getattr(request.app.state, "write_queue", None) if request else None

    # Prefer a real CollaborateEngine when one is configured (team mode).
    collaborate = getattr(request.app.state, "collaborate", None) if request else None
    if collaborate is not None and hasattr(collaborate, "execute_workflow_definition"):
        # Delegate to the engine in the background; it emits its own events.
        task = asyncio.create_task(_run_via_engine(collaborate, wf_id, workflow, params or {}))
    else:
        task = asyncio.create_task(_run_workflow(wf_id, query, write_queue, workflow, params or {}))
    # Keep a strong reference so the task is not garbage-collected mid-run.
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return {
        "workflow_id": wf_id,
        "status": "running",
        "steps_total": len(steps),
        "steps_completed": 0,
        "status_url": f"/api/v1/workflows/{wf_id}/status",
    }


async def _run_via_engine(engine: Any, wf_id: str, workflow: str, params: dict[str, Any]) -> None:
    """Delegate to a real CollaborateEngine (team mode).

    ``CollaborateEngine`` exposes ``execute_workflow(path, inputs)`` (and
    ``execute_workflow_definition``); it has no ``execute`` method, so the
    previous ``hasattr(engine, "execute")`` guard always skipped the call
    and silently marked the workflow ``completed``. We now resolve the
    workflow name to a YAML definition file and run it for real; if no
    definition can be found the workflow is marked **failed** (not
    completed) so the caller sees the truth.
    """
    try:
        from pathlib import Path

        candidates = [
            Path("workflows") / f"{workflow}.yaml",
            Path("workflows") / f"{workflow}.yml",
            Path(".saw/workflows") / f"{workflow}.yaml",
            Path(".saw/workflows") / f"{workflow}.yml",
        ]
        workflow_path = next((p for p in candidates if p.is_file()), None)
        if workflow_path is None:
            raise FileNotFoundError(
                f"No workflow definition found for '{workflow}' "
                f"(looked in: {', '.join(str(c) for c in candidates)})"
            )

        result = await engine.execute_workflow(workflow_path, params or {})
        status = getattr(result, "status", "completed")
        if status == "completed":
            _workflows[wf_id]["status"] = "completed"
        else:
            _workflows[wf_id]["status"] = "failed"
            errors = getattr(result, "errors", []) or [status]
            _workflows[wf_id]["error"] = "; ".join(str(e) for e in errors)
        _workflows[wf_id]["completed_at"] = _utcnow_iso()
    except Exception as e:
        logger.warning("Engine workflow %s failed: %s", wf_id, e)
        _workflows[wf_id]["status"] = "failed"
        _workflows[wf_id]["error"] = str(e)
        _workflows[wf_id]["completed_at"] = _utcnow_iso()


@router.get("/workflows")
async def list_workflows() -> dict[str, Any]:
    """List recent workflows (newest first)."""
    items = sorted(
        _workflows.values(),
        key=lambda w: w.get("started_at", ""),
        reverse=True,
    )
    return {"workflows": items[:20], "total": len(_workflows)}


@router.get("/workflows/{workflow_id}/status")
async def workflow_status(
    workflow_id: str = Path(..., description="Workflow UUID"),
):
    """Get workflow execution status (per api_contract §5.6)."""
    wf = _workflows.get(workflow_id)
    if wf is None:
        raise HTTPException(404, f"Workflow '{workflow_id}' not found")
    return wf

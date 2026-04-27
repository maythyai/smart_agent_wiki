"""MCP tools for learning operations.

Per 02-03 Task 2: Learn tools (5 tools: saw_status, saw_learn, saw_distill,
saw_suggest, saw_wip).
"""
from __future__ import annotations

from typing import Any

from saw.drivers.mcp.server import mcp

# Global references (set during initialization)
_learn_engine = None


def init_learn_tools(learn_engine) -> None:
    """Initialize learn tools with engine reference.

    Args:
        learn_engine: LearnEngine instance.
    """
    global _learn_engine
    _learn_engine = learn_engine


@mcp.tool
async def saw_status() -> dict[str, Any]:
    """Get knowledge base status overview.

    Returns:
        Status overview with page counts, claim counts, and freshness summary.
    """
    result = {
        "total_pages": 0,
        "total_claims": 0,
        "total_entities": 0,
        "freshness": {},
        "training_progress": {},
        "version": "1.0.0",
    }

    if _learn_engine is None:
        result["error"] = "Learn engine not initialized"
        return result

    try:
        # Get training progress
        result["training_progress"] = _learn_engine.get_training_progress()

        # In production, would get actual counts from repos
        # For now, return basic status
    except Exception as e:
        result["error"] = str(e)

    return result


@mcp.tool
async def saw_learn() -> dict[str, Any]:
    """Trigger learning/adaptation cycle.

    Returns:
        Learning report with preferences learned, SOPs extracted, etc.
    """
    result = {
        "preferences_learned": 0,
        "sops_extracted": 0,
        "gaps_detected": 0,
        "review_queue_size": 0,
        "duration_ms": 0,
        "version": "1.0.0",
    }

    if _learn_engine is None:
        result["error"] = "Learn engine not initialized"
        return result

    try:
        import time
        start = time.time()

        report = _learn_engine.run_daily_learning()
        result["preferences_learned"] = report.preferences_learned
        result["sops_extracted"] = report.sops_extracted
        result["gaps_detected"] = report.gaps_detected
        result["review_queue_size"] = report.review_queue_size
        result["duration_ms"] = int((time.time() - start) * 1000)
    except Exception as e:
        result["error"] = str(e)

    return result


@mcp.tool
async def saw_distill() -> list[dict]:
    """Trigger cognitive distillation for SOP extraction.

    Returns:
        List of extracted SOPs with patterns.
    """
    results = []

    if _learn_engine is None:
        return [{"error": "Learn engine not initialized"}]

    try:
        if _learn_engine._distiller:
            # Run distillation on approved patterns
            approved_file = _learn_engine._feedback_dir / "approved.yaml"
            if approved_file.is_file():
                sops = _learn_engine._distiller.run_distillation(approved_file)
                for sop in sops:
                    results.append({
                        "name": sop.name,
                        "pattern": sop.pattern,
                        "context": sop.context,
                        "version": "1.0.0",
                    })
    except Exception as e:
        results = [{"error": str(e)}]

    return results


@mcp.tool
async def saw_suggest() -> list[dict]:
    """Get improvement suggestions.

    Returns:
        List of suggestions for knowledge base improvement.
    """
    results = []

    if _learn_engine is None:
        return [{"error": "Learn engine not initialized"}]

    try:
        # Get review queue as suggestions
        queue = _learn_engine.get_review_queue()
        for item in queue[:10]:  # Top 10 items
            results.append({
                "type": "review",
                "page_path": item.page_path,
                "priority": item.priority,
                "reason": item.reason,
                "version": "1.0.0",
            })

        # Get gap suggestions if trends senser available
        if _learn_engine._trends:
            gaps = _learn_engine._trends.detect_gaps()
            for gap in gaps[:5]:  # Top 5 gaps
                results.append({
                    "type": "gap",
                    "topic": gap.topic,
                    "query_count": gap.query_count,
                    "coverage": gap.coverage,
                    "version": "1.0.0",
                })
    except Exception as e:
        results = [{"error": str(e)}]

    return results


@mcp.tool
async def saw_wip(action: str = "read", updates: dict[str, Any] | None = None) -> dict[str, Any]:
    """Read or update cross-session work momentum.

    Args:
        action: Action to perform: "read" or "update".
        updates: Updates to apply (only for "update" action).

    Returns:
        Current WIP state.
    """
    result = {
        "action": action,
        "active_tasks": [],
        "next_steps": [],
        "pending_questions": [],
        "last_session": None,
        "version": "1.0.0",
    }

    if _learn_engine is None:
        result["error"] = "Learn engine not initialized"
        return result

    try:
        wip_file = _learn_engine._settings.path / ".saw" / "wip.yaml"

        if action == "update" and updates:
            import yaml
            import time

            # Load existing
            wip_data: dict[str, Any] = {}
            if wip_file.is_file():
                with open(wip_file, encoding="utf-8") as f:
                    wip_data = yaml.safe_load(f) or {}

            # Apply updates
            for key, value in updates.items():
                if value is None:
                    wip_data.pop(key, None)
                else:
                    wip_data[key] = value

            wip_data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            # Write back
            wip_file.parent.mkdir(parents=True, exist_ok=True)
            with open(wip_file, "w", encoding="utf-8") as f:
                yaml.dump(wip_data, f, default_flow_style=False)

        # Read current state
        if wip_file.is_file():
            import yaml

            with open(wip_file, encoding="utf-8") as f:
                wip_data = yaml.safe_load(f) or {}
            result["active_tasks"] = wip_data.get("active_tasks", [])
            result["next_steps"] = wip_data.get("next_steps", [])
            result["pending_questions"] = wip_data.get("pending_questions", [])
            result["last_session"] = wip_data.get("updated_at")
    except Exception as e:
        result["error"] = str(e)

    return result
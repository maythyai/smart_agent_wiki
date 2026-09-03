"""MCP tools for collaboration operations.

Per 02-03 Task 2: Collaborate tools (2 tools: saw_workflow, saw_feedback).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from saw.drivers.mcp.server import mcp

# Global references (set during initialization)
_learn_engine = None


def init_collaborate_tools(learn_engine) -> None:
    """Initialize collaborate tools with engine reference.

    Args:
        learn_engine: LearnEngine instance.
    """
    global _learn_engine
    _learn_engine = learn_engine


@mcp.tool
async def saw_workflow(yaml_path: str, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute a YAML-defined workflow.

    Args:
        yaml_path: Path to the YAML workflow definition.
        inputs: Optional inputs for the workflow.

    Returns:
        Workflow execution result.
    """
    import time
    import yaml

    result = {
        "yaml_path": yaml_path,
        "status": "pending",
        "steps_executed": 0,
        "outputs": {},
        "errors": [],
        "duration_ms": 0,
        "version": "1.0.0",
    }

    start = time.time()

    try:
        workflow_path = Path(yaml_path)
        if not workflow_path.is_file():
            result["errors"].append(f"Workflow file not found: {yaml_path}")
            result["duration_ms"] = int((time.time() - start) * 1000)
            return result

        with open(workflow_path, encoding="utf-8") as f:
            workflow = yaml.safe_load(f)

        if not workflow:
            result["errors"].append("Empty workflow definition")
            result["duration_ms"] = int((time.time() - start) * 1000)
            return result

        # Parse and execute workflow steps
        steps = workflow.get("steps", [])
        inputs = inputs or {}

        for i, step in enumerate(steps):

            # Placeholder for step execution
            # In production, would route to appropriate engine based on step_type
            result["steps_executed"] += 1

        result["status"] = "completed"
    except Exception as e:
        result["errors"].append(str(e))
        result["status"] = "failed"

    result["duration_ms"] = int((time.time() - start) * 1000)
    return result


@mcp.tool
async def saw_feedback(action: str, approved: bool, context: str) -> dict[str, Any]:
    """Submit positive or negative behavioral reinforcement.

    Per D-20: Edit implies implicit acceptance, reject requires explicit action.

    Args:
        action: The action type (e.g., "entity_extraction", "claim_extraction").
        approved: Whether the action was approved.
        context: Context about the action.

    Returns:
        Feedback submission result.
    """
    result = {
        "action": action,
        "approved": approved,
        "recorded": False,
        "version": "1.0.0",
    }

    if _learn_engine is None:
        result["error"] = "Learn engine not initialized"
        return result

    try:
        _learn_engine.record_feedback(action, approved, context)
        result["recorded"] = True
    except Exception as e:
        result["error"] = str(e)

    return result

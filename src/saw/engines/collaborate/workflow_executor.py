"""Workflow executor for YAML-based multi-agent orchestration.

Per PLAN.md Task 3: WorkflowExecutor executes steps with gates and fallbacks.
Per PITFALLS.md Pitfall 10: Deadlock prevention via timeout.
Per PITFALLS.md Pitfall 17: Gate loop prevention via max_retries.
Per D-09: Gate conditions support confidence, contradiction_count, freshness.
"""
from __future__ import annotations

import asyncio
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .workflow_parser import WorkflowDefinition, WorkflowParser, WorkflowStep

if TYPE_CHECKING:
    from .a2a_protocol import A2AAdapter
    from .dispatcher import AgentDispatcher
    from ..govern.governor import Governor

logger = logging.getLogger(__name__)


@dataclass
class GateResult:
    """Result of gate condition evaluation.

    Per D-09: Gate conditions support confidence, contradiction_count, freshness.
    """

    passed: bool
    reason: str | None = None
    value: Any = None
    expected: Any = None


@dataclass
class WorkflowResult:
    """Result of workflow execution.

    Contains execution status, outputs, and timing information.
    """

    workflow_id: str
    name: str
    status: str  # "running", "completed", "failed", "timeout"
    steps_completed: int
    steps_total: int
    outputs: dict[str, Any]
    errors: list[str]
    start_time: datetime
    end_time: datetime | None = None


class WorkflowExecutor:
    """YAML workflow executor with gate checking and fallback handling.

    Per PITFALLS.md Pitfall 10: Workflow timeout prevents deadlock.
    Per PITFALLS.md Pitfall 17: max_retries prevents infinite loops.
    """

    def __init__(
        self,
        dispatcher: AgentDispatcher,
        a2a_adapter: A2AAdapter,
        governor: Governor | None,
        event_bus: Any | None = None,
        conn: Any = None,
    ) -> None:
        """Initialize workflow executor.

        Args:
            dispatcher: Agent dispatcher for task execution
            a2a_adapter: A2A adapter for agent communication
            governor: Governance engine (optional, for confidence checks)
            event_bus: Event bus for progress publishing (optional)
            conn: Optional sqlite3 connection for durable execution state
                (HI-9: crash recovery). When None, execution is in-memory only.
        """
        self._dispatcher = dispatcher
        self._a2a = a2a_adapter
        self._governor = governor
        self._event_bus = event_bus
        self._conn = conn
        self._parser = WorkflowParser()

    async def execute(
        self,
        workflow_path: Path,
        inputs: dict[str, Any],
    ) -> WorkflowResult:
        """Execute a YAML workflow file.

        Args:
            workflow_path: Path to workflow YAML file
            inputs: Input context for workflow

        Returns:
            WorkflowResult with execution status and outputs
        """
        workflow_def = self._parser.parse(workflow_path)
        return await self.execute_definition(workflow_def, inputs)

    async def execute_definition(
        self,
        workflow: WorkflowDefinition,
        inputs: dict[str, Any],
    ) -> WorkflowResult:
        """Execute a workflow definition.

        Per PITFALLS.md Pitfall 10: Timeout prevents infinite execution.

        Args:
            workflow: Parsed workflow definition
            inputs: Input context for workflow

        Returns:
            WorkflowResult with execution status and outputs
        """
        workflow_id = str(uuid.uuid4())
        context = dict(inputs)  # Copy inputs as initial context
        steps_completed = 0
        errors: list[str] = []
        outputs: dict[str, Any] = {}

        start_time = datetime.now(timezone.utc)

        # HI-9: record the execution as 'running' so a crash leaves a stranded
        # row that startup recovery can detect (instead of silent loss).
        self._persist_workflow(
            workflow_id, workflow.name, "running", 0, len(workflow.steps), []
        )

        # Publish workflow start event
        await self._publish_event({
            "type": "WorkflowStarted",
            "workflow_id": workflow_id,
            "name": workflow.name,
        })

        # Execute with timeout
        try:
            async with asyncio.timeout(workflow.timeout):
                for step in workflow.steps:
                    step_result = await self._execute_step(
                        workflow_id, step, context, workflow
                    )

                    if step_result.get("skipped"):
                        continue

                    if step_result.get("failed"):
                        errors.extend(step_result.get("errors", []))
                        if workflow.on_failure == "abort":
                            break

                    steps_completed += 1

        except asyncio.TimeoutError:
            errors.append(f"Workflow timeout after {workflow.timeout}s")
            self._persist_workflow(
                workflow_id, workflow.name, "timeout",
                steps_completed, len(workflow.steps), errors,
            )
            return WorkflowResult(
                workflow_id=workflow_id,
                name=workflow.name,
                status="timeout",
                steps_completed=steps_completed,
                steps_total=len(workflow.steps),
                outputs=outputs,
                errors=errors,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
            )

        # Collect outputs (context values not in original inputs)
        for key in context:
            if key not in inputs:
                outputs[key] = context[key]

        status = "completed" if not errors else "failed"
        end_time = datetime.now(timezone.utc)

        self._persist_workflow(
            workflow_id, workflow.name, status,
            steps_completed, len(workflow.steps), errors,
        )

        # Publish workflow complete event
        await self._publish_event({
            "type": "WorkflowCompleted",
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": status,
        })

        return WorkflowResult(
            workflow_id=workflow_id,
            name=workflow.name,
            status=status,
            steps_completed=steps_completed,
            steps_total=len(workflow.steps),
            outputs=outputs,
            errors=errors,
            start_time=start_time,
            end_time=end_time,
        )

    async def _execute_step(
        self,
        workflow_id: str,
        step: WorkflowStep,
        context: dict[str, Any],
        workflow: WorkflowDefinition,
    ) -> dict[str, Any]:
        """Execute a single workflow step.

        Per PITFALLS.md Pitfall 17: max_retries prevents infinite retry loops.

        Args:
            workflow_id: ID of the workflow execution
            step: Step to execute
            context: Execution context (modified in place)
            workflow: Parent workflow definition

        Returns:
            Dict with execution result (success, failed, skipped)
        """
        # Check condition
        if step.condition and not self._eval_condition(step.condition, context):
            return {"skipped": True}

        retry_count = 0
        last_error: str | None = None

        while retry_count <= step.max_retries:
            # Check gate (pre-execution)
            # WR-03: Gate failure should directly execute fallback action, not retry
            # Retrying without state change leads to infinite loop until max_retries exhausted
            if step.gates:
                gate_result = await self._check_gates(step.gates, context)
                if not gate_result.passed:
                    return await self._handle_gate_failure(step, gate_result, context)

            # Execute Agent
            try:
                from saw.domain.agent import AgentTask, AgentContext

                task = AgentTask(
                    type=step.action,
                    payload=context.get(step.input_key, {}),
                )
                agent_context = AgentContext(
                    wiki_state={},
                    claims_context=[],
                    workflow_id=workflow_id,
                )

                result = await self._dispatcher.dispatch(
                    step.agent, task, agent_context
                )

                if result.success:
                    context[step.output_key] = result.payload

                    # Publish step complete event
                    await self._publish_event({
                        "type": "WorkflowStep",
                        "workflow_id": workflow_id,
                        "step": f"{step.agent}.{step.action}",
                        "status": "completed",
                        "output_key": step.output_key,
                    })

                    return {"success": True}
                else:
                    last_error = result.error
                    retry_count += 1

            except Exception as e:
                last_error = str(e)
                retry_count += 1
                logger.error(f"Step {step.agent}.{step.action} failed: {e}")

        # Max retries exceeded
        return {
            "failed": True,
            "errors": [
                f"Step {step.agent}.{step.action} failed after {step.max_retries} retries: {last_error}"
            ],
        }

    async def _check_gates(
        self, gates: list[dict[str, str]], context: dict[str, Any]
    ) -> GateResult:
        """Evaluate gate conditions.

        Per D-09: Supports confidence, contradiction_count, freshness conditions.

        Args:
            gates: List of gate conditions
            context: Execution context with gate values

        Returns:
            GateResult with pass/fail status
        """
        for gate in gates:
            for key, condition in gate.items():
                value = context.get(key)

                # Parse condition
                match = re.match(r"^(>=|<=|==|!=|>|<)\s*(\d+)$", condition)
                if not match:
                    return GateResult(
                        passed=False, reason=f"Invalid condition: {condition}"
                    )

                op, expected = match.groups()
                expected = int(expected)

                # Evaluate condition
                passed = self._eval_operator(value, op, expected)

                if not passed:
                    return GateResult(
                        passed=False,
                        reason=f"{key}={value} failed condition {condition}",
                        value=value,
                        expected=expected,
                    )

        return GateResult(passed=True)

    def _eval_operator(self, value: Any, op: str, expected: Any) -> bool:
        """Evaluate comparison operator.

        Args:
            value: Actual value
            op: Operator string (>=, <=, ==, !=, >, <)
            expected: Expected value

        Returns:
            True if condition is satisfied
        """
        if value is None:
            return False

        ops = {
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
        }
        return ops[op](value, expected)

    async def _handle_gate_failure(
        self,
        step: WorkflowStep,
        gate_result: GateResult,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle gate failure with fallback action.

        Per PITFALLS.md Pitfall 17: Fallback actions prevent infinite loops.

        Args:
            step: Failed step
            gate_result: Gate evaluation result
            context: Execution context (modified for flagged results)

        Returns:
            Dict with failure handling result
        """
        if step.fallback_action == "accept_with_flag":
            context[f"{step.output_key}_flagged"] = True
            return {
                "success": True,
                "flagged": True,
                "reason": gate_result.reason,
            }
        elif step.fallback_action == "escalate_to_human":
            return {
                "failed": True,
                "errors": [f"Gate failed, requires human review: {gate_result.reason}"],
                "needs_review": True,
            }
        else:  # abort
            return {
                "failed": True,
                "errors": [f"Gate failed: {gate_result.reason}"],
            }

    def _eval_condition(self, condition: str, context: dict[str, Any]) -> bool:
        """Evaluate a conditional expression to a native bool.

        Uses ``jinja2.Environment.compile_expression`` so the result is a real
        Python value (bool/int/None), not the string ``"True"``/``"False"``.
        The previous ``bool(Template(...).render(...))`` was *always* truthy
        because ``bool("False") == True`` (any non-empty string is truthy),
        so step conditions never skipped — conditional branching was
        silently broken (HI-8).
        """
        try:
            from jinja2 import Environment

            env = Environment()
            expr = env.compile_expression(condition)
            return bool(expr(**context))
        except Exception as e:
            # WR-08: Log condition evaluation failures for debugging
            logger.warning(f"Condition evaluation failed: {condition}, error: {e}")
            return False

    async def _publish_event(self, event: dict[str, Any]) -> None:
        """Publish event to event bus.

        Args:
            event: Event dictionary to publish
        """
        if self._event_bus and hasattr(self._event_bus, "publish"):
            await self._event_bus.publish(event)
        logger.debug(f"Workflow event: {event}")

    def _persist_workflow(
        self,
        workflow_id: str,
        name: str,
        status: str,
        steps_completed: int,
        steps_total: int,
        errors: list[str] | None = None,
    ) -> None:
        """HI-9: upsert workflow execution state for crash recovery.

        When a process dies mid-workflow the row is left at status='running';
        startup recovery (lifespan) marks such rows 'interrupted' so they are
        visible rather than silently lost. No-op when no connection was wired.
        """
        if self._conn is None:
            return
        import json as _json

        now = datetime.now(timezone.utc).isoformat()
        try:
            with self._conn:
                self._conn.execute(
                    """INSERT INTO workflow_executions
                       (workflow_id, definition_name, status, steps_completed,
                        steps_total, errors_json, updated_at, finished_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(workflow_id) DO UPDATE SET
                         status=excluded.status,
                         steps_completed=excluded.steps_completed,
                         steps_total=excluded.steps_total,
                         errors_json=excluded.errors_json,
                         updated_at=excluded.updated_at,
                         finished_at=excluded.finished_at""",
                    (
                        workflow_id,
                        name,
                        status,
                        steps_completed,
                        steps_total,
                        _json.dumps(errors or []),
                        now,
                        now if status in ("completed", "failed", "timeout", "interrupted") else None,
                    ),
                )
        except Exception:
            # Persistence must never break workflow execution.
            pass

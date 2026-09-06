"""Agent activity aggregation via event bus subscription.

ADR-015 决策二: event_bus subscriber writes in-memory counters.
Handler runs on publisher thread (sync), ``_dispatch`` has try/except —
lightweight O(1) dict update, no lock needed (single-thread).

The tracker subscribes to ``WorkflowStep`` events published by
``WorkflowExecutor._execute_step`` (workflow_executor.py) and aggregates
per-agent call/failure/last-action counters in memory. Data is lost on
process restart (PRD §3.3 rule 6 — not persisted).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class AgentActivityTracker:
    """Aggregate agent activity by subscribing to WorkflowStep events.

    In-memory only — process restart loses all data (PRD §3.3 rule 6).
    Handler is lightweight (dict counter update), does not block workflow.
    """

    def __init__(self) -> None:
        self._activities: dict[str, dict[str, Any]] = {}

    def subscribe(self, event_bus: Any) -> None:
        """Register as subscriber for WorkflowStep events.

        Args:
            event_bus: An object with ``add_subscriber(event_type, handler)``
                (e.g. :class:`InMemoryEventBus`).
        """
        event_bus.add_subscriber("WorkflowStep", self._handle_event)

    def _handle_event(self, event: dict[str, Any]) -> None:
        """Handle WorkflowStep event — update agent activity counters.

        Event format (from workflow_executor.py ``_execute_step``):
        ``{"type":"WorkflowStep","workflow_id":...,"step":"{agent}.{action}",
        "status":"completed"|"failed","output_key":...}``
        """
        try:
            step_str = event.get("step", "")
            if "." not in step_str:
                return
            agent_name, action = step_str.split(".", 1)
            status = event.get("status", "completed")

            now = datetime.now(timezone.utc).isoformat()

            if agent_name not in self._activities:
                self._activities[agent_name] = {
                    "calls": 0,
                    "failures": 0,
                    "last_action": None,
                    "last_active_at": None,
                }

            activity = self._activities[agent_name]
            if status == "completed":
                activity["calls"] += 1
            elif status == "failed":
                activity["failures"] += 1

            activity["last_action"] = action
            activity["last_active_at"] = now
        except Exception:
            # Handler must never raise — _dispatch already has try/except,
            # but double-guard for safety.
            logger.warning("Activity tracker handler error", exc_info=True)

    def get_activity(self, agent_name: str) -> dict[str, Any]:
        """Get activity aggregation for a specific agent.

        Returns empty activity (calls=0) if agent has no activity.
        """
        if agent_name not in self._activities:
            return {
                "agent": agent_name,
                "calls": 0,
                "failures": 0,
                "last_action": None,
                "last_active_at": None,
            }
        activity = self._activities[agent_name]
        return {
            "agent": agent_name,
            "calls": activity["calls"],
            "failures": activity["failures"],
            "last_action": activity["last_action"],
            "last_active_at": activity["last_active_at"],
        }

    def get_summary(self, agent_name: str) -> dict[str, Any] | None:
        """Get compact activity summary for roster (calls + last_active_at).

        Returns ``None`` if agent has no activity.
        """
        if agent_name not in self._activities:
            return None
        activity = self._activities[agent_name]
        return {
            "calls": activity["calls"],
            "last_active_at": activity["last_active_at"],
        }

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

    def __init__(self, conn: Any = None) -> None:
        """Initialize activity tracker.

        Args:
            conn: Optional SQLite connection for durable persistence
                (AUDIT-F-05 / v1.31.0). When set, each event write-throughs
                to the ``agent_activity`` table and ``load()`` is called so
                counters survive restart. None (CLI/test) → in-memory only
                (legacy behaviour).
        """
        self._activities: dict[str, dict[str, Any]] = {}
        self._conn = conn
        if conn is not None:
            self.load()

    def attach_conn(self, conn: Any) -> None:
        """Attach a SQLite connection post-construction and load state.

        Used by the ``saw web`` lifespan which creates the tracker before
        the write-queue/connection is available, then attaches once the
        shared ``conn`` is known. Idempotent + safe to call multiple times.
        """
        self._conn = conn
        self.load()

    def load(self) -> int:
        """Load persisted activity counts from ``agent_activity``.

        Merges DB rows into the in-memory dict (DB wins on overlap so the
        durable store is authoritative after restart). Returns the number
        of agents loaded. No-op when no connection is attached.
        """
        if self._conn is None:
            return 0
        try:
            rows = self._conn.execute(
                "SELECT agent_name, calls, failures, last_action, "
                "last_active_at FROM agent_activity"
            ).fetchall()
        except Exception:
            # Table may not exist yet (pre-migration) — degrade to empty.
            return 0
        for name, calls, failures, last_action, last_active_at in rows:
            self._activities[name] = {
                "calls": calls,
                "failures": failures,
                "last_action": last_action,
                "last_active_at": last_active_at,
            }
        return len(rows)

    def _persist(self, agent_name: str) -> None:
        """Upsert one agent's activity to ``agent_activity`` (best-effort)."""
        if self._conn is None:
            return
        activity = self._activities.get(agent_name)
        if activity is None:
            return
        try:
            self._conn.execute(
                "INSERT INTO agent_activity "
                "(agent_name, calls, failures, last_action, last_active_at, "
                "updated_at) VALUES (?, ?, ?, ?, ?, datetime('now')) "
                "ON CONFLICT(agent_name) DO UPDATE SET "
                "calls=excluded.calls, failures=excluded.failures, "
                "last_action=excluded.last_action, "
                "last_active_at=excluded.last_active_at, "
                "updated_at=datetime('now')",
                (
                    agent_name,
                    activity["calls"],
                    activity["failures"],
                    activity["last_action"],
                    activity["last_active_at"],
                ),
            )
            # Commit is owned by the caller's connection lifecycle; in the
            # web runtime the shared conn autocommits per-execute. For safety
            # in contexts that need it, best-effort commit.
            if hasattr(self._conn, "commit"):
                self._conn.commit()
        except Exception:
            logger.warning(
                "Activity persist failed for %s", agent_name, exc_info=True
            )

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
            # AUDIT-F-05 (v1.31.0): write-through to durable store so
            # counters survive restart. Best-effort; never blocks the event.
            self._persist(agent_name)
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


# ── Process-global singleton accessor (T4) ──────────────────────────
# Canonical home for the activity-tracker singleton so the CLI and REST
# routes don't have to import from saw.drivers.web.app (which created a
# fragile CLI→web coupling). ``saw web``'s lifespan calls set_activity_tracker()
# on startup; CLI-only mode / tests leave it None and callers degrade to
# empty activity.
_tracker: "AgentActivityTracker | None" = None


def get_activity_tracker() -> "AgentActivityTracker | None":
    """Return the process-global activity tracker, or None if unset."""
    return _tracker


def set_activity_tracker(tracker: "AgentActivityTracker | None") -> None:
    """Set the process-global activity tracker (called by the web lifespan)."""
    global _tracker  # noqa: PLW0603
    _tracker = tracker

"""Agent activity aggregation tests — T-F-T-3 (AC-C-1/2).

Tests the ``AgentActivityTracker`` class: event handling, in-memory
counters, and empty-activity responses. All tests use mock events —
no real workflow execution, no LLM calls.
"""
from __future__ import annotations


def test_ac_c_1_event_aggregation() -> None:
    """AC-C-1: publish WorkflowStep event → tracker aggregates calls +
    last_action + last_active_at."""
    from saw.engines.collaborate.activity_tracker import AgentActivityTracker

    tracker = AgentActivityTracker()

    # Simulate a WorkflowStep event (as published by workflow_executor.py)
    tracker._handle_event({
        "type": "WorkflowStep",
        "workflow_id": "wf-001",
        "step": "Scholar.synthesize",
        "status": "completed",
        "output_key": "synthesis",
    })

    activity = tracker.get_activity("Scholar")
    assert activity["agent"] == "Scholar"
    assert activity["calls"] == 1
    assert activity["failures"] == 0
    assert activity["last_action"] == "synthesize"
    assert activity["last_active_at"] is not None


def test_ac_c_1_multiple_events_increment_counter() -> None:
    """AC-C-1 (variant): 3 completed events → calls == 3."""
    from saw.engines.collaborate.activity_tracker import AgentActivityTracker

    tracker = AgentActivityTracker()
    for _ in range(3):
        tracker._handle_event({
            "type": "WorkflowStep",
            "step": "Librarian.search",
            "status": "completed",
        })

    activity = tracker.get_activity("Librarian")
    assert activity["calls"] == 3
    assert activity["last_action"] == "search"


def test_ac_c_1_failed_event_increments_failures() -> None:
    """AC-C-1 (variant): failed status increments failures, not calls."""
    from saw.engines.collaborate.activity_tracker import AgentActivityTracker

    tracker = AgentActivityTracker()
    tracker._handle_event({
        "type": "WorkflowStep",
        "step": "Critic.review",
        "status": "failed",
    })

    activity = tracker.get_activity("Critic")
    assert activity["calls"] == 0
    assert activity["failures"] == 1
    assert activity["last_action"] == "review"


def test_ac_c_2_no_activity_returns_empty() -> None:
    """AC-C-2: tracker.get_activity('Guardian') with no Guardian events →
    calls=0, last_active_at=None."""
    from saw.engines.collaborate.activity_tracker import AgentActivityTracker

    tracker = AgentActivityTracker()
    # Publish a Scholar event (not Guardian)
    tracker._handle_event({
        "type": "WorkflowStep",
        "step": "Scholar.synthesize",
        "status": "completed",
    })

    # Guardian has no activity
    activity = tracker.get_activity("Guardian")
    assert activity["agent"] == "Guardian"
    assert activity["calls"] == 0
    assert activity["failures"] == 0
    assert activity["last_action"] is None
    assert activity["last_active_at"] is None


def test_ac_c_2_get_summary_none_for_no_activity() -> None:
    """AC-C-2 (variant): get_summary returns None when agent has no activity."""
    from saw.engines.collaborate.activity_tracker import AgentActivityTracker

    tracker = AgentActivityTracker()
    assert tracker.get_summary("Guardian") is None


def test_ac_c_2_get_summary_returns_compact_for_active_agent() -> None:
    """AC-C-2 (variant): get_summary returns {calls, last_active_at}."""
    from saw.engines.collaborate.activity_tracker import AgentActivityTracker

    tracker = AgentActivityTracker()
    tracker._handle_event({
        "type": "WorkflowStep",
        "step": "Scholar.synthesize",
        "status": "completed",
    })

    summary = tracker.get_summary("Scholar")
    assert summary is not None
    assert summary["calls"] == 1
    assert summary["last_active_at"] is not None


def test_subscribe_registers_with_event_bus() -> None:
    """Subscribe calls event_bus.add_subscriber('WorkflowStep', handler)."""
    from saw.engines.collaborate.activity_tracker import AgentActivityTracker

    class MockBus:
        def __init__(self):
            self.registrations = []

        def add_subscriber(self, event_type, handler):
            self.registrations.append((event_type, handler))

    bus = MockBus()
    tracker = AgentActivityTracker()
    tracker.subscribe(bus)

    assert len(bus.registrations) == 1
    assert bus.registrations[0][0] == "WorkflowStep"
    # The handler should be the tracker's _handle_event
    assert bus.registrations[0][1] == tracker._handle_event

    # Verify the registered handler works
    bus.registrations[0][1]({
        "type": "WorkflowStep",
        "step": "Writer.publish",
        "status": "completed",
    })
    assert tracker.get_activity("Writer")["calls"] == 1


def test_handler_never_raises_on_bad_event() -> None:
    """Handler swallows exceptions (double-guard with _dispatch try/except)."""
    from saw.engines.collaborate.activity_tracker import AgentActivityTracker

    tracker = AgentActivityTracker()
    # Malformed events should not raise
    tracker._handle_event({})  # no step key
    tracker._handle_event({"step": "no-dot"})  # no dot separator
    tracker._handle_event({"step": None})  # None step
    # No activity recorded for any agent
    assert tracker.get_activity("Librarian")["calls"] == 0

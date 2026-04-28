"""Agent domain types - data classes for agent operations.

Per PLAN.md Task 1: AgentTask, AgentContext, AgentResult definitions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentTask:
    """Task to be executed by an agent.

    Per D-15: A2A message payload structure.
    """

    type: str
    payload: dict[str, Any]
    correlation_id: str | None = None


@dataclass(frozen=True)
class AgentContext:
    """Execution context for an agent.

    Contains wiki state, claims context, workflow tracking.

    Per T-03-01-02: frozen=True prevents tampering with context during transfer.
    """

    wiki_state: dict[str, Any]
    claims_context: list[dict[str, Any]]
    workflow_id: str | None = None
    calling_agent: str | None = None


@dataclass
class AgentResult:
    """Result from an agent execution.

    Per D-06: Confidence maps to ConfidenceLevel (0-4).
    """

    success: bool
    payload: dict[str, Any]
    confidence: int = 0  # 0-4 mapping to ConfidenceLevel
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
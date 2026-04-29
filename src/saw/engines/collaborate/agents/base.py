"""Base agent implementation.

Per PLAN.md Task 1: BaseAgent class with common agent behavior.
Per D-02: Agent role definition includes name, model_tier, system_prompt, tools_allowed.
"""
from __future__ import annotations

import json
from typing import Literal

from saw.domain.agent import AgentContext, AgentTask


class BaseAgent:
    """Base class for specialized agents.

    Provides common functionality for all agent implementations.
    """

    def __init__(
        self,
        name: str,
        model_tier: Literal["haiku", "sonnet", "opus", "rule"],
        system_prompt: str,
        tools_allowed: list[str],
        constraints: dict | None = None,
    ) -> None:
        """Initialize the agent.

        Args:
            name: Agent role name.
            model_tier: LLM tier to use for this agent.
            system_prompt: System prompt for the agent.
            tools_allowed: List of tool names this agent can use.
            constraints: Optional constraints on agent behavior.
        """
        self._name = name
        self._model_tier = model_tier
        self._system_prompt = system_prompt
        self._tools_allowed = tools_allowed
        self._constraints = constraints or {}

    @property
    def name(self) -> str:
        """Agent role name."""
        return self._name

    @property
    def model_tier(self) -> Literal["haiku", "sonnet", "opus", "rule"]:
        """Model tier for this agent."""
        return self._model_tier

    def _build_messages(self, task: AgentTask, context: AgentContext) -> list[dict]:
        """Build message list for LLM completion.

        Args:
            task: The task to execute.
            context: Execution context.

        Returns:
            List of messages for LLM completion.
        """
        return [
            {"role": "system", "content": self._system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "task_type": task.type,
                        "payload": task.payload,
                        "context": {
                            "workflow_id": context.workflow_id,
                            "calling_agent": context.calling_agent,
                        },
                    }
                ),
            },
        ]

    async def execute(
        self,
        task: AgentTask,
        context: AgentContext,
        tools: list,
    ) -> "AgentResult":
        """Execute a task. Subclasses should override this.

        WR-07: The 'tools' parameter is currently unused in base implementation.
        Future versions may support tool execution. Subclasses may ignore this
        parameter if they don't need tool support.

        Args:
            task: The task to execute.
            context: Execution context.
            tools: Available tools (reserved for future tool execution support).

        Returns:
            AgentResult (base implementation returns empty success).
        """
        from saw.domain.agent import AgentResult

        return AgentResult(
            success=True,
            payload={},
            confidence=0,
            metadata={"agent": self._name},
        )
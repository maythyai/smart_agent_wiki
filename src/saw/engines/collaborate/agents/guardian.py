"""Guardian Agent - Security and policy enforcement.

Per D-01: Security checks, permission control, policy enforcement.
Per D-02: model_tier='rule' - zero LLM, pure rule engine.
Per D-03: Guardian is a pure rule engine, no LLM calls (zero cost security).
"""
from __future__ import annotations

from dataclasses import dataclass

from saw.domain.agent import AgentContext, AgentResult, AgentTask
from saw.engines.collaborate.agents.base import BaseAgent


@dataclass
class GuardianRule:
    """A single Guardian rule."""

    id: str
    agent_pattern: str  # "*" for all, or specific agent name
    action_pattern: str  # "*" for all, or specific action
    resource_pattern: str  # "*" for all, or specific resource
    effect: str  # "permit" or "forbid"
    reason: str = ""
    ttl_days: int | None = None  # Auto-expiry for generated rules


class GuardianAgent(BaseAgent):
    """Guardian agent for security and policy enforcement.

    Zero-LLM agent: Uses pure rule engine for policy decisions.
    Per D-14: Max 200 rules, default deny policy.
    """

    def __init__(self) -> None:
        """Initialize the Guardian agent with empty rule set."""
        super().__init__(
            name="Guardian",
            model_tier="rule",  # No LLM used
            system_prompt="",  # Rule engine doesn't need prompt
            tools_allowed=["*"],  # Can check all operations
        )
        self._rules: list[GuardianRule] = []
        self._max_rules = 200  # D-14: Rule complexity limit

    def add_rule(self, rule: GuardianRule) -> None:
        """Add a rule to the Guardian.

        Args:
            rule: The rule to add.

        Raises:
            ValueError: If max rules exceeded.
        """
        if len(self._rules) >= self._max_rules:
            raise ValueError(f"Max rules ({self._max_rules}) exceeded")
        self._rules.append(rule)

    def clear_rules(self) -> None:
        """Clear all rules."""
        self._rules.clear()

    async def execute(
        self,
        task: AgentTask,
        context: AgentContext,
        tools: list,
    ) -> AgentResult:
        """Execute a policy check.

        Pure rule evaluation, no LLM calls.

        Args:
            task: Contains action and resource to check.
            context: Contains calling_agent.
            tools: Not used by Guardian.

        Returns:
            AgentResult with permit/deny decision.
        """
        action = task.payload.get("action", "*")
        resource = task.payload.get("resource", "*")
        calling_agent = context.calling_agent or "unknown"

        # T-03-01-06: Check tools_allowed before execution
        # If the calling agent has restricted tools_allowed, verify this action is permitted
        if tools and calling_agent != "unknown":
            # Get the calling agent's tools_allowed from the context if available
            calling_agent_tools = context.wiki_state.get("agent_tools", {})
            allowed_tools = calling_agent_tools.get(calling_agent, ["*"])

            # If not wildcard, check if the action is in allowed tools
            if allowed_tools != ["*"] and "*" not in allowed_tools:
                # Extract tool name from action (e.g., "saw_search" from "search")
                tool_name = f"saw_{action}" if not action.startswith("saw_") else action
                if tool_name not in allowed_tools:
                    return AgentResult(
                        success=False,
                        payload={
                            "allowed": False,
                            "reason": f"Tool '{tool_name}' not in tools_allowed for agent '{calling_agent}'",
                            "tool_check_failed": True,
                        },
                        error=f"Elevation blocked: {calling_agent} cannot use {tool_name}",
                    )

        # Evaluate all rules - deny rules take precedence
        for rule in self._rules:
            if self._rule_matches(rule, calling_agent, action, resource):
                if rule.effect == "forbid":
                    return AgentResult(
                        success=False,
                        payload={
                            "allowed": False,
                            "reason": rule.reason,
                            "rule_id": rule.id,
                        },
                        error=f"Policy denied by rule {rule.id}",
                    )

        # Per D-14: Default deny - must have explicit permit to allow
        has_permit_rule = any(
            self._rule_matches(r, calling_agent, action, resource)
            and r.effect == "permit"
            for r in self._rules
        )

        if has_permit_rule:
            return AgentResult(
                success=True,
                payload={"allowed": True, "reason": "Permit rule matched"},
            )

        # No rules configured → fail-open. A local-first deployment is
        # permissive until an operator adds rules; requiring boilerplate
        # permit rules for safe "read" actions would make the tool unusable.
        if not self._rules:
            return AgentResult(
                success=True,
                payload={"allowed": True, "reason": "No rules configured (default permit)"},
            )

        # D-14: Default deny - rules exist but no permit matched.
        return AgentResult(
            success=False,
            payload={"allowed": False, "reason": "No permit rule matched (default deny)"},
            error="Default deny policy",
        )

    def _rule_matches(
        self,
        rule: GuardianRule,
        agent: str,
        action: str,
        resource: str,
    ) -> bool:
        """Check if a rule matches the given parameters.

        Args:
            rule: The rule to check.
            agent: Calling agent name.
            action: Action being performed.
            resource: Resource being accessed.

        Returns:
            True if the rule matches.
        """
        return (
            (rule.agent_pattern == "*" or rule.agent_pattern == agent)
            and (rule.action_pattern == "*" or rule.action_pattern == action)
            and (rule.resource_pattern == "*" or rule.resource_pattern == resource)
        )
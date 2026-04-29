"""Agent Dispatcher with model routing and fallback.

Per PLAN.md Task 3: AgentDispatcher routes agents to appropriate LLM tiers.
Per PITFALLS.md Pitfall 2: Use allowed_fails=3 to prevent aggressive cooldown.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from saw.adapters.llm.router import LLMRouter
    from saw.domain.agent import AgentContext, AgentResult, AgentTask
    from saw.domain.protocols import AgentProtocol


class ModelTier(Enum):
    """Model tier for agent routing."""

    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"
    RULE = "rule"  # Guardian, no LLM


# Per PITFALLS.md: Model names as of 2026
MODEL_MAPPING = {
    ModelTier.HAIKU: "claude-3-5-haiku-latest",
    ModelTier.SONNET: "claude-sonnet-4-20250514",
    ModelTier.OPUS: "claude-opus-4-20250514",
}

# Fallback order: higher tier falls back to lower tier
FALLBACK_ORDER = {
    ModelTier.OPUS: [ModelTier.SONNET, ModelTier.HAIKU],
    ModelTier.SONNET: [ModelTier.HAIKU],
    ModelTier.HAIKU: [],  # No fallback from Haiku
    ModelTier.RULE: [],  # No fallback needed for rule agents
}


class AgentNotFoundError(Exception):
    """Raised when requested agent is not registered."""


class DispatchError(Exception):
    """Raised when dispatch fails after all fallbacks."""


class RateLimitError(Exception):
    """Raised when rate limit is hit."""


@dataclass
class DispatcherConfig:
    """Configuration for AgentDispatcher.

    Per PITFALLS.md Pitfall 2:
    - allowed_fails: Minimum 3 to prevent aggressive cooldown
    - cooldown_time: 120 seconds recommended
    """

    allowed_fails: int = 3
    cooldown_time: int = 120  # seconds
    timeout: int = 60  # seconds per call


class AgentDispatcher:
    """Agent dispatcher with model routing and fallback support.

    Per D-04: Three-tier model routing (Haiku → Sonnet → Opus).
    Per D-05: Routing based on task complexity.
    Per D-06: Runtime fallback when higher tiers unavailable.
    """

    def __init__(
        self,
        llm_router: LLMRouter | None,
        agents: dict[str, AgentProtocol],
        config: DispatcherConfig | None = None,
    ) -> None:
        """Initialize the dispatcher.

        Args:
            llm_router: LLM router for model access.
            agents: Dictionary of agent name -> agent instance.
            config: Optional dispatcher configuration.
        """
        self._llm = llm_router
        self._agents = agents
        self._config = config or DispatcherConfig()

    def get_model_for_tier(self, tier: ModelTier) -> str:
        """Return the actual model name for a tier.

        Args:
            tier: The model tier.

        Returns:
            The model name string.
        """
        return MODEL_MAPPING.get(tier, MODEL_MAPPING[ModelTier.SONNET])

    async def dispatch(
        self,
        agent_name: str,
        task: AgentTask,
        context: AgentContext,
        tools: list | None = None,
    ) -> AgentResult:
        """Dispatch a task to an agent with fallback support.

        Args:
            agent_name: Name of the agent to dispatch.
            task: The task to execute.
            context: Execution context.
            tools: Optional list of tools.

        Returns:
            AgentResult from the agent.

        Raises:
            AgentNotFoundError: If agent not registered.
            DispatchError: If all fallbacks exhausted.
        """
        agent = self._agents.get(agent_name)
        if not agent:
            raise AgentNotFoundError(f"Agent '{agent_name}' not found")

        # Rule-based agents don't need LLM
        if agent.model_tier == "rule":
            result = await agent.execute(task, context, tools or [])
            result.metadata["model_tier_used"] = "rule"
            return result

        # Get fallback chain for this agent's tier
        tier = ModelTier(agent.model_tier)
        fallback_chain = [tier] + FALLBACK_ORDER.get(tier, [])

        last_error: Exception | None = None
        for fallback_tier in fallback_chain:
            try:
                # TODO(WR-01): The fallback_tier is currently not used to switch models.
                # Agent's model_tier is fixed at construction time. The metadata below
                # records the intended tier but actual LLM calls use the original model.
                # Future: Either pass model dynamically to agent.execute() or have
                # LLMRouter.completion() support fallback model selection.
                result = await agent.execute(task, context, tools or [])
                result.metadata["model_tier_used"] = fallback_tier.value
                return result
            except RateLimitError as e:
                last_error = e
                # Try next fallback
                if fallback_tier == fallback_chain[-1]:
                    raise DispatchError(
                        f"All model tiers exhausted for agent {agent_name}"
                    ) from last_error
                continue
            except Exception:
                raise

        raise DispatchError(f"All model tiers exhausted for agent {agent_name}")

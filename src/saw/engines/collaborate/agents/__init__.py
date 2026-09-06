"""Agent implementations for collaboration engine."""
from __future__ import annotations

from typing import TYPE_CHECKING

from saw.engines.collaborate.agents.base import BaseAgent
from saw.engines.collaborate.agents.critic import CriticAgent, CRITIC_PROMPT
from saw.engines.collaborate.agents.guardian import GuardianAgent, GuardianRule
from saw.engines.collaborate.agents.librarian import LibrarianAgent, LIBRARIAN_PROMPT
from saw.engines.collaborate.agents.linker import LinkerAgent, LINKER_PROMPT
from saw.engines.collaborate.agents.scholar import ScholarAgent, SCHOLAR_PROMPT
from saw.engines.collaborate.agents.writer import WriterAgent, WRITER_PROMPT

if TYPE_CHECKING:
    from saw.adapters.llm.router import LLMRouter

__all__ = [
    "BaseAgent",
    "CriticAgent",
    "CRITIC_PROMPT",
    "GuardianAgent",
    "GuardianRule",
    "LibrarianAgent",
    "LIBRARIAN_PROMPT",
    "LinkerAgent",
    "LINKER_PROMPT",
    "ScholarAgent",
    "SCHOLAR_PROMPT",
    "WriterAgent",
    "WRITER_PROMPT",
    "build_default_agents",
    "load_custom_agents",
    "build_agent_roster",
]


def build_default_agents(
    llm_router: "LLMRouter | None",
    feedback_engine=None,
) -> dict[str, BaseAgent]:
    """Construct the full 6-agent roster keyed by agent name.

    Args:
        llm_router: Shared LLM router (None enables heuristic fallbacks).
        feedback_engine: Optional FeedbackEngine. When provided, Critic opens
            KnowledgeIssues on detected contradictions and Scholar submits
            ChangeRequests for proposed page updates.

    Returns:
        Dict mapping agent name -> agent instance, ready for AgentDispatcher.
    """
    critic = CriticAgent(llm_router, feedback_engine=feedback_engine)
    scholar = ScholarAgent(llm_router, feedback_engine=feedback_engine)
    return {
        "Librarian": LibrarianAgent(llm_router),
        "Writer": WriterAgent(llm_router),
        "Critic": critic,
        "Linker": LinkerAgent(llm_router),
        "Scholar": scholar,
        "Guardian": GuardianAgent(),
    }


_BUILTIN_AGENT_NAMES = frozenset({
    "Librarian", "Writer", "Critic", "Linker", "Scholar", "Guardian",
})
_VALID_MODEL_TIERS = frozenset({"haiku", "sonnet", "opus", "rule"})


def load_custom_agents(
    llm_router: "LLMRouter | None",
    agents_dir: "Path | None" = None,
) -> dict[str, BaseAgent]:
    """Scan ``.saw/agents/*.yaml`` and build custom agent instances.

    Additive to :func:`build_default_agents` — does not modify it.
    Invalid definitions are skipped with a warning, never blocking startup.
    The ``.saw/agents/`` directory not existing is a normal degradation (only
    built-in agents are returned).
    """
    import logging
    from pathlib import Path

    import yaml

    logger = logging.getLogger(__name__)
    if agents_dir is None:
        agents_dir = Path(".saw/agents")

    custom: dict[str, BaseAgent] = {}
    if not agents_dir.is_dir():
        return custom  # no .saw/agents/ → only built-in agents

    for yaml_file in sorted(agents_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                logger.warning(
                    "Agent definition '%s' is not a mapping, skipped", yaml_file
                )
                continue
        except (yaml.YAMLError, OSError) as e:
            logger.error(
                "Failed to parse agent definition '%s': %s", yaml_file, e
            )
            continue

        name = data.get("name", "")
        if not name or name in _BUILTIN_AGENT_NAMES:
            logger.warning(
                "Agent role '%s' conflicts with built-in, skipped", name
            )
            continue

        model_tier = data.get("model_tier", "")
        if model_tier not in _VALID_MODEL_TIERS:
            logger.warning(
                "Invalid model_tier '%s' for agent '%s', "
                "must be haiku/sonnet/opus/rule",
                model_tier, name,
            )
            continue

        system_prompt = data.get("system_prompt", "")
        if not system_prompt or not system_prompt.strip():
            logger.warning(
                "Agent '%s' missing system_prompt, skipped", name
            )
            continue

        tools_allowed = data.get("tools_allowed", [])
        if not isinstance(tools_allowed, list):
            logger.warning(
                "tools_allowed for '%s' is not a list, defaulting to []", name
            )
            tools_allowed = []

        constraints = data.get("constraints", {})
        if not isinstance(constraints, dict):
            constraints = {}

        custom[name] = BaseAgent(
            name=name,
            model_tier=model_tier,
            system_prompt=system_prompt,
            tools_allowed=tools_allowed,
            constraints=constraints or None,
        )
        logger.info("Loaded custom agent '%s' from %s", name, yaml_file)

    return custom


def build_agent_roster(
    llm_router: "LLMRouter | None",
    feedback_engine=None,
) -> dict[str, BaseAgent]:
    """Build the full agent roster: built-in 6 + custom from ``.saw/agents/*.yaml``.

    Additive merge — :func:`build_default_agents` is called unchanged, then
    custom agents are merged in. Built-in agents are never overwritten.
    """
    roster = build_default_agents(llm_router, feedback_engine=feedback_engine)
    custom = load_custom_agents(llm_router)
    roster.update(custom)  # custom agents added additively
    return roster
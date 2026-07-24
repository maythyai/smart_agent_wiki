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
"""Agent implementations for collaboration engine."""
from saw.engines.collaborate.agents.base import BaseAgent
from saw.engines.collaborate.agents.critic import CriticAgent, CRITIC_PROMPT
from saw.engines.collaborate.agents.guardian import GuardianAgent, GuardianRule
from saw.engines.collaborate.agents.librarian import LibrarianAgent, LIBRARIAN_PROMPT
from saw.engines.collaborate.agents.linker import LinkerAgent, LINKER_PROMPT
from saw.engines.collaborate.agents.scholar import ScholarAgent, SCHOLAR_PROMPT
from saw.engines.collaborate.agents.writer import WriterAgent, WRITER_PROMPT

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
]
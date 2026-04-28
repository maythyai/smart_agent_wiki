"""Collaboration engine - multi-agent orchestration.

Per D-01: 6 specialized agents with role-specific behavior.
"""
from saw.engines.collaborate.orchestrator import CollaborateEngine, CollaborateConfig
from saw.engines.collaborate.dispatcher import (
    AgentDispatcher,
    AgentNotFoundError,
    DispatchError,
    DispatcherConfig,
    ModelTier,
    RateLimitError,
)
from saw.engines.collaborate.workflow_parser import (
    WorkflowParser,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowParseError,
)
from saw.engines.collaborate.workflow_executor import (
    WorkflowExecutor,
    WorkflowResult,
    GateResult,
)
from saw.engines.collaborate.a2a_protocol import (
    A2A_PROTOCOL_VERSION,
    A2AAdapter,
    A2AMessage,
    A2AResult,
    MessageType,
)
from saw.engines.collaborate.agents.base import BaseAgent
from saw.domain.protocols import AgentProtocol
from saw.engines.collaborate.agents.librarian import LibrarianAgent
from saw.engines.collaborate.agents.writer import WriterAgent
from saw.engines.collaborate.agents.critic import CriticAgent
from saw.engines.collaborate.agents.linker import LinkerAgent
from saw.engines.collaborate.agents.scholar import ScholarAgent
from saw.engines.collaborate.agents.guardian import GuardianAgent
from saw.domain.agent import AgentTask, AgentContext, AgentResult

__all__ = [
    # Orchestrator
    "CollaborateEngine",
    "CollaborateConfig",
    # Dispatcher
    "AgentDispatcher",
    "AgentNotFoundError",
    "DispatchError",
    "DispatcherConfig",
    "ModelTier",
    "RateLimitError",
    # Workflow Parser
    "WorkflowParser",
    "WorkflowDefinition",
    "WorkflowStep",
    "WorkflowParseError",
    # Workflow Executor
    "WorkflowExecutor",
    "WorkflowResult",
    "GateResult",
    # A2A Protocol
    "A2A_PROTOCOL_VERSION",
    "A2AAdapter",
    "A2AMessage",
    "A2AResult",
    "MessageType",
    # Agents
    "AgentProtocol",
    "BaseAgent",
    "AgentTask",
    "AgentContext",
    "AgentResult",
    "LibrarianAgent",
    "WriterAgent",
    "CriticAgent",
    "LinkerAgent",
    "ScholarAgent",
    "GuardianAgent",
]

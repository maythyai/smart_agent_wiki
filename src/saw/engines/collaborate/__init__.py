"""Collaboration engine - multi-agent orchestration.

Per D-01: 6 specialized agents with role-specific behavior.
"""
from saw.engines.collaborate.a2a_protocol import (
    A2A_PROTOCOL_VERSION,
    A2AAdapter,
    A2AMessage,
    A2AResult,
    MessageType,
)
from saw.engines.collaborate.agents.base import BaseAgent
from saw.engines.collaborate.dispatcher import (
    AgentDispatcher,
    AgentNotFoundError,
    DispatchError,
    DispatcherConfig,
    ModelTier,
    RateLimitError,
)

__all__ = [
    "A2A_PROTOCOL_VERSION",
    "A2AAdapter",
    "A2AMessage",
    "A2AResult",
    "BaseAgent",
    "AgentDispatcher",
    "AgentNotFoundError",
    "DispatchError",
    "DispatcherConfig",
    "MessageType",
    "ModelTier",
    "RateLimitError",
]
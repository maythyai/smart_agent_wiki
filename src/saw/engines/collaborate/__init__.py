"""Collaboration engine - multi-agent orchestration.

Per D-01: 6 specialized agents with role-specific behavior.
"""
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
    "BaseAgent",
    "AgentDispatcher",
    "AgentNotFoundError",
    "DispatchError",
    "DispatcherConfig",
    "ModelTier",
    "RateLimitError",
]
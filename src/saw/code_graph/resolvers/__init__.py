"""Language-specific resolvers for framework semantics."""

from saw.code_graph.resolvers.base import BaseResolver
from saw.code_graph.resolvers.registry import ResolverRegistry, get_resolver

__all__ = ["BaseResolver", "ResolverRegistry", "get_resolver"]

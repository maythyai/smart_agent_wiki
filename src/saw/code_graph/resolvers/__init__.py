"""Language-specific resolvers for framework semantics."""

from saw.code_graph.resolvers.base import BaseResolver
from saw.code_graph.resolvers.registry import ResolverRegistry, get_resolver, register_resolver
from saw.code_graph.resolvers.python_resolver import PythonResolver

# 自动注册内置 Resolver
register_resolver(PythonResolver())

__all__ = ["BaseResolver", "ResolverRegistry", "get_resolver", "register_resolver", "PythonResolver"]

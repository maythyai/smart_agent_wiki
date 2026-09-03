"""Resolver 注册表 — 按语言/框架分发"""

from __future__ import annotations


from saw.code_graph.resolvers.base import BaseResolver


class ResolverRegistry:
    """Resolver 注册表

    管理所有已注册的 Resolver，按语言分发。
    """

    def __init__(self):
        self._resolvers: dict[str, list[BaseResolver]] = {}

    def register(self, resolver: BaseResolver) -> None:
        """注册一个 Resolver"""
        lang = resolver.language
        if lang not in self._resolvers:
            self._resolvers[lang] = []
        self._resolvers[lang].append(resolver)

    def get_resolvers(self, language: str) -> list[BaseResolver]:
        """获取指定语言的所有 Resolver"""
        return self._resolvers.get(language, [])

    def has_resolvers(self, language: str) -> bool:
        """是否有该语言的 Resolver"""
        return language in self._resolvers and len(self._resolvers[language]) > 0


# 全局注册表
_registry = ResolverRegistry()


def get_resolver(language: str) -> list[BaseResolver]:
    """获取指定语言的 Resolver 列表"""
    return _registry.get_resolvers(language)


def register_resolver(resolver: BaseResolver) -> None:
    """注册 Resolver 到全局注册表"""
    _registry.register(resolver)

"""Resolver 基类 — 语言/框架特化解析接口"""

from __future__ import annotations

from abc import ABC, abstractmethod

from saw.code_graph.models import CodeNode, ParseResult


class BaseResolver(ABC):
    """语言/框架特化解析器基类

    Resolver 在通用 AST 解析之后运行，负责:
    1. 解析框架特有的调用语义 (e.g., Spring DI, FastAPI Depends)
    2. 解析装饰器/注解驱动的隐式关系
    3. 将裸名边解析为完整 UID (证据门控)

    子类实现:
    - python_resolver.py: FastAPI/Flask 路由、装饰器语义
    - typescript_resolver.py: tsconfig paths、re-exports
    - java_resolver.py: Spring DI、注解驱动
    """

    @property
    @abstractmethod
    def language(self) -> str:
        """该 Resolver 适用的语言"""
        ...

    @abstractmethod
    def resolve(self, result: ParseResult, all_nodes: dict[str, CodeNode]) -> ParseResult:
        """对 ParseResult 进行后处理解析

        Args:
            result: 通用解析器的输出
            all_nodes: 当前已知的所有节点 (uid → CodeNode)，用于跨文件解析

        Returns:
            增强后的 ParseResult (可能新增/修改边)
        """
        ...

    def can_resolve(self, node: CodeNode) -> bool:
        """判断该 Resolver 是否能处理此节点"""
        return node.language == self.language

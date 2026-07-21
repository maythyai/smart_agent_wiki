"""Python Resolver — FastAPI/Flask 装饰器语义解析

解析框架特有的隐式关系:
- @app.route / @router.get → ENDPOINT 节点 + 路由元数据
- @app.dependency / Depends() → DEPENDS_ON 边
- @pytest.fixture → TEST 依赖
- dataclass / pydantic BaseModel → 字段 REFERENCES
"""

from __future__ import annotations

import logging
from typing import Optional

from saw.code_graph.models import (
    CodeEdge,
    CodeNode,
    EdgeType,
    NodeKind,
    ConfidenceTier,
    ParseResult,
)
from saw.code_graph.resolvers.base import BaseResolver

logger = logging.getLogger(__name__)

# FastAPI/Flask 路由装饰器
ROUTE_DECORATORS = {
    "route", "get", "post", "put", "delete", "patch",
    "api_route", "websocket", "options", "head",
}

# 测试框架装饰器
TEST_DECORATORS = {
    "fixture", "test", "parametrize", "mark",
}


class PythonResolver(BaseResolver):
    """Python 框架特化解析器

    在通用 AST 解析之后运行，增强:
    1. 路由装饰器 → ENDPOINT 标记 + HTTP method 元数据
    2. Depends() 调用 → DEPENDS_ON 边
    3. 测试 fixture → TESTED_BY 关系推断
    """

    @property
    def language(self) -> str:
        return "python"

    def resolve(self, result: ParseResult, all_nodes: dict[str, CodeNode]) -> ParseResult:
        """增强 ParseResult"""
        self._resolve_endpoints(result)
        self._resolve_dependencies(result)
        return result

    def _resolve_endpoints(self, result: ParseResult) -> None:
        """识别路由装饰器，标记为 ENDPOINT"""
        for node in result.nodes:
            if node.kind in (NodeKind.FUNCTION, NodeKind.METHOD):
                metadata = node.metadata or {}
                decorators = metadata.get("decorators", [])

                for dec in decorators:
                    dec_lower = dec.lower()
                    # 匹配 @app.get, @router.post, @app.route 等
                    if any(f".{route}" in dec_lower for route in ROUTE_DECORATORS):
                        node.kind = NodeKind.ENDPOINT
                        # 提取 HTTP method
                        for route in ROUTE_DECORATORS:
                            if f".{route}" in dec_lower:
                                node.metadata["http_method"] = route.upper()
                                break
                        break

    def _resolve_dependencies(self, result: ParseResult) -> None:
        """识别 Depends() 调用，生成 DEPENDS_ON 边"""
        for edge in result.edges:
            if edge.edge_type == EdgeType.CALLS:
                # 如果调用名是 Depends，升级为 DEPENDS_ON
                if edge.metadata.get("bare_name") and "depend" in edge.target.lower():
                    edge.edge_type = EdgeType.DEPENDS_ON
                    edge.confidence = 0.8
                    edge.confidence_tier = ConfidenceTier.INFERRED

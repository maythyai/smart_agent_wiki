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
    ConfidenceTier,
    ParseResult,
)
from saw.code_graph.resolvers.base import BaseResolver

logger = logging.getLogger(__name__)

# FastAPI/Flask 路由装饰器 (reserved for future tree-sitter resolver)
ROUTE_DECORATORS = {
    "route", "get", "post", "put", "delete", "patch",
    "api_route", "websocket", "options", "head",
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
        self._resolve_dependencies(result)
        return result

    def _resolve_dependencies(self, result: ParseResult) -> None:
        """识别 Depends() 调用，生成 DEPENDS_ON 边"""
        for edge in result.edges:
            if edge.edge_type == EdgeType.CALLS:
                # 如果调用名是 Depends，升级为 DEPENDS_ON
                if edge.metadata.get("bare_name") and "depend" in edge.target.lower():
                    edge.edge_type = EdgeType.DEPENDS_ON
                    edge.confidence = 0.8
                    edge.confidence_tier = ConfidenceTier.INFERRED

"""Code Graph 数据模型 — 节点、边、枚举类型定义"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class NodeKind(str, Enum):
    """代码符号类型"""

    FILE = "file"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    TYPE = "type"
    VARIABLE = "variable"
    CONSTANT = "constant"
    TEST = "test"
    CONFIG = "config"
    ENDPOINT = "endpoint"


class EdgeType(str, Enum):
    """代码关系类型"""

    CALLS = "CALLS"
    IMPORTS = "IMPORTS"
    INHERITS = "INHERITS"
    IMPLEMENTS = "IMPLEMENTS"
    CONTAINS = "CONTAINS"
    TESTED_BY = "TESTED_BY"
    REFERENCES = "REFERENCES"
    OVERRIDES = "OVERRIDES"
    DEPENDS_ON = "DEPENDS_ON"


class ConfidenceTier(str, Enum):
    """边置信度层级"""

    EXTRACTED = "EXTRACTED"  # AST 精确提取, confidence = 1.0
    RESOLVED = "RESOLVED"  # 跨文件解析确认, confidence 0.8-0.99
    INFERRED = "INFERRED"  # 启发式推断, confidence < 0.8


# 边类型权重（影响分析用）
EDGE_WEIGHTS: dict[EdgeType, float] = {
    EdgeType.CALLS: 1.0,
    EdgeType.INHERITS: 0.9,
    EdgeType.IMPLEMENTS: 0.85,
    EdgeType.IMPORTS: 0.7,
    EdgeType.TESTED_BY: 0.6,
    EdgeType.REFERENCES: 0.4,
    EdgeType.OVERRIDES: 0.8,
    EdgeType.DEPENDS_ON: 0.6,
    EdgeType.CONTAINS: 0.3,
}

# 深度衰减因子
DEPTH_DECAY = 0.85
# 影响分析分数地板
SCORE_FLOOR = 0.05


def make_uid(file_path: str, qualified_name: str) -> str:
    """生成确定性节点 UID (SCIP-style moniker)

    格式: "{relative_file_path}::{qualified_name}"
    重索引时 upsert 语义，不产生重复。
    """
    return f"{file_path}::{qualified_name}"


def content_hash(content: str) -> str:
    """计算内容 SHA-256 哈希（增量检测用）"""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


@dataclass
class CodeNode:
    """代码符号节点"""

    uid: str
    name: str
    kind: NodeKind
    file_path: str
    language: str
    start_line: int = 0
    end_line: int = 0
    signature: str = ""
    parameters: list[str] = field(default_factory=list)
    docstring: Optional[str] = None
    content_hash: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        """序列化为 dict（兼容现有 analysis 模块接口）"""
        return {
            "uid": self.uid,
            "name": self.name,
            "kind": self.kind.value,
            "filePath": self.file_path,
            "language": self.language,
            "startLine": self.start_line,
            "endLine": self.end_line,
            "signature": self.signature,
            "parameters": self.parameters,
            "docstring": self.docstring,
            "content_hash": self.content_hash,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CodeNode":
        """从 dict 反序列化"""
        return cls(
            uid=data["uid"],
            name=data["name"],
            kind=NodeKind(data.get("kind", "function")),
            file_path=data.get("filePath", data.get("file_path", "")),
            language=data.get("language", ""),
            start_line=data.get("startLine", data.get("start_line", 0)),
            end_line=data.get("endLine", data.get("end_line", 0)),
            signature=data.get("signature", ""),
            parameters=data.get("parameters", []),
            docstring=data.get("docstring"),
            content_hash=data.get("content_hash", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CodeEdge:
    """代码关系边"""

    source: str
    target: str
    edge_type: EdgeType
    confidence: float = 1.0
    confidence_tier: ConfidenceTier = ConfidenceTier.EXTRACTED
    metadata: dict = field(default_factory=dict)

    @property
    def weight(self) -> float:
        """影响分析权重"""
        return EDGE_WEIGHTS.get(self.edge_type, 0.5) * self.confidence

    def to_dict(self) -> dict:
        """序列化为 dict（兼容现有 analysis 模块接口）"""
        return {
            "source": self.source,
            "target": self.target,
            "type": self.edge_type.value,
            "confidence": self.confidence,
            "confidence_tier": self.confidence_tier.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CodeEdge":
        """从 dict 反序列化"""
        return cls(
            source=data["source"],
            target=data["target"],
            edge_type=EdgeType(data.get("type", data.get("edge_type", "CALLS"))),
            confidence=data.get("confidence", 1.0),
            confidence_tier=ConfidenceTier(
                data.get("confidence_tier", "EXTRACTED")
            ),
            metadata=data.get("metadata", {}),
        )


@dataclass
class FileTracking:
    """文件追踪记录（增量更新用）"""

    file_path: str
    content_hash: str
    last_parsed_at: str = ""
    node_count: int = 0
    edge_count: int = 0


@dataclass
class GraphSnapshot:
    """图快照元数据"""

    snapshot_id: str
    created_at: str
    trigger: str  # 'full_build' | 'incremental' | 'manual'
    node_count: int = 0
    edge_count: int = 0
    files_changed: int = 0


@dataclass
class ParseResult:
    """单文件解析结果"""

    file_path: str
    language: str
    nodes: list[CodeNode] = field(default_factory=list)
    edges: list[CodeEdge] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    parse_time_ms: float = 0.0


@dataclass
class BuildResult:
    """构建结果"""

    total_files: int = 0
    files_parsed: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    total_nodes: int = 0
    total_edges: int = 0
    build_time_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    snapshot_id: Optional[str] = None


@dataclass
class ImpactScore:
    """影响分析评分节点"""

    uid: str
    name: str
    kind: str
    file_path: str
    score: float
    depth: int
    edge_type: str
    risk_level: str  # WILL_BREAK | LIKELY_AFFECTED | MAY_NEED_TESTING

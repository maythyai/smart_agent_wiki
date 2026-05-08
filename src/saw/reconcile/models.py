"""
Reconcile Engine 数据模型

定义 Bi-Temporal Facts 和矛盾检测相关数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ResolutionStrategyType(Enum):
    """解决策略类型"""
    FRESHNESS_WINS = "freshness_wins"      # 新数据优先
    CONFIDENCE_WINS = "confidence_wins"     # 高置信度优先
    SOURCE_DIVERSITY = "source_diversity"   # 多来源一致优先
    MANUAL = "manual"                       # 手动解决


class ContradictionType(Enum):
    """矛盾类型"""
    DIRECT = "direct"              # 直接矛盾：A vs !A
    TEMPORAL = "temporal"          # 时间矛盾：同主题不同时间的陈述
    CONFIDENCE = "confidence"      # 置信度矛盾：同事实不同置信度
    PARTIAL = "partial"            # 部分矛盾：有交集但不完全冲突


class FactStatus(Enum):
    """事实状态"""
    ACTIVE = "active"              # 当前有效
    SUPERSEDED = "superseded"      # 被取代
    DISPUTED = "disputed"          # 存在争议
    RESOLVED = "resolved"          # 已解决


@dataclass
class BiTemporalFact:
    """
    Bi-Temporal Fact - 双时态事实

    追踪'何时为真'和'何时得知'，完整审计知识演变

    Attributes:
        fact_id: 事实唯一标识
        content: 事实内容
        topic: 主题/实体
        valid_from: 事实何时开始为真
        valid_until: 事实何时不再为真（None 表示仍然有效）
        learned_at: Vault 何时得知此事实
        source: 来源标识
        confidence: 置信度 (1-4)
        status: 当前状态
    """
    fact_id: str
    content: str
    topic: str
    valid_from: datetime
    valid_until: Optional[datetime] = None
    learned_at: datetime = field(default_factory=datetime.now)
    source: str = ""
    confidence: int = 1
    status: FactStatus = FactStatus.ACTIVE
    metadata: dict = field(default_factory=dict)

    def is_valid_at(self, dt: datetime) -> bool:
        """检查在指定时间是否有效"""
        if self.valid_from > dt:
            return False
        if self.valid_until and self.valid_until < dt:
            return False
        return True

    def is_current(self) -> bool:
        """检查是否当前有效"""
        return self.is_valid_at(datetime.now())

    def supersede(self, superseded_at: Optional[datetime] = None) -> None:
        """标记为被取代"""
        self.valid_until = superseded_at or datetime.now()
        self.status = FactStatus.SUPERSEDED

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "fact_id": self.fact_id,
            "content": self.content,
            "topic": self.topic,
            "valid_from": self.valid_from.isoformat(),
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "learned_at": self.learned_at.isoformat(),
            "source": self.source,
            "confidence": self.confidence,
            "status": self.status.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BiTemporalFact":
        """从字典创建"""
        return cls(
            fact_id=data["fact_id"],
            content=data["content"],
            topic=data["topic"],
            valid_from=datetime.fromisoformat(data["valid_from"]),
            valid_until=datetime.fromisoformat(data["valid_until"]) if data.get("valid_until") else None,
            learned_at=datetime.fromisoformat(data["learned_at"]) if data.get("learned_at") else datetime.now(),
            source=data.get("source", ""),
            confidence=data.get("confidence", 1),
            status=FactStatus(data.get("status", "active")),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Contradiction:
    """
    矛盾记录

    记录检测到的矛盾及其状态
    """
    contradiction_id: str
    contradiction_type: ContradictionType
    topic: str
    fact_a: BiTemporalFact
    fact_b: BiTemporalFact
    detected_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_strategy: Optional[ResolutionStrategyType] = None
    winner: Optional[str] = None  # fact_id of winner
    resolution_reason: str = ""

    def describe(self) -> str:
        """描述矛盾"""
        return (
            f"Contradiction on '{self.topic}':\n"
            f"  A: {self.fact_a.content[:100]}...\n"
            f"  B: {self.fact_b.content[:100]}...\n"
            f"  Type: {self.contradiction_type.value}"
        )

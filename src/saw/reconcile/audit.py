"""
Audit Logger - 审计日志器

记录矛盾解决过程的完整审计
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


from .models import (
    Contradiction,
)
from .strategies import ResolutionResult


@dataclass
class AuditEntry:
    """
    审计条目

    记录一次矛盾解决的完整过程
    """
    audit_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    contradiction_id: str = ""
    contradiction_type: str = ""
    topic: str = ""

    # 原始矛盾双方
    fact_a_id: str = ""
    fact_a_content: str = ""
    fact_a_source: str = ""
    fact_a_confidence: int = 1
    fact_a_learned_at: Optional[datetime] = None

    fact_b_id: str = ""
    fact_b_content: str = ""
    fact_b_source: str = ""
    fact_b_confidence: int = 1
    fact_b_learned_at: Optional[datetime] = None

    # 解决结果
    resolution_strategy: str = ""
    winner_id: str = ""
    loser_id: str = ""
    resolution_reason: str = ""
    confidence_score: float = 0.0

    # 后续操作
    loser_superseded_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "audit_id": self.audit_id,
            "timestamp": self.timestamp.isoformat(),
            "contradiction_id": self.contradiction_id,
            "contradiction_type": self.contradiction_type,
            "topic": self.topic,
            "fact_a": {
                "id": self.fact_a_id,
                "content": self.fact_a_content[:200],
                "source": self.fact_a_source,
                "confidence": self.fact_a_confidence,
                "learned_at": self.fact_a_learned_at.isoformat() if self.fact_a_learned_at else None,
            },
            "fact_b": {
                "id": self.fact_b_id,
                "content": self.fact_b_content[:200],
                "source": self.fact_b_source,
                "confidence": self.fact_b_confidence,
                "learned_at": self.fact_b_learned_at.isoformat() if self.fact_b_learned_at else None,
            },
            "resolution": {
                "strategy": self.resolution_strategy,
                "winner_id": self.winner_id,
                "loser_id": self.loser_id,
                "reason": self.resolution_reason,
                "confidence_score": self.confidence_score,
                "loser_superseded_at": self.loser_superseded_at.isoformat() if self.loser_superseded_at else None,
            },
        }

    @classmethod
    def from_resolution(
        cls,
        audit_id: str,
        contradiction: Contradiction,
        result: ResolutionResult,
    ) -> "AuditEntry":
        """从解决结果创建审计条目"""
        return cls(
            audit_id=audit_id,
            contradiction_id=contradiction.contradiction_id,
            contradiction_type=contradiction.contradiction_type.value,
            topic=contradiction.topic,
            fact_a_id=result.winner.fact_id,  # winner 作为 A
            fact_a_content=result.winner.content,
            fact_a_source=result.winner.source,
            fact_a_confidence=result.winner.confidence,
            fact_a_learned_at=result.winner.learned_at,
            fact_b_id=result.loser.fact_id,  # loser 作为 B
            fact_b_content=result.loser.content,
            fact_b_source=result.loser.source,
            fact_b_confidence=result.loser.confidence,
            fact_b_learned_at=result.loser.learned_at,
            resolution_strategy=result.strategy.value,
            winner_id=result.winner.fact_id,
            loser_id=result.loser.fact_id,
            resolution_reason=result.reason,
            confidence_score=result.confidence_score,
        )


class AuditLogger:
    """
    审计日志器

    记录矛盾解决过程到文件和数据库
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        初始化审计日志器

        Args:
            storage_path: 存储路径，默认为 .saw/reconcile_audit.json
        """
        self.storage_path = storage_path
        self.entries: list[AuditEntry] = []
        self._next_id = 1

        if storage_path and storage_path.exists():
            self.load()

    def log(
        self,
        contradiction: Contradiction,
        result: ResolutionResult,
    ) -> AuditEntry:
        """
        记录审计条目

        Args:
            contradiction: 矛盾记录
            result: 解决结果

        Returns:
            创建的审计条目
        """
        audit_id = f"audit-{self._next_id:04d}"
        self._next_id += 1

        entry = AuditEntry.from_resolution(
            audit_id=audit_id,
            contradiction=contradiction,
            result=result,
        )

        # 记录 loser 被取代的时间
        entry.loser_superseded_at = datetime.now()

        self.entries.append(entry)
        self.save()

        return entry

    def batch_log(
        self,
        contradictions: list[Contradiction],
        results: list[ResolutionResult],
    ) -> list[AuditEntry]:
        """
        批量记录审计

        Args:
            contradictions: 猛盾列表
            results: 解决结果列表

        Returns:
            审计条目列表
        """
        entries = []
        for contradiction, result in zip(contradictions, results):
            entry = self.log(contradiction, result)
            entries.append(entry)
        return entries

    def get_entry(self, audit_id: str) -> Optional[AuditEntry]:
        """获取审计条目"""
        for entry in self.entries:
            if entry.audit_id == audit_id:
                return entry
        return None

    def get_entries_for_topic(self, topic: str) -> list[AuditEntry]:
        """获取主题的所有审计条目"""
        return [e for e in self.entries if e.topic == topic]

    def get_entries_for_fact(self, fact_id: str) -> list[AuditEntry]:
        """获取涉及某事实的所有审计条目"""
        return [
            e for e in self.entries
            if e.fact_a_id == fact_id or e.fact_b_id == fact_id
        ]

    def get_stats(self) -> dict:
        """获取统计信息"""
        strategies_count = {}
        for entry in self.entries:
            strategy = entry.resolution_strategy
            strategies_count[strategy] = strategies_count.get(strategy, 0) + 1

        return {
            "total_entries": len(self.entries),
            "strategies_used": strategies_count,
            "average_confidence_score": (
                sum(e.confidence_score for e in self.entries) / len(self.entries)
                if self.entries else 0
            ),
        }

    def to_json(self) -> dict:
        """转换为 JSON 格式"""
        return {
            "version": 1,
            "entries": [e.to_dict() for e in self.entries],
        }

    def save(self) -> None:
        """保存到文件"""
        if self.storage_path:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            content = json.dumps(self.to_json(), indent=2, ensure_ascii=False)
            self.storage_path.write_text(content, encoding="utf-8")

    def load(self) -> None:
        """从文件加载"""
        if not self.storage_path or not self.storage_path.exists():
            return

        try:
            content = json.loads(self.storage_path.read_text(encoding="utf-8"))
            self.entries = []

            for e_data in content.get("entries", []):
                entry = AuditEntry(
                    audit_id=e_data["audit_id"],
                    timestamp=datetime.fromisoformat(e_data["timestamp"]),
                    contradiction_id=e_data["contradiction_id"],
                    contradiction_type=e_data["contradiction_type"],
                    topic=e_data["topic"],
                    fact_a_id=e_data["fact_a"]["id"],
                    fact_a_content=e_data["fact_a"]["content"],
                    fact_a_source=e_data["fact_a"]["source"],
                    fact_a_confidence=e_data["fact_a"]["confidence"],
                    fact_a_learned_at=(
                        datetime.fromisoformat(e_data["fact_a"]["learned_at"])
                        if e_data["fact_a"]["learned_at"] else None
                    ),
                    fact_b_id=e_data["fact_b"]["id"],
                    fact_b_content=e_data["fact_b"]["content"],
                    fact_b_source=e_data["fact_b"]["source"],
                    fact_b_confidence=e_data["fact_b"]["confidence"],
                    fact_b_learned_at=(
                        datetime.fromisoformat(e_data["fact_b"]["learned_at"])
                        if e_data["fact_b"]["learned_at"] else None
                    ),
                    resolution_strategy=e_data["resolution"]["strategy"],
                    winner_id=e_data["resolution"]["winner_id"],
                    loser_id=e_data["resolution"]["loser_id"],
                    resolution_reason=e_data["resolution"]["reason"],
                    confidence_score=e_data["resolution"]["confidence_score"],
                    loser_superseded_at=(
                        datetime.fromisoformat(e_data["resolution"]["loser_superseded_at"])
                        if e_data["resolution"]["loser_superseded_at"] else None
                    ),
                )
                self.entries.append(entry)

            # 更新 ID 计数器
            if self.entries:
                max_id = max(int(e.audit_id.split("-")[1]) for e in self.entries)
                self._next_id = max_id + 1

        except (json.JSONDecodeError, KeyError, ValueError):
            self.entries = []
            self._next_id = 1

    def clear(self) -> None:
        """清除所有审计记录"""
        self.entries.clear()
        self._next_id = 1
        self.save()
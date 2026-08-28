"""
Reconcile Engine - 矛盾解决引擎

整合检测、策略和审计的完整引擎
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .detector import ContradictionDetector, DetectionResult
from .strategies import ResolutionStrategist, ResolutionResult
from .audit import AuditLogger, AuditEntry
from .models import BiTemporalFact, Contradiction, FactStatus, ResolutionStrategyType


@dataclass
class ReconcileResult:
    """解决引擎结果"""
    detection: DetectionResult
    resolutions: list[ResolutionResult]
    audits: list[AuditEntry]
    total_time: float = 0.0


class ReconcileEngine:
    """
    矛盾解决引擎

    整合检测、策略选择和审计记录：
    1. 扫描 Claims 层检测矛盾
    2. 选择最优解决策略
    3. 执行解决并更新事实状态
    4. 记录完整审计过程
    """

    def __init__(
        self,
        audit_path: Optional[Path] = None,
    ):
        """
        初始化解决引擎

        Args:
            audit_path: 审计日志存储路径
        """
        self.detector = ContradictionDetector()
        self.strategist = ResolutionStrategist()
        self.audit_logger = AuditLogger(storage_path=audit_path)

    def reconcile(
        self,
        facts: list[BiTemporalFact],
        scope: Optional[str] = None,
        auto_apply: bool = False,
    ) -> ReconcileResult:
        """
        执行矛盾解决流程

        Args:
            facts: 事实列表
            scope: 检测范围（topic 过滤）
            auto_apply: 是否自动应用解决结果（F-GOV-06: 默认 False ——
                自动 supersede 输家事实是不可逆的破坏性操作，调用方必须
                显式 opt-in；预览请用 detect_only()）

        Returns:
            解决结果
        """
        start_time = datetime.now()

        # 1. 检测矛盾
        detection = self.detector.detect(facts, scope)

        if not detection.contradictions:
            return ReconcileResult(
                detection=detection,
                resolutions=[],
                audits=[],
                total_time=(datetime.now() - start_time).total_seconds(),
            )

        # 2. 解决矛盾
        resolutions = self.strategist.batch_resolve(detection.contradictions)

        # 3. 记录审计
        audits = self.audit_logger.batch_log(
            detection.contradictions,
            resolutions
        )

        # 4. 应用解决结果（更新事实状态）
        if auto_apply:
            self._apply_resolutions(resolutions)

        total_time = (datetime.now() - start_time).total_seconds()

        return ReconcileResult(
            detection=detection,
            resolutions=resolutions,
            audits=audits,
            total_time=total_time,
        )

    def _apply_resolutions(
        self,
        resolutions: list[ResolutionResult]
    ) -> None:
        """
        应用解决结果

        更新输家事实的状态为 SUPERSEDED
        """
        for result in resolutions:
            # 标记输家为被取代
            result.loser.supersede()

    def get_stats(self) -> dict:
        """获取引擎统计"""
        audit_stats = self.audit_logger.get_stats()

        return {
            "audit": audit_stats,
            "detector": {
                "negation_patterns": len(self.detector.NEGATION_PATTERNS),
            },
        }

    def get_audit_history(
        self,
        topic: Optional[str] = None,
        fact_id: Optional[str] = None,
    ) -> list[AuditEntry]:
        """
        获取审计历史

        Args:
            topic: 按主题过滤
            fact_id: 按事实 ID 过滤

        Returns:
            审计条目列表
        """
        if topic:
            return self.audit_logger.get_entries_for_topic(topic)
        if fact_id:
            return self.audit_logger.get_entries_for_fact(fact_id)
        return self.audit_logger.entries

    def detect_only(
        self,
        facts: list[BiTemporalFact],
        scope: Optional[str] = None,
    ) -> DetectionResult:
        """
        仅执行检测，不解决

        用于预览矛盾情况

        Args:
            facts: 事实列表
            scope: 检测范围

        Returns:
            检测结果
        """
        return self.detector.detect(facts, scope)

    def resolve_single(
        self,
        contradiction: Contradiction,
        strategy_override: Optional[str] = None,
    ) -> tuple[ResolutionResult, AuditEntry]:
        """
        解决单个矛盾

        Args:
            contradiction: 矛盾记录
            strategy_override: 强制使用的策略

        Returns:
            (解决结果, 审计条目) 元组
        """
        if strategy_override:
            # 使用指定策略
            from .strategies import ResolutionStrategy, ResolutionStrategyType
            strategy = ResolutionStrategy(
                ResolutionStrategyType(strategy_override)
            )
            result = strategy.resolve(contradiction)
        else:
            result = self.strategist.resolve(contradiction)

        audit = self.audit_logger.log(contradiction, result)

        # 应用解决
        # F-GOV-06: MANUAL 策略表示"待人工决策"，不应自动 supersede 输家。
        # 只有自动化策略（FRESHNESS/CONFIDENCE/SOURCE_DIVERSITY）才应用。
        if result.strategy != ResolutionStrategyType.MANUAL:
            result.loser.supersede()

        return result, audit

    def explain(self, audit_id: str) -> str:
        """
        解释审计条目的解决过程

        Args:
            audit_id: 审计 ID

        Returns:
            解释文本
        """
        entry = self.audit_logger.get_entry(audit_id)
        if not entry:
            return f"No audit entry found for {audit_id}"

        return (
            f"## Reconciliation Audit: {audit_id}\n\n"
            f"**Topic:** {entry.topic}\n\n"
            f"### Contradiction\n\n"
            f"**Type:** {entry.contradiction_type}\n\n"
            f"**Fact A:**\n"
            f"- ID: {entry.fact_a_id}\n"
            f"- Content: {entry.fact_a_content[:100]}...\n"
            f"- Source: {entry.fact_a_source}\n"
            f"- Confidence: {entry.fact_a_confidence}\n\n"
            f"**Fact B:**\n"
            f"- ID: {entry.fact_b_id}\n"
            f"- Content: {entry.fact_b_content[:100]}...\n"
            f"- Source: {entry.fact_b_source}\n"
            f"- Confidence: {entry.fact_b_confidence}\n\n"
            f"### Resolution\n\n"
            f"**Strategy:** {entry.resolution_strategy}\n"
            f"**Winner:** {entry.winner_id}\n"
            f"**Reason:** {entry.resolution_reason}\n"
            f"**Confidence Score:** {entry.confidence_score:.2f}\n\n"
            f"### Timeline\n\n"
            f"- Detected & Resolved: {entry.timestamp.isoformat()}\n"
            f"- Loser Superseded: {entry.loser_superseded_at.isoformat() if entry.loser_superseded_at else 'N/A'}\n"
        )
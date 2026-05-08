"""
Reconcile Engine Tests

测试矛盾检测、解决策略和审计记录
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from saw.reconcile import (
    ReconcileEngine,
    BiTemporalFact,
    ContradictionDetector,
    ContradictionType,
    ResolutionStrategist,
    ResolutionStrategyType,
    AuditLogger,
    FactStatus,
)


class TestBiTemporalFact:
    """Bi-Temporal Fact 测试"""

    def test_is_valid_at(self):
        """测试时间有效性检查"""
        fact = BiTemporalFact(
            fact_id="test-001",
            content="Test content",
            topic="test",
            valid_from=datetime(2026, 1, 1),
            valid_until=datetime(2026, 12, 31),
        )

        assert fact.is_valid_at(datetime(2026, 6, 1)) is True
        assert fact.is_valid_at(datetime(2025, 12, 31)) is False
        assert fact.is_valid_at(datetime(2027, 1, 1)) is False

    def test_is_current(self):
        """测试当前有效性"""
        fact = BiTemporalFact(
            fact_id="test-002",
            content="Test",
            topic="test",
            valid_from=datetime.now() - timedelta(days=1),
        )

        assert fact.is_current() is True

        fact.supersede()
        assert fact.is_current() is False
        assert fact.status == FactStatus.SUPERSEDED

    def test_supersede(self):
        """测试取代操作"""
        fact = BiTemporalFact(
            fact_id="test-003",
            content="Test",
            topic="test",
            valid_from=datetime.now() - timedelta(days=1),
        )

        fact.supersede()

        assert fact.valid_until is not None
        assert fact.status == FactStatus.SUPERSEDED


class TestContradictionDetector:
    """矛盾检测器测试"""

    def test_detect_direct_contradiction(self):
        """测试直接矛盾检测"""
        detector = ContradictionDetector()

        facts = [
            BiTemporalFact(
                fact_id="fact-a",
                content="The sky is blue",
                topic="sky",
                valid_from=datetime.now(),
                confidence=2,
            ),
            BiTemporalFact(
                fact_id="fact-b",
                content="The sky is not blue",
                topic="sky",
                valid_from=datetime.now(),
                confidence=2,
            ),
        ]

        result = detector.detect(facts)

        assert len(result.contradictions) >= 1
        if result.contradictions:
            assert result.contradictions[0].contradiction_type == ContradictionType.DIRECT

    def test_detect_confidence_contradiction(self):
        """测试置信度矛盾检测"""
        detector = ContradictionDetector()

        facts = [
            BiTemporalFact(
                fact_id="fact-a",
                content="Python is a programming language",
                topic="python",
                valid_from=datetime.now(),
                confidence=4,
            ),
            BiTemporalFact(
                fact_id="fact-b",
                content="Python is a programming language",
                topic="python",
                valid_from=datetime.now(),
                confidence=1,
            ),
        ]

        result = detector.detect(facts)

        assert len(result.contradictions) >= 1
        if result.contradictions:
            assert result.contradictions[0].contradiction_type == ContradictionType.CONFIDENCE

    def test_no_contradiction_for_same_content(self):
        """测试相同内容不产生矛盾"""
        detector = ContradictionDetector()

        facts = [
            BiTemporalFact(
                fact_id="fact-a",
                content="Same content",
                topic="test",
                valid_from=datetime.now(),
                confidence=2,
            ),
            BiTemporalFact(
                fact_id="fact-b",
                content="Same content",
                topic="test",
                valid_from=datetime.now(),
                confidence=2,
            ),
        ]

        result = detector.detect(facts)

        # 相同内容不应该产生直接矛盾
        direct_contradictions = [
            c for c in result.contradictions
            if c.contradiction_type == ContradictionType.DIRECT
        ]
        assert len(direct_contradictions) == 0


class TestResolutionStrategist:
    """解决策略测试"""

    def test_freshness_wins_strategy(self):
        """测试 FRESHNESS_WINS 策略"""
        strategist = ResolutionStrategist()

        now = datetime.now()
        earlier = now - timedelta(days=2)

        fact_a = BiTemporalFact(
            fact_id="fact-a",
            content="Old fact",
            topic="test",
            valid_from=earlier,
            learned_at=earlier,
            confidence=2,
        )
        fact_b = BiTemporalFact(
            fact_id="fact-b",
            content="New fact",
            topic="test",
            valid_from=now,
            learned_at=now,
            confidence=2,
        )

        contradiction = type('obj', (object,), {
            'fact_a': fact_a,
            'fact_b': fact_b,
        })()

        result = strategist.resolve(contradiction)

        assert result.strategy == ResolutionStrategyType.FRESHNESS_WINS
        assert result.winner.fact_id == "fact-b"

    def test_confidence_wins_strategy(self):
        """测试 CONFIDENCE_WINS 策略"""
        strategist = ResolutionStrategist()

        now = datetime.now()

        fact_a = BiTemporalFact(
            fact_id="fact-a",
            content="Low confidence fact",
            topic="test",
            valid_from=now,
            learned_at=now,
            confidence=1,
        )
        fact_b = BiTemporalFact(
            fact_id="fact-b",
            content="High confidence fact",
            topic="test",
            valid_from=now,
            learned_at=now,
            confidence=4,
        )

        contradiction = type('obj', (object,), {
            'fact_a': fact_a,
            'fact_b': fact_b,
        })()

        result = strategist.resolve(contradiction)

        assert result.strategy == ResolutionStrategyType.CONFIDENCE_WINS
        assert result.winner.fact_id == "fact-b"


class TestAuditLogger:
    """审计日志器测试"""

    def test_log_and_retrieve(self):
        """测试记录和检索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit.json"
            logger = AuditLogger(storage_path=audit_path)

            # 创建模拟数据
            fact_a = BiTemporalFact(
                fact_id="fact-a",
                content="Test A",
                topic="test",
                valid_from=datetime.now(),
                confidence=2,
            )
            fact_b = BiTemporalFact(
                fact_id="fact-b",
                content="Test B",
                topic="test",
                valid_from=datetime.now(),
                confidence=2,
            )

            from saw.reconcile.models import Contradiction
            from saw.reconcile.strategies import ResolutionResult

            contradiction = Contradiction(
                contradiction_id="contr-001",
                contradiction_type=ContradictionType.DIRECT,
                topic="test",
                fact_a=fact_a,
                fact_b=fact_b,
            )

            result = ResolutionResult(
                winner=fact_a,
                loser=fact_b,
                strategy=ResolutionStrategyType.CONFIDENCE_WINS,
                reason="Test reason",
                confidence_score=0.75,
            )

            # 记录审计
            entry = logger.log(contradiction, result)

            assert entry.audit_id is not None
            assert entry.winner_id == "fact-a"
            assert entry.loser_id == "fact-b"

            # 检索审计
            retrieved = logger.get_entry(entry.audit_id)
            assert retrieved is not None

    def test_persistence(self):
        """测试持久化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit.json"

            # 创建并保存
            logger1 = AuditLogger(storage_path=audit_path)
            # ... 添加条目 ...

            # 重新加载
            logger2 = AuditLogger(storage_path=audit_path)
            assert len(logger2.entries) == len(logger1.entries)


class TestReconcileEngine:
    """解决引擎集成测试"""

    def test_full_reconcile_flow(self):
        """测试完整解决流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit.json"
            engine = ReconcileEngine(audit_path=audit_path)

            # 创建矛盾事实
            now = datetime.now()

            facts = [
                BiTemporalFact(
                    fact_id="fact-a",
                    content="API returns JSON format",
                    topic="api",
                    valid_from=now,
                    learned_at=now - timedelta(days=1),
                    confidence=2,
                ),
                BiTemporalFact(
                    fact_id="fact-b",
                    content="API does not return JSON format",
                    topic="api",
                    valid_from=now,
                    learned_at=now,
                    confidence=3,
                ),
            ]

            # 运行解决
            result = engine.reconcile(facts, auto_apply=True)

            assert result.detection.total_scanned == 2
            assert len(result.resolutions) >= 1
            assert len(result.audits) >= 1

    def test_detect_only(self):
        """测试仅检测不解决"""
        engine = ReconcileEngine()

        facts = [
            BiTemporalFact(
                fact_id="fact-a",
                content="Statement A",
                topic="test",
                valid_from=datetime.now(),
            ),
            BiTemporalFact(
                fact_id="fact-b",
                content="Not statement A",
                topic="test",
                valid_from=datetime.now(),
            ),
        ]

        result = engine.detect_only(facts)

        assert result.total_scanned == 2

    def test_get_stats(self):
        """测试获取统计"""
        engine = ReconcileEngine()
        stats = engine.get_stats()

        assert "audit" in stats
        assert "detector" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Resolution Strategies - 解决策略

实现三种矛盾解决策略
"""

from dataclasses import dataclass
from typing import Tuple

from .models import (
    BiTemporalFact,
    Contradiction,
    ResolutionStrategyType,
)


@dataclass
class ResolutionResult:
    """解决结果"""
    winner: BiTemporalFact
    loser: BiTemporalFact
    strategy: ResolutionStrategyType
    reason: str
    confidence_score: float


class ResolutionStrategist:
    """
    解决策略选择器

    根据矛盾类型和事实属性选择最优解决策略
    """

    def resolve(self, contradiction: Contradiction) -> ResolutionResult:
        """
        解决矛盾

        Args:
            contradiction: 矛盾记录

        Returns:
            解决结果
        """
        # 根据矛盾类型选择策略
        strategy = self._select_strategy(contradiction)

        # 应用策略选出赢家
        winner, loser, reason = self._apply_strategy(
            contradiction.fact_a,
            contradiction.fact_b,
            strategy
        )

        # 计算置信度分数
        confidence_score = self._calculate_confidence_score(
            winner, loser, strategy
        )

        return ResolutionResult(
            winner=winner,
            loser=loser,
            strategy=strategy,
            reason=reason,
            confidence_score=confidence_score,
        )

    def _select_strategy(
        self,
        contradiction: Contradiction
    ) -> ResolutionStrategyType:
        """
        选择解决策略

        策略选择规则：
        1. 如果置信度差异 >= 2，使用 CONFIDENCE_WINS
        2. 如果时间差异显著（> 1 天），使用 FRESHNESS_WINS
        3. 如果来源多样性差异显著，使用 SOURCE_DIVERSITY
        4. 默认使用 FRESHNESS_WINS
        """
        fact_a = contradiction.fact_a
        fact_b = contradiction.fact_b

        # 检查置信度差异
        confidence_diff = abs(fact_a.confidence - fact_b.confidence)
        if confidence_diff >= 2:
            return ResolutionStrategyType.CONFIDENCE_WINS

        # 检查时间差异
        time_diff = abs(
            (fact_a.learned_at - fact_b.learned_at).total_seconds()
        )
        if time_diff > 86400:  # > 1 天
            return ResolutionStrategyType.FRESHNESS_WINS

        # 检查来源多样性（简化：检查 source 是否相同）
        if fact_a.source != fact_b.source:
            return ResolutionStrategyType.SOURCE_DIVERSITY

        # 默认使用 FRESHNESS_WINS
        return ResolutionStrategyType.FRESHNESS_WINS

    def _apply_strategy(
        self,
        fact_a: BiTemporalFact,
        fact_b: BiTemporalFact,
        strategy: ResolutionStrategyType
    ) -> Tuple[BiTemporalFact, BiTemporalFact, str]:
        """
        应用解决策略

        Args:
            fact_a: 第一个事实
            fact_b: 第二个事实
            strategy: 策略类型

        Returns:
            (赢家, 输家, 原因) 元组
        """
        if strategy == ResolutionStrategyType.FRESHNESS_WINS:
            # 新数据优先
            if fact_a.learned_at >= fact_b.learned_at:
                return fact_a, fact_b, "Fact A is more recent"
            else:
                return fact_b, fact_a, "Fact B is more recent"

        elif strategy == ResolutionStrategyType.CONFIDENCE_WINS:
            # 高置信度优先
            if fact_a.confidence >= fact_b.confidence:
                return fact_a, fact_b, f"Fact A has higher confidence ({fact_a.confidence} vs {fact_b.confidence})"
            else:
                return fact_b, fact_a, f"Fact B has higher confidence ({fact_b.confidence} vs {fact_a.confidence})"

        elif strategy == ResolutionStrategyType.SOURCE_DIVERSITY:
            # 多来源一致优先（这里简化为检查置信度）
            # 实际应该检查来源的独立性和可信度
            if fact_a.confidence >= fact_b.confidence:
                return fact_a, fact_b, "Fact A preferred by source diversity heuristic"
            else:
                return fact_b, fact_a, "Fact B preferred by source diversity heuristic"

        else:
            # Manual 策略需要人工决策，默认返回第一个
            return fact_a, fact_b, "Manual resolution pending"

    def _calculate_confidence_score(
        self,
        winner: BiTemporalFact,
        loser: BiTemporalFact,
        strategy: ResolutionStrategyType
    ) -> float:
        """
        计算解决置信度分数

        Args:
            winner: 赢家事实
            loser: 输家事实
            strategy: 使用的策略

        Returns:
            置信度分数 (0-1)
        """
        # 基础分数来自赢家置信度
        base_score = winner.confidence / 4.0

        # 根据策略调整
        strategy_bonus = {
            ResolutionStrategyType.CONFIDENCE_WINS: 0.15,  # 高置信度策略加分
            ResolutionStrategyType.FRESHNESS_WINS: 0.10,  # 新数据策略加分
            ResolutionStrategyType.SOURCE_DIVERSITY: 0.12,  # 多来源策略加分
            ResolutionStrategyType.MANUAL: 0.0,  # 手动策略不加分
        }

        return min(1.0, base_score + strategy_bonus[strategy])

    def batch_resolve(
        self,
        contradictions: list[Contradiction]
    ) -> list[ResolutionResult]:
        """
        批量解决矛盾

        Args:
            contradictions: 矛盾列表

        Returns:
            解决结果列表
        """
        results = []
        for contradiction in contradictions:
            result = self.resolve(contradiction)
            results.append(result)
        return results


class ResolutionStrategy:
    """
    单一策略实现类

    用于手动指定策略解决矛盾
    """

    def __init__(self, strategy_type: ResolutionStrategyType):
        self.strategy_type = strategy_type
        self.strategist = ResolutionStrategist()

    def resolve(self, contradiction: Contradiction) -> ResolutionResult:
        """
        使用指定策略解决矛盾

        Args:
            contradiction: 矛盾记录

        Returns:
            解决结果
        """
        # 直接应用指定策略
        winner, loser, reason = self.strategist._apply_strategy(
            contradiction.fact_a,
            contradiction.fact_b,
            self.strategy_type
        )

        confidence_score = self.strategist._calculate_confidence_score(
            winner, loser, self.strategy_type
        )

        return ResolutionResult(
            winner=winner,
            loser=loser,
            strategy=self.strategy_type,
            reason=reason,
            confidence_score=confidence_score,
        )
"""
Purpose Analyzer - Purpose 分析器

分析内容与 Purpose 的匹配度
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import re


@dataclass
class AlignmentResult:
    """对齐分析结果"""
    score: float  # 0-1
    matched_goals: list[str]
    relevance_to_thesis: float
    in_scope: bool
    recommendations: list[str]


class PurposeAnalyzer:
    """
    Purpose 分析器

    分析内容与 Purpose 的匹配度：
    1. 检查是否在研究范围内
    2. 评估对目标的贡献度
    3. 识别论点相关性
    4. 提供建议
    """

    def analyze(
        self,
        content: str,
        purpose_summary: str,
        goals: list[str],
        thesis: str,
        scope_included: list[str],
        scope_excluded: list[str],
    ) -> AlignmentResult:
        """
        分析内容与 Purpose 的对齐度

        Args:
            content: 待分析内容
            purpose_summary: Purpose 摘要
            goals: 目标列表
            thesis: 演进论点
            scope_included: 包含范围
            scope_excluded: 排除范围

        Returns:
            对齐分析结果
        """
        # 1. 检查范围
        in_scope = self._check_scope(content, scope_included, scope_excluded)

        # 2. 匹配目标
        matched_goals = self._match_goals(content, goals)

        # 3. 评估论点相关性
        relevance_to_thesis = self._evaluate_thesis_relevance(content, thesis)

        # 4. 计算总体分数
        score = self._calculate_score(
            in_scope=in_scope,
            matched_goals=len(matched_goals),
            total_goals=len(goals),
            thesis_relevance=relevance_to_thesis,
        )

        # 5. 生成建议
        recommendations = self._generate_recommendations(
            in_scope=in_scope,
            matched_goals=matched_goals,
            thesis_relevance=relevance_to_thesis,
        )

        return AlignmentResult(
            score=score,
            matched_goals=matched_goals,
            relevance_to_thesis=relevance_to_thesis,
            in_scope=in_scope,
            recommendations=recommendations,
        )

    def _check_scope(
        self,
        content: str,
        included: list[str],
        excluded: list[str],
    ) -> bool:
        """检查是否在范围内"""
        content_lower = content.lower()

        # 检查排除范围
        for keyword in excluded:
            if keyword.lower() in content_lower:
                return False

        # 检查包含范围
        if included:
            for keyword in included:
                if keyword.lower() in content_lower:
                    return True
            # 有关键词但都不匹配
            return False

        # 无限制
        return True

    def _match_goals(
        self,
        content: str,
        goals: list[str],
    ) -> list[str]:
        """匹配目标"""
        matched = []

        for goal in goals:
            # 简单关键词匹配
            keywords = self._extract_keywords(goal)
            content_lower = content.lower()

            match_count = sum(
                1 for kw in keywords
                if kw.lower() in content_lower
            )

            if match_count >= len(keywords) * 0.3:
                matched.append(goal)

        return matched

    def _evaluate_thesis_relevance(
        self,
        content: str,
        thesis: str,
    ) -> float:
        """评估论点相关性"""
        if not thesis:
            return 0.5

        thesis_keywords = self._extract_keywords(thesis)
        if not thesis_keywords:
            return 0.5

        content_lower = content.lower()
        matches = sum(
            1 for kw in thesis_keywords
            if kw.lower() in content_lower
        )

        return min(1.0, matches / len(thesis_keywords))

    def _calculate_score(
        self,
        in_scope: bool,
        matched_goals: int,
        total_goals: int,
        thesis_relevance: float,
    ) -> float:
        """计算总体分数"""
        if not in_scope:
            return 0.0

        # 加权计算
        scope_score = 1.0 if in_scope else 0.0
        goal_score = matched_goals / total_goals if total_goals > 0 else 0.5

        return (
            scope_score * 0.3 +
            goal_score * 0.4 +
            thesis_relevance * 0.3
        )

    def _generate_recommendations(
        self,
        in_scope: bool,
        matched_goals: list[str],
        thesis_relevance: float,
    ) -> list[str]:
        """生成建议"""
        recommendations = []

        if not in_scope:
            recommendations.append(
                "Content is out of scope. Consider if it should be included."
            )

        if not matched_goals:
            recommendations.append(
                "Content does not directly align with current goals."
            )

        if thesis_relevance < 0.3:
            recommendations.append(
                "Content has low relevance to the evolving thesis."
            )

        if thesis_relevance > 0.7:
            recommendations.append(
                "High thesis relevance - may warrant thesis update."
            )

        return recommendations

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 简单分词
        words = re.findall(r"\w+", text.lower())

        # 过滤停用词
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "can",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "and", "or", "but", "if", "not", "this", "that", "these",
        }

        return [w for w in words if len(w) >= 3 and w not in stop_words]

    def suggest_thesis_update(
        self,
        new_content: str,
        current_thesis: str,
    ) -> Optional[str]:
        """
        建议论点更新

        Args:
            new_content: 新内容
            current_thesis: 当前论点

        Returns:
            建议的论点更新（如有）
        """
        if not current_thesis:
            return None

        # 分析新内容是否与论点相关
        relevance = self._evaluate_thesis_relevance(new_content, current_thesis)

        if relevance > 0.7:
            # 高相关性，可能需要更新论点
            return (
                "New content strongly supports or challenges current thesis. "
                "Consider reviewing and potentially updating the thesis."
            )

        return None
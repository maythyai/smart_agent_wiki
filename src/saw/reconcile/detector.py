"""
Contradiction Detector - 矛盾检测器

检测 Claims 层中的矛盾主张
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import hashlib
import re

from .models import BiTemporalFact, Contradiction, ContradictionType


@dataclass
class DetectionResult:
    """检测结果"""
    contradictions: list[Contradiction] = field(default_factory=list)
    total_scanned: int = 0
    scan_time: float = 0.0


class ContradictionDetector:
    """
    矛盾检测器

    检测 Claims 层中的矛盾主张：
    - 直接矛盾：A vs !A
    - 时间矛盾：同主题不同时间的陈述
    - 置信度矛盾：同事实不同置信度
    - 部分矛盾：有交集但不完全冲突
    """

    # 否定词模式
    NEGATION_PATTERNS = [
        r"\bnot\b",
        r"\bno\b",
        r"\bnever\b",
        r"\bdon'?t\b",
        r"\bdoesn'?t\b",
        r"\bisn'?t\b",
        r"\baren'?t\b",
        r"\bwasn'?t\b",
        r"\bweren'?t\b",
        r"\b非\b",
        r"\b不\b",
        r"\b无\b",
        r"\b没有\b",
    ]

    def __init__(self):
        self._negation_regex = re.compile(
            "|".join(self.NEGATION_PATTERNS),
            re.IGNORECASE
        )

    def detect(
        self,
        facts: list[BiTemporalFact],
        scope: Optional[str] = None
    ) -> DetectionResult:
        """
        检测矛盾

        Args:
            facts: 事实列表
            scope: 检测范围（topic 过滤）

        Returns:
            检测结果
        """
        start_time = datetime.now()
        contradictions = []

        # 按 topic 分组
        topic_facts: dict[str, list[BiTemporalFact]] = {}
        for fact in facts:
            if scope and scope not in fact.topic:
                continue
            if fact.topic not in topic_facts:
                topic_facts[fact.topic] = []
            topic_facts[fact.topic].append(fact)

        # 检测每个 topic 内的矛盾
        for topic, topic_fact_list in topic_facts.items():
            if len(topic_fact_list) < 2:
                continue

            # 两两比较
            for i, fact_a in enumerate(topic_fact_list):
                for fact_b in topic_fact_list[i + 1:]:
                    contradiction = self._check_contradiction(fact_a, fact_b)
                    if contradiction:
                        contradictions.append(contradiction)

        scan_time = (datetime.now() - start_time).total_seconds()

        return DetectionResult(
            contradictions=contradictions,
            total_scanned=len(facts),
            scan_time=scan_time,
        )

    def _check_contradiction(
        self,
        fact_a: BiTemporalFact,
        fact_b: BiTemporalFact
    ) -> Optional[Contradiction]:
        """
        检查两个事实是否存在矛盾

        Args:
            fact_a: 第一个事实
            fact_b: 第二个事实

        Returns:
            如果存在矛盾则返回 Contradiction，否则返回 None
        """
        # 检查直接矛盾
        if self._is_direct_contradiction(fact_a, fact_b):
            return Contradiction(
                contradiction_id=self._generate_id(fact_a, fact_b),
                contradiction_type=ContradictionType.DIRECT,
                topic=fact_a.topic,
                fact_a=fact_a,
                fact_b=fact_b,
            )

        # 检查时间矛盾
        if self._is_temporal_contradiction(fact_a, fact_b):
            return Contradiction(
                contradiction_id=self._generate_id(fact_a, fact_b),
                contradiction_type=ContradictionType.TEMPORAL,
                topic=fact_a.topic,
                fact_a=fact_a,
                fact_b=fact_b,
            )

        # 检查置信度矛盾
        if self._is_confidence_contradiction(fact_a, fact_b):
            return Contradiction(
                contradiction_id=self._generate_id(fact_a, fact_b),
                contradiction_type=ContradictionType.CONFIDENCE,
                topic=fact_a.topic,
                fact_a=fact_a,
                fact_b=fact_b,
            )

        return None

    def _is_direct_contradiction(
        self,
        fact_a: BiTemporalFact,
        fact_b: BiTemporalFact
    ) -> bool:
        """
        检查是否为直接矛盾

        使用启发式规则：
        - 一个包含否定词，另一个不包含
        - 内容相似度高
        """
        content_a = fact_a.content.lower()
        content_b = fact_b.content.lower()

        # 检查否定词
        has_negation_a = bool(self._negation_regex.search(content_a))
        has_negation_b = bool(self._negation_regex.search(content_b))

        # 如果一个有否定一个没有，检查相似度
        if has_negation_a != has_negation_b:
            # 简单相似度检查：移除否定词后比较
            clean_a = self._negation_regex.sub("", content_a).strip()
            clean_b = self._negation_regex.sub("", content_b).strip()

            # 如果相似度 > 50%，认为是直接矛盾
            similarity = self._calculate_similarity(clean_a, clean_b)
            if similarity > 0.5:
                return True

        return False

    def _is_temporal_contradiction(
        self,
        fact_a: BiTemporalFact,
        fact_b: BiTemporalFact
    ) -> bool:
        """
        检查是否为时间矛盾

        条件：
        - 同一主题
        - 有效期重叠
        - 内容不同
        """
        # 内容完全相同不算矛盾
        if fact_a.content == fact_b.content:
            return False

        # 检查有效期是否重叠
        if fact_a.valid_until and fact_b.valid_until:
            # 两个都有结束时间
            if fact_a.valid_from > fact_b.valid_until or fact_b.valid_from > fact_a.valid_until:
                return False  # 不重叠
        elif fact_a.valid_until:
            if fact_a.valid_from > fact_b.valid_from or fact_a.valid_until < fact_b.valid_from:
                return False
        elif fact_b.valid_until:
            if fact_b.valid_from > fact_a.valid_from or fact_b.valid_until < fact_a.valid_from:
                return False

        # 有效期重叠且内容不同
        return True

    def _is_confidence_contradiction(
        self,
        fact_a: BiTemporalFact,
        fact_b: BiTemporalFact
    ) -> bool:
        """
        检查是否为置信度矛盾

        条件：
        - 内容相似度高
        - 置信度差异 >= 2
        """
        if abs(fact_a.confidence - fact_b.confidence) < 2:
            return False

        similarity = self._calculate_similarity(
            fact_a.content.lower(),
            fact_b.content.lower()
        )

        return similarity > 0.7

    def _calculate_similarity(self, text_a: str, text_b: str) -> float:
        """
        计算文本相似度（简单 Jaccard 相似度）

        Args:
            text_a: 第一个文本
            text_b: 第二个文本

        Returns:
            相似度 (0-1)
        """
        words_a = set(text_a.split())
        words_b = set(text_b.split())

        if not words_a or not words_b:
            return 0.0

        intersection = words_a & words_b
        union = words_a | words_b

        return len(intersection) / len(union)

    def _generate_id(
        self,
        fact_a: BiTemporalFact,
        fact_b: BiTemporalFact
    ) -> str:
        """生成矛盾 ID"""
        # 确保 ID 稳定（不依赖于顺序）
        ids = sorted([fact_a.fact_id, fact_b.fact_id])
        combined = f"{ids[0]}:{ids[1]}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]

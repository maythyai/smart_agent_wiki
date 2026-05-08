"""
Pattern Miner - 模式挖掘器

发现跨来源的隐含模式
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from collections import Counter
import hashlib
import re


@dataclass
class Pattern:
    """
    发现的模式

    记录重复出现的概念及其统计信息
    """
    pattern_id: str
    name: str  # 建议的命名
    keywords: list[str]  # 关键词集合
    occurrences: int  # 出现次数
    sources: list[str]  # 来源列表
    first_seen: datetime
    last_seen: datetime
    confidence: float = 0.0  # 模式置信度
    description: str = ""

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "keywords": self.keywords,
            "occurrences": self.occurrences,
            "sources": self.sources,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "confidence": self.confidence,
            "description": self.description,
        }


@dataclass
class MiningResult:
    """挖掘结果"""
    patterns: list[Pattern] = field(default_factory=list)
    total_items: int = 0
    mining_time: float = 0.0


class PatternMiner:
    """
    模式挖掘器

    使用 TF-IDF 和频率分析发现隐含模式：
    1. 提取关键词
    2. 计算关键词频率
    3. 聚合高频关键词为模式
    4. 生成模式命名建议
    """

    # 常见停用词
    STOP_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "must", "can",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "under", "again", "further", "then",
        "once", "here", "there", "when", "where", "why", "how",
        "all", "each", "few", "more", "most", "other", "some", "such",
        "no", "nor", "not", "only", "own", "same", "so", "than",
        "too", "very", "just", "and", "but", "if", "or", "because",
        "until", "while", "although", "though", "whether",
        # 中文停用词
        "的", "是", "在", "有", "和", "与", "了", "不", "也", "就",
        "都", "这", "那", "要", "会", "能", "为", "对", "上", "下",
        "中", "来", "去", "到", "说", "看", "做", "想", "把", "被",
    }

    def __init__(
        self,
        min_occurrences: int = 3,
        min_confidence: float = 0.3,
    ):
        """
        初始化模式挖掘器

        Args:
            min_occurrences: 最小出现次数阈值
            min_confidence: 最小置信度阈值
        """
        self.min_occurrences = min_occurrences
        self.min_confidence = min_confidence

    def mine(
        self,
        items: list[dict],
        time_window: Optional[timedelta] = None,
    ) -> MiningResult:
        """
        挖掘模式

        Args:
            items: 内容项列表，每项包含 content, source, timestamp
            time_window: 时间窗口限制

        Returns:
            挖掘结果
        """
        start_time = datetime.now()

        # 过滤时间窗口
        if time_window:
            cutoff = datetime.now() - time_window
            items = [
                i for i in items
                if datetime.fromisoformat(i.get("timestamp", "")) >= cutoff
            ]

        # 提取关键词
        keyword_occurrences: dict[str, list[dict]] = {}
        keyword_sources: dict[str, set[str]] = {}

        for item in items:
            keywords = self._extract_keywords(item.get("content", ""))
            source = item.get("source", "unknown")
            timestamp = datetime.fromisoformat(item.get("timestamp", "")) if item.get("timestamp") else datetime.now()

            for keyword in keywords:
                if keyword not in keyword_occurrences:
                    keyword_occurrences[keyword] = []
                    keyword_sources[keyword] = set()

                keyword_occurrences[keyword].append({
                    "source": source,
                    "timestamp": timestamp,
                    "content": item.get("content", ""),
                })
                keyword_sources[keyword].add(source)

        # 构建模式
        patterns = self._build_patterns(
            keyword_occurrences,
            keyword_sources,
            items,
        )

        # 过滤低置信度模式
        patterns = [
            p for p in patterns
            if p.occurrences >= self.min_occurrences
            and p.confidence >= self.min_confidence
        ]

        mining_time = (datetime.now() - start_time).total_seconds()

        return MiningResult(
            patterns=patterns,
            total_items=len(items),
            mining_time=mining_time,
        )

    def _extract_keywords(self, content: str) -> list[str]:
        """
        提取关键词

        Args:
            content: 文本内容

        Returns:
            关键词列表
        """
        # 简单分词
        words = re.findall(r"\w+", content.lower())

        # 过滤停用词和短词
        keywords = [
            w for w in words
            if len(w) >= 3 and w not in self.STOP_WORDS
        ]

        return keywords

    def _build_patterns(
        self,
        keyword_occurrences: dict[str, list[dict]],
        keyword_sources: dict[str, set[str]],
        items: list[dict],
    ) -> list[Pattern]:
        """
        构建模式

        从高频关键词聚合为模式
        """
        patterns = []

        # 计算关键词频率
        keyword_freq = Counter({
            k: len(v) for k, v in keyword_occurrences.items()
        })

        # 取高频关键词
        top_keywords = [
            k for k, v in keyword_freq.most_common(100)
            if v >= self.min_occurrences
        ]

        # 为每个高频关键词创建模式
        for keyword in top_keywords:
            occurrences = keyword_occurrences[keyword]
            sources = list(keyword_sources[keyword])

            # 计算置信度（基于来源多样性）
            confidence = min(1.0, len(sources) / 5.0) * 0.5 + \
                         min(1.0, len(occurrences) / 10.0) * 0.5

            # 时间范围
            timestamps = [o["timestamp"] for o in occurrences]
            first_seen = min(timestamps)
            last_seen = max(timestamps)

            pattern = Pattern(
                pattern_id=self._generate_id(keyword),
                name=self._suggest_name(keyword),
                keywords=[keyword],
                occurrences=len(occurrences),
                sources=sources,
                first_seen=first_seen,
                last_seen=last_seen,
                confidence=confidence,
                description=f"Pattern involving '{keyword}' appears {len(occurrences)} times",
            )

            patterns.append(pattern)

        return patterns

    def _suggest_name(self, keyword: str) -> str:
        """
        建议模式命名

        简单实现：使用关键词作为名称
        """
        return f"{keyword.capitalize()} Pattern"

    def _generate_id(self, keyword: str) -> str:
        """生成模式 ID"""
        return hashlib.md5(keyword.encode()).hexdigest()[:12]


class PatternAggregator:
    """
    模式聚合器

    将相似关键词聚合为更复杂的模式
    """

    def aggregate(
        self,
        patterns: list[Pattern],
        similarity_threshold: float = 0.5,
    ) -> list[Pattern]:
        """
        聚合相似模式

        Args:
            patterns: 模式列表
            similarity_threshold: 相似度阈值

        Returns:
            聚合后的模式列表
        """
        # TODO: 实现更复杂的聚合算法
        # 当前简单实��：合并相同关键词
        return patterns
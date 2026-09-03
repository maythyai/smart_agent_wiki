"""
Cluster Builder - 聚合构建器

将相关主张聚合为簇
"""

from dataclasses import dataclass, field
from datetime import datetime
import hashlib


@dataclass
class Cluster:
    """
    主张聚合簇

    将相关主张聚合在一起
    """
    cluster_id: str
    topic: str
    claims: list[str]  # claim IDs
    summary: str
    confidence: float
    sources: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "cluster_id": self.cluster_id,
            "topic": self.topic,
            "claims": self.claims,
            "summary": self.summary,
            "confidence": self.confidence,
            "sources": self.sources,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ClusterResult:
    """聚合结果"""
    clusters: list[Cluster] = field(default_factory=list)
    total_claims: int = 0


class ClusterBuilder:
    """
    聚合构建器

    将相关主张聚合为簇：
    1. 按主题分组
    2. 计算相似度
    3. 合并相似主张
    4. 生成簇摘要
    """

    def __init__(
        self,
        similarity_threshold: float = 0.6,
        min_cluster_size: int = 2,
    ):
        """
        初始化聚合构建器

        Args:
            similarity_threshold: 相似度阈值
            min_cluster_size: 最小簇大小
        """
        self.similarity_threshold = similarity_threshold
        self.min_cluster_size = min_cluster_size

    def build(
        self,
        claims: list[dict],
    ) -> ClusterResult:
        """
        构建聚合簇

        Args:
            claims: 主张列表，每项包含 id, content, topic, confidence, source

        Returns:
            聚合结果
        """
        # 按 topic 分组
        topic_groups: dict[str, list[dict]] = {}
        for claim in claims:
            topic = claim.get("topic", "general")
            if topic not in topic_groups:
                topic_groups[topic] = []
            topic_groups[topic].append(claim)

        clusters = []

        # 对每个 topic 进行聚合
        for topic, topic_claims in topic_groups.items():
            if len(topic_claims) < self.min_cluster_size:
                continue

            # 简单实现：同一 topic 全部聚合
            cluster = Cluster(
                cluster_id=self._generate_id(topic),
                topic=topic,
                claims=[c.get("id", "") for c in topic_claims],
                summary=self._generate_summary(topic_claims),
                confidence=self._calculate_confidence(topic_claims),
                sources=list(set(c.get("source", "") for c in topic_claims)),
            )

            clusters.append(cluster)

        return ClusterResult(
            clusters=clusters,
            total_claims=len(claims),
        )

    def _generate_id(self, topic: str) -> str:
        """生成簇 ID"""
        return hashlib.md5(topic.encode()).hexdigest()[:12]

    def _generate_summary(self, claims: list[dict]) -> str:
        """
        生成簇摘要

        Args:
            claims: 主张列表

        Returns:
            摘要文本
        """
        # 合并所有主张的内容片段
        return f"Cluster of {len(claims)} related claims about similar topics"

    def _calculate_confidence(self, claims: list[dict]) -> float:
        """
        计算簇置信度

        Args:
            claims: 主张列表

        Returns:
            置信度分数
        """
        # 平均置信度
        confidences = [c.get("confidence", 1) for c in claims]
        return sum(confidences) / len(confidences) if confidences else 1.0

    def merge_clusters(
        self,
        clusters: list[Cluster],
    ) -> list[Cluster]:
        """
        合并相似簇

        Args:
            clusters: 簇列表

        Returns:
            合并后的簇列表
        """
        # Merge clusters with overlapping claims (Jaccard similarity on claim content)
        if not clusters or len(clusters) < 2:
            return clusters

        merged: list[Cluster] = []
        used: set[int] = set()

        for i, c in enumerate(clusters):
            if i in used:
                continue
            current = c
            for j in range(i + 1, len(clusters)):
                if j in used:
                    continue
                other = clusters[j]
                # Compare by topic similarity and claim overlap
                claims_a = set(cl.get("content", "")[:100] if isinstance(cl, dict) else getattr(cl, "content", "")[:100] for cl in current.claims)
                claims_b = set(cl.get("content", "")[:100] if isinstance(cl, dict) else getattr(cl, "content", "")[:100] for cl in other.claims)
                if not claims_a or not claims_b:
                    continue
                intersection = claims_a & claims_b
                union = claims_a | claims_b
                overlap = len(intersection) / len(union) if union else 0.0
                topic_similar = current.topic.lower() == other.topic.lower()
                if overlap > 0.3 or topic_similar:
                    # Merge: combine claims, average confidence
                    all_claims = list(current.claims) + [cl for cl in other.claims if cl not in current.claims]
                    avg_conf = (current.confidence + other.confidence) / 2
                    current = Cluster(
                        cluster_id=current.cluster_id,
                        topic=current.topic,
                        claims=all_claims,
                        confidence=avg_conf,
                    )
                    used.add(j)
            merged.append(current)
        return merged
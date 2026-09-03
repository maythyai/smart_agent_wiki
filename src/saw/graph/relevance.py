"""
Relevance Model - 4-Signal 相关性模型

基于直接链接、来源重叠、Adamic-Adar 和类型亲和度
"""

from dataclasses import dataclass, field
from enum import Enum
import math


class RelevanceSignal(Enum):
    """相关性信号类型"""
    DIRECT_LINK = "direct_link"       # 直接 wikilink
    SOURCE_OVERLAP = "source_overlap"  # 共享原始来源
    ADAMIC_ADAR = "adamic_adar"        # Adamic-Adar 共同邻居
    TYPE_AFFINITY = "type_affinity"    # 同类型页面


@dataclass
class Edge:
    """图边"""
    source_id: str
    target_id: str
    relevance_score: float = 0.0
    signals: dict[RelevanceSignal, float] = field(default_factory=dict)

    def calculate_total_score(self) -> float:
        """计算总相关性分数"""
        # 权重定义（来自 llm_wiki）
        weights = {
            RelevanceSignal.DIRECT_LINK: 3.0,
            RelevanceSignal.SOURCE_OVERLAP: 4.0,
            RelevanceSignal.ADAMIC_ADAR: 1.5,
            RelevanceSignal.TYPE_AFFINITY: 1.0,
        }

        total = 0.0
        for signal, value in self.signals.items():
            total += value * weights[signal]

        self.relevance_score = total
        return total


@dataclass
class Node:
    """图节点"""
    node_id: str
    title: str
    node_type: str  # entity, concept, source, etc.
    sources: list[str] = field(default_factory=list)  # frontmatter sources[]
    links: list[str] = field(default_factory=list)  # [[wikilinks]]
    degree: int = 0


class RelevanceModel:
    """
    4-Signal 相关性模型

    计算页面间的相关性分数：
    - Direct link (×3.0): [[wikilink]] 直接连接
    - Source overlap (×4.0): frontmatter sources[] 共享
    - Adamic-Adar (×1.5): 共同邻居加权
    - Type affinity (×1.0): 同类型页面
    """

    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.edges: dict[tuple[str, str], Edge] = {}

    def add_node(self, node: Node) -> None:
        """添加节点"""
        self.nodes[node.node_id] = node

    def add_edge(self, source_id: str, target_id: str) -> Edge:
        """添加边"""
        key = (min(source_id, target_id), max(source_id, target_id))

        if key not in self.edges:
            edge = Edge(source_id=source_id, target_id=target_id)
            self.edges[key] = edge

        return self.edges[key]

    def calculate_relevance(self) -> None:
        """计算所有边的相关性"""
        for edge in self.edges.values():
            self._calculate_edge_relevance(edge)

    def _calculate_edge_relevance(self, edge: Edge) -> None:
        """计算单条边的相关性"""
        source = self.nodes.get(edge.source_id)
        target = self.nodes.get(edge.target_id)

        if not source or not target:
            return

        # Signal 1: Direct link
        if target.node_id in source.links or source.node_id in target.links:
            edge.signals[RelevanceSignal.DIRECT_LINK] = 1.0

        # Signal 2: Source overlap
        source_overlap = len(set(source.sources) & set(target.sources))
        if source_overlap > 0:
            edge.signals[RelevanceSignal.SOURCE_OVERLAP] = min(1.0, source_overlap / 3.0)

        # Signal 3: Adamic-Adar
        aa_score = self._adamic_adar(source, target)
        if aa_score > 0:
            edge.signals[RelevanceSignal.ADAMIC_ADAR] = min(1.0, aa_score)

        # Signal 4: Type affinity
        if source.node_type == target.node_type:
            edge.signals[RelevanceSignal.TYPE_AFFINITY] = 1.0

        # 计算总分
        edge.calculate_total_score()

    def _adamic_adar(self, node_a: Node, node_b: Node) -> float:
        """
        Adamic-Adar 相似度

        计算共同邻居的加权贡献：
        AA(a,b) = Σ (1 / log(degree(z))) for z in common_neighbors
        """
        # 找到共同邻居
        neighbors_a = self._get_neighbors(node_a.node_id)
        neighbors_b = self._get_neighbors(node_b.node_id)
        common = neighbors_a & neighbors_b

        if not common:
            return 0.0

        score = 0.0
        for neighbor_id in common:
            neighbor = self.nodes.get(neighbor_id)
            if neighbor and neighbor.degree > 1:
                score += 1.0 / math.log(neighbor.degree)

        return score

    def _get_neighbors(self, node_id: str) -> set[str]:
        """获取节点的邻居"""
        neighbors = set()

        for (a, b), edge in self.edges.items():
            if a == node_id:
                neighbors.add(b)
            elif b == node_id:
                neighbors.add(a)

        return neighbors

    def get_related_nodes(
        self,
        node_id: str,
        top_k: int = 10,
        min_score: float = 1.0,
    ) -> list[tuple[str, float]]:
        """
        获取相关节点

        Args:
            node_id: 起始节点
            top_k: 返回数量
            min_score: 最小分数阈值

        Returns:
            (node_id, score) 列表
        """
        related = []

        for (a, b), edge in self.edges.items():
            if a == node_id:
                related.append((b, edge.relevance_score))
            elif b == node_id:
                related.append((a, edge.relevance_score))

        # 排序并过滤
        related.sort(key=lambda x: -x[1])
        related = [(n, s) for n, s in related if s >= min_score]

        return related[:top_k]

    def expand_from_seeds(
        self,
        seed_ids: list[str],
        max_hops: int = 2,
        decay: float = 0.5,
    ) -> dict[str, float]:
        """
        从种子节点扩展

        Args:
            seed_ids: 种子节点列表
            max_hops: 最大跳数
            decay: 每跳衰减因子

        Returns:
            {node_id: score} 字典
        """
        result: dict[str, float] = {}

        for seed_id in seed_ids:
            if seed_id not in self.nodes:
                continue

            # BFS 扩展
            current_frontier = {seed_id: 1.0}
            visited = {seed_id}

            for hop in range(max_hops):
                next_frontier: dict[str, float] = {}

                for node_id, base_score in current_frontier.items():
                    related = self.get_related_nodes(node_id, top_k=5)

                    for rel_id, rel_score in related:
                        if rel_id in visited:
                            continue

                        score = base_score * rel_score * decay
                        if rel_id not in next_frontier:
                            next_frontier[rel_id] = 0.0
                        next_frontier[rel_id] = max(
                            next_frontier[rel_id],
                            score
                        )

                # 更新结果
                for node_id, score in next_frontier.items():
                    if node_id not in result:
                        result[node_id] = 0.0
                    result[node_id] = max(result[node_id], score)

                visited.update(next_frontier.keys())
                current_frontier = next_frontier

        return result
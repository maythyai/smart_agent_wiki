"""
Graph Insights - 图洞察引擎

发现意外连接和知识缺口
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class InsightType(Enum):
    """洞察类型"""
    SURPRISING_CONNECTION = "surprising_connection"  # 意外连接
    ISOLATED_PAGE = "isolated_page"                   # 孤立页面
    SPARSE_COMMUNITY = "sparse_community"             # 稀疏社区
    BRIDGE_NODE = "bridge_node"                        # 桥接节点
    KNOWLEDGE_GAP = "knowledge_gap"                    # 知识缺口


@dataclass
class GraphInsight:
    """图洞察"""
    insight_id: str
    insight_type: InsightType
    title: str
    description: str
    nodes_involved: list[str]  # 相关节点
    score: float  # 洞察强度
    actionable: bool  # 是否可行动
    research_topic: Optional[str] = None  # Deep Research 主题
    created_at: datetime = field(default_factory=datetime.now)

    def to_markdown(self) -> str:
        """转换为 markdown"""
        icon = {
            InsightType.SURPRISING_CONNECTION: "🔗",
            InsightType.ISOLATED_PAGE: "🏝️",
            InsightType.SPARSE_COMMUNITY: "📊",
            InsightType.BRIDGE_NODE: "🌉",
            InsightType.KNOWLEDGE_GAP: "🕳️",
        }.get(self.insight_type, "💡")

        lines = [
            f"### {icon} {self.title}",
            "",
            self.description,
            "",
            f"**Score**: {self.score:.2f}",
        ]

        if self.nodes_involved:
            lines.append(f"**Nodes**: {len(self.nodes_involved)}")

        if self.actionable and self.research_topic:
            lines.append("")
            lines.append(f"**Research Topic**: {self.research_topic}")
            lines.append("")
            lines.append("[Deep Research](#)")

        return "\n".join(lines)


@dataclass
class InsightsResult:
    """洞察结果"""
    insights: list[GraphInsight] = field(default_factory=list)
    surprising_connections: list[GraphInsight] = field(default_factory=list)
    knowledge_gaps: list[GraphInsight] = field(default_factory=list)
    analysis_time: float = 0.0


class InsightGenerator:
    """
    图洞察生成器

    分析图结构发现：
    1. 意外连接：跨社区、跨类型、边角-中心连接
    2. 知识缺口：孤立页面、稀疏社区、桥接节点
    """

    # 低内聚度阈值
    LOW_COHESION_THRESHOLD = 0.15

    # 孤立页面度阈值
    ISOLATED_DEGREE_THRESHOLD = 1

    # 桥接节点阈值
    BRIDGE_THRESHOLD = 3

    def __init__(self):
        self.insights: list[GraphInsight] = []

    def generate(
        self,
        nodes: dict[str, dict],
        edges: dict[tuple[str, str], dict],
        communities: list[dict],
        node_communities: dict[str, int],
    ) -> InsightsResult:
        """
        生成洞察

        Args:
            nodes: 节点数据
            edges: 边数据
            communities: 社区列表
            node_communities: 节点->社区映射

        Returns:
            洞察结果
        """
        from time import time
        start_time = time()

        self.insights = []

        # 1. 发现意外连接
        self._find_surprising_connections(nodes, edges, node_communities)

        # 2. 发现孤立页面
        self._find_isolated_pages(nodes, edges)

        # 3. 发现稀疏社区
        self._find_sparse_communities(communities)

        # 4. 发现桥接节点
        self._find_bridge_nodes(nodes, edges, node_communities)

        analysis_time = time() - start_time

        # 分类
        surprising = [
            i for i in self.insights
            if i.insight_type == InsightType.SURPRISING_CONNECTION
        ]

        gaps = [
            i for i in self.insights
            if i.insight_type in (
                InsightType.ISOLATED_PAGE,
                InsightType.SPARSE_COMMUNITY,
                InsightType.BRIDGE_NODE,
                InsightType.KNOWLEDGE_GAP,
            )
        ]

        return InsightsResult(
            insights=self.insights,
            surprising_connections=surprising,
            knowledge_gaps=gaps,
            analysis_time=analysis_time,
        )

    def _find_surprising_connections(
        self,
        nodes: dict[str, dict],
        edges: dict[tuple[str, str], dict],
        node_communities: dict[str, int],
    ) -> None:
        """发现意外连接"""
        for (a, b), edge_data in edges.items():
            # 计算意外分数
            surprise_score = self._calculate_surprise(
                a, b, nodes, node_communities
            )

            if surprise_score < 0.3:
                continue

            insight = GraphInsight(
                insight_id=f"surprise-{len(self.insights)}",
                insight_type=InsightType.SURPRISING_CONNECTION,
                title=f"Unexpected: {nodes.get(a, {}).get('title', a)} ↔ {nodes.get(b, {}).get('title', b)}",
                description=f"Cross-community or cross-type connection with high surprise score.",
                nodes_involved=[a, b],
                score=surprise_score,
                actionable=True,
            )

            self.insights.append(insight)

    def _calculate_surprise(
        self,
        node_a: str,
        node_b: str,
        nodes: dict[str, dict],
        node_communities: dict[str, int],
    ) -> float:
        """
        计算意外分数

        组合多个因素：
        - 跨社区连接
        - 跨类型连接
        - 边角-中心连接
        """
        score = 0.0

        # 跨社区
        comm_a = node_communities.get(node_a, -1)
        comm_b = node_communities.get(node_b, -1)
        if comm_a != comm_b and comm_a >= 0 and comm_b >= 0:
            score += 0.5

        # 跨类型
        type_a = nodes.get(node_a, {}).get("type", "unknown")
        type_b = nodes.get(node_b, {}).get("type", "unknown")
        if type_a != type_b:
            score += 0.3

        # 边角-中心（基于度）
        degree_a = nodes.get(node_a, {}).get("degree", 0)
        degree_b = nodes.get(node_b, {}).get("degree", 0)

        if degree_a <= 2 and degree_b >= 5:
            score += 0.2
        elif degree_b <= 2 and degree_a >= 5:
            score += 0.2

        return min(1.0, score)

    def _find_isolated_pages(
        self,
        nodes: dict[str, dict],
        edges: dict[tuple[str, str], dict],
    ) -> None:
        """发现孤立页面"""
        for node_id, node_data in nodes.items():
            degree = self._count_degree(node_id, edges)

            if degree <= self.ISOLATED_DEGREE_THRESHOLD:
                title = node_data.get("title", node_id)

                insight = GraphInsight(
                    insight_id=f"isolated-{len(self.insights)}",
                    insight_type=InsightType.ISOLATED_PAGE,
                    title=f"Isolated: {title}",
                    description=f"Page has only {degree} connections. May need more context.",
                    nodes_involved=[node_id],
                    score=1.0 - (degree / 5),
                    actionable=True,
                    research_topic=f"Find connections for '{title}'",
                )

                self.insights.append(insight)

    def _find_sparse_communities(
        self,
        communities: list[dict],
    ) -> None:
        """发现稀疏社区"""
        for community in communities:
            cohesion = community.get("cohesion", 1.0)
            members = community.get("members", [])

            if cohesion < self.LOW_COHESION_THRESHOLD and len(members) >= 3:
                label = community.get("label", "Unknown")

                insight = GraphInsight(
                    insight_id=f"sparse-{len(self.insights)}",
                    insight_type=InsightType.SPARSE_COMMUNITY,
                    title=f"Sparse Cluster: {label}",
                    description=f"Community has low cohesion ({cohesion:.2f}). "
                                f"Consider adding cross-references.",
                    nodes_involved=members,
                    score=1.0 - cohesion,
                    actionable=True,
                    research_topic=f"Expand knowledge about '{label}'",
                )

                self.insights.append(insight)

    def _find_bridge_nodes(
        self,
        nodes: dict[str, dict],
        edges: dict[tuple[str, str], dict],
        node_communities: dict[str, int],
    ) -> None:
        """发现桥接节点（连接多个社区的节点）."""
        # 计算每个节点连接的社区数
        node_connections: dict[str, set[int]] = {}

        for node_id in nodes.keys():
            comm = node_communities.get(node_id, -1)
            node_connections[node_id] = {comm}

        # 从 edges 扩展：每条边把对端社区加入本端连接集。此前代码错误地
        # 遍历 ``nodes.keys()``（字符串）并按 (a, b) 解包 → ValueError。
        for (a, b) in edges.keys():
            ca = node_communities.get(a)
            cb = node_communities.get(b)
            if ca is not None:
                node_connections.setdefault(a, set()).add(ca)
            if cb is not None:
                node_connections.setdefault(b, set()).add(cb)

        # 识别桥接节点
        for node_id, connected_comms in node_connections.items():
            if len(connected_comms) >= self.BRIDGE_THRESHOLD:
                title = nodes.get(node_id, {}).get("title", node_id)

                insight = GraphInsight(
                    insight_id=f"bridge-{len(self.insights)}",
                    insight_type=InsightType.BRIDGE_NODE,
                    title=f"Bridge: {title}",
                    description=f"Node connects {len(connected_comms)} knowledge clusters. "
                                f"Critical junction worth deeper research.",
                    nodes_involved=[node_id],
                    score=len(connected_comms) / 5,
                    actionable=True,
                    research_topic=f"Deep research on '{title}'",
                )

                self.insights.append(insight)

    def _count_degree(
        self,
        node_id: str,
        edges: dict[tuple[str, str], dict],
    ) -> int:
        """计算节点度"""
        count = 0

        for (a, b) in edges.keys():
            if a == node_id or b == node_id:
                count += 1

        return count

    def dismiss_insight(self, insight_id: str) -> bool:
        """标记洞察为已处理"""
        for insight in self.insights:
            if insight.insight_id == insight_id:
                self.insights.remove(insight)
                return True

        return False

    def get_top_insights(self, limit: int = 10) -> list[GraphInsight]:
        """获取最强洞察"""
        sorted_insights = sorted(
            self.insights,
            key=lambda x: -x.score
        )
        return sorted_insights[:limit]
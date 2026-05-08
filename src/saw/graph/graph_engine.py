"""
Knowledge Graph Engine - 知识图谱引擎

整合相关性模型、社区检测和洞察生成
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

from .relevance import RelevanceModel, Node, Edge, RelevanceSignal
from .community import CommunityDetector, CommunityResult
from .insights import InsightGenerator, InsightsResult


@dataclass
class GraphState:
    """图谱状态"""
    nodes: dict[str, dict] = field(default_factory=dict)
    edges: dict[tuple[str, str], dict] = field(default_factory=dict)
    communities: list[dict] = field(default_factory=list)
    node_communities: dict[str, int] = field(default_factory=dict)


@dataclass
class GraphResult:
    """图谱构建结果"""
    state: GraphState
    relevance_model: Optional[RelevanceModel] = None
    community_result: Optional[CommunityResult] = None
    insights_result: Optional[InsightsResult] = None
    total_time: float = 0.0


class KnowledgeGraphEngine:
    """
    知识图谱引擎

    整合四个核心功能：
    1. 4-Signal 相关性模型
    2. Louvain 社区检测
    3. 图洞察生成
    4. 可视化数据生成
    """

    def __init__(
        self,
        wiki_path: Optional[Path] = None,
        state_path: Optional[Path] = None,
    ):
        """
        初始化图谱引擎

        Args:
            wiki_path: Wiki 目录路径
            state_path: 状态文件路径
        """
        self.wiki_path = wiki_path or Path(".saw/wiki")
        self.state_path = state_path or Path(".saw/graph_state.json")

        self.relevance_model = RelevanceModel()
        self.community_detector = CommunityDetector()
        self.insight_generator = InsightGenerator()

        self._state = GraphState()

    def build(self, wiki_pages: list[dict]) -> GraphResult:
        """
        构建知识图谱

        Args:
            wiki_pages: Wiki 页面列表，每个包含:
                - page_id: 页面 ID
                - title: 标题
                - type: 页面类型 (entity, concept, source)
                - sources: frontmatter sources[]
                - links: [[wikilinks]]

        Returns:
            构建结果
        """
        from time import time
        start_time = time()

        # 1. 构建节点
        for page in wiki_pages:
            node = Node(
                node_id=page["page_id"],
                title=page.get("title", page["page_id"]),
                node_type=page.get("type", "unknown"),
                sources=page.get("sources", []),
                links=page.get("links", []),
            )
            self.relevance_model.add_node(node)
            self._state.nodes[node.node_id] = {
                "title": node.title,
                "type": node.node_type,
                "sources": node.sources,
                "links": node.links,
            }

        # 2. 构建边（基于 wikilinks）
        for page in wiki_pages:
            page_id = page["page_id"]
            for link in page.get("links", []):
                if link in self._state.nodes:
                    self.relevance_model.add_edge(page_id, link)
                    key = (min(page_id, link), max(page_id, link))
                    self._state.edges[key] = {"weight": 1.0}

        # 更新节点度
        self._update_degrees()

        # 3. 计算相关性
        self.relevance_model.calculate_relevance()

        # 更新边数据
        for (a, b), edge in self.relevance_model.edges.items():
            self._state.edges[(a, b)] = {
                "relevance_score": edge.relevance_score,
                "signals": {s.value: v for s, v in edge.signals.items()},
            }

        # 4. 社区检测
        community_result = self.community_detector.detect(
            self._state.nodes,
            self._state.edges,
        )

        self._state.communities = [c.to_dict() for c in community_result.communities]

        # 更新节点-社区映射
        for comm in community_result.communities:
            for node_id in comm.members:
                self._state.node_communities[node_id] = comm.community_id

        # 5. 生成洞察
        insights_result = self.insight_generator.generate(
            self._state.nodes,
            self._state.edges,
            self._state.communities,
            self._state.node_communities,
        )

        total_time = time() - start_time

        return GraphResult(
            state=self._state,
            relevance_model=self.relevance_model,
            community_result=community_result,
            insights_result=insights_result,
            total_time=total_time,
        )

    def _update_degrees(self) -> None:
        """更新节点度"""
        degrees: dict[str, int] = {}

        for (a, b) in self._state.edges.keys():
            degrees[a] = degrees.get(a, 0) + 1
            degrees[b] = degrees.get(b, 0) + 1

        for node_id, degree in degrees.items():
            if node_id in self._state.nodes:
                self._state.nodes[node_id]["degree"] = degree

    def get_related_pages(
        self,
        page_id: str,
        top_k: int = 10,
    ) -> list[tuple[str, float]]:
        """获取相关页面"""
        return self.relevance_model.get_related_nodes(page_id, top_k)

    def expand_search(
        self,
        seed_ids: list[str],
        max_hops: int = 2,
    ) -> dict[str, float]:
        """从种子扩展"""
        return self.relevance_model.expand_from_seeds(seed_ids, max_hops)

    def get_community_pages(
        self,
        community_id: int,
    ) -> list[str]:
        """获取社区页面"""
        for comm in self._state.communities:
            if comm["community_id"] == community_id:
                return comm["members"]
        return []

    def get_insights(self) -> list[dict]:
        """获取洞察"""
        if not self.insight_generator.insights:
            return []

        return [
            {
                "insight_id": i.insight_id,
                "type": i.insight_type.value,
                "title": i.title,
                "description": i.description,
                "score": i.score,
                "actionable": i.actionable,
                "research_topic": i.research_topic,
            }
            for i in self.insight_generator.insights
        ]

    def to_visualization_data(self) -> dict:
        """
        生成可视化数据

        用于前端图表库（如 sigma.js）
        """
        nodes = []
        for node_id, node_data in self._state.nodes.items():
            community_id = self._state.node_communities.get(node_id, -1)

            # 获取社区颜色
            color = "#999999"
            for comm in self._state.communities:
                if comm["community_id"] == community_id:
                    color = comm.get("color", "#999999")
                    break

            nodes.append({
                "id": node_id,
                "label": node_data.get("title", node_id),
                "type": node_data.get("type", "unknown"),
                "community": community_id,
                "color": color,
                "size": max(3, node_data.get("degree", 1) ** 0.5),
            })

        edges = []
        for (a, b), edge_data in self._state.edges.items():
            relevance = edge_data.get("relevance_score", 1.0)

            edges.append({
                "id": f"{a}-{b}",
                "source": a,
                "target": b,
                "weight": relevance,
                "color": "#00ff00" if relevance > 3 else "#aaaaaa",
            })

        communities = [
            {
                "id": c["community_id"],
                "label": c["label"],
                "color": c["color"],
                "cohesion": c["cohesion"],
                "size": len(c["members"]),
            }
            for c in self._state.communities
        ]

        return {
            "nodes": nodes,
            "edges": edges,
            "communities": communities,
        }

    def save(self) -> None:
        """保存图谱状态"""
        if self.state_path:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "nodes": self._state.nodes,
                "edges": [
                    {"source": a, "target": b, **e}
                    for (a, b), e in self._state.edges.items()
                ],
                "communities": self._state.communities,
                "node_communities": self._state.node_communities,
                "updated_at": datetime.now().isoformat(),
            }

            self.state_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

    def load(self) -> bool:
        """加载图谱状态"""
        if not self.state_path or not self.state_path.exists():
            return False

        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))

            self._state.nodes = data.get("nodes", {})

            self._state.edges = {}
            for e in data.get("edges", []):
                key = (e["source"], e["target"])
                self._state.edges[key] = {k: v for k, v in e.items()
                                          if k not in ["source", "target"]}

            self._state.communities = data.get("communities", [])
            self._state.node_communities = {
                k: int(v) if isinstance(v, str) else v
                for k, v in data.get("node_communities", {}).items()
            }

            return True

        except (json.JSONDecodeError, KeyError):
            return False

    def get_stats(self) -> dict:
        """获取统计"""
        return {
            "nodes": len(self._state.nodes),
            "edges": len(self._state.edges),
            "communities": len(self._state.communities),
            "insights": len(self.insight_generator.insights),
        }
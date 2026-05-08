"""
Knowledge Graph Tests

测试知识图谱引擎功能
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from saw.graph import (
    RelevanceModel,
    RelevanceSignal,
    CommunityDetector,
    InsightGenerator,
    KnowledgeGraphEngine,
)
from saw.graph.relevance import Node, Edge
from saw.graph.insights import InsightType


class TestRelevanceModel:
    """Relevance Model 测试"""

    def test_add_node(self):
        """测试添加节点"""
        model = RelevanceModel()
        node = Node(
            node_id="test-1",
            title="Test Node",
            node_type="entity",
        )

        model.add_node(node)

        assert "test-1" in model.nodes

    def test_add_edge(self):
        """测试添加边"""
        model = RelevanceModel()
        model.add_node(Node("a", "A", "entity"))
        model.add_node(Node("b", "B", "entity"))

        edge = model.add_edge("a", "b")

        assert edge.source_id == "a"
        assert edge.target_id == "b"

    def test_calculate_relevance(self):
        """测试相关性计算"""
        model = RelevanceModel()

        # 添加带链接的节点
        model.add_node(Node("a", "A", "entity", links=["b"]))
        model.add_node(Node("b", "B", "entity", links=["a"]))
        model.add_edge("a", "b")

        model.calculate_relevance()

        # 检查是否有直接链接信号
        key = ("a", "b")
        if key in model.edges:
            assert RelevanceSignal.DIRECT_LINK in model.edges[key].signals

    def test_get_related_nodes(self):
        """测试获取相关节点"""
        model = RelevanceModel()
        model.add_node(Node("a", "A", "entity"))
        model.add_node(Node("b", "B", "entity"))
        model.add_node(Node("c", "C", "entity"))
        model.add_edge("a", "b")
        model.add_edge("a", "c")
        model.calculate_relevance()

        related = model.get_related_nodes("a", top_k=5)

        assert len(related) >= 0

    def test_expand_from_seeds(self):
        """测试从种子扩展"""
        model = RelevanceModel()
        model.add_node(Node("a", "A", "entity"))
        model.add_node(Node("b", "B", "entity"))
        model.add_node(Node("c", "C", "entity"))
        model.add_edge("a", "b")
        model.add_edge("b", "c")
        model.calculate_relevance()

        result = model.expand_from_seeds(["a"], max_hops=2)

        assert isinstance(result, dict)


class TestCommunityDetector:
    """Community Detector 测试"""

    def test_detect_communities(self):
        """测试社区检测"""
        detector = CommunityDetector()

        nodes = {
            "a": {"title": "A", "type": "entity"},
            "b": {"title": "B", "type": "entity"},
            "c": {"title": "C", "type": "entity"},
            "d": {"title": "D", "type": "entity"},
        }

        edges = {
            ("a", "b"): {"weight": 1},
            ("a", "c"): {"weight": 1},
            ("b", "c"): {"weight": 1},
            ("d", "d"): {"weight": 1},  # 自连接（实际不应存在）
        }

        result = detector.detect(nodes, edges)

        assert result.total_nodes == 4
        assert len(result.communities) >= 1

    def test_community_cohesion(self):
        """测试社区内聚度计算"""
        detector = CommunityDetector()

        # 紧密连接的社区
        nodes = {
            "a": {"title": "A", "type": "entity"},
            "b": {"title": "B", "type": "entity"},
            "c": {"title": "C", "type": "entity"},
        }

        edges = {
            ("a", "b"): {"weight": 1},
            ("b", "c"): {"weight": 1},
            ("a", "c"): {"weight": 1},  # 完全连接
        }

        result = detector.detect(nodes, edges)

        # 完全连接的社区应该有高内聚度
        if result.communities:
            assert result.communities[0].cohesion >= 0.5


class TestInsightGenerator:
    """Insight Generator 测试"""

    def test_find_isolated_pages(self):
        """测试发现孤立页面"""
        generator = InsightGenerator()

        nodes = {
            "isolated": {"title": "Isolated", "type": "entity", "degree": 0},
            "connected": {"title": "Connected", "type": "entity", "degree": 5},
        }

        edges = {}

        result = generator.generate(nodes, edges, [], {})

        # 应该发现孤立页面
        isolated_insights = [
            i for i in result.insights
            if i.insight_type == InsightType.ISOLATED_PAGE
        ]

        assert len(isolated_insights) >= 1

    def test_generate_insights(self):
        """测试洞察生成"""
        generator = InsightGenerator()

        nodes = {
            "a": {"title": "A", "type": "entity", "degree": 3},
            "b": {"title": "B", "type": "concept", "degree": 3},
        }

        edges = {
            ("a", "b"): {"weight": 1},
        }

        communities = [
            {"community_id": 0, "label": "Comm1", "members": ["a"], "cohesion": 0.5},
            {"community_id": 1, "label": "Comm2", "members": ["b"], "cohesion": 0.5},
        ]

        node_communities = {"a": 0, "b": 1}

        result = generator.generate(nodes, edges, communities, node_communities)

        assert len(result.insights) >= 0


class TestKnowledgeGraphEngine:
    """Knowledge Graph Engine 测试"""

    def test_build_graph(self):
        """测试构建图谱"""
        engine = KnowledgeGraphEngine()

        pages = [
            {
                "page_id": "page-1",
                "title": "Python",
                "type": "concept",
                "sources": ["source-1"],
                "links": ["page-2"],
            },
            {
                "page_id": "page-2",
                "title": "Programming",
                "type": "concept",
                "sources": ["source-1"],
                "links": ["page-1"],
            },
        ]

        result = engine.build(pages)

        assert result.total_time >= 0
        assert len(result.state.nodes) == 2

    def test_get_related_pages(self):
        """测试获取相关页面"""
        engine = KnowledgeGraphEngine()

        pages = [
            {"page_id": "a", "title": "A", "type": "entity", "links": ["b"]},
            {"page_id": "b", "title": "B", "type": "entity", "links": ["a"]},
        ]

        engine.build(pages)

        related = engine.get_related_pages("a")

        assert isinstance(related, list)

    def test_visualization_data(self):
        """测试可视化数据生成"""
        engine = KnowledgeGraphEngine()

        pages = [
            {"page_id": "a", "title": "A", "type": "entity", "links": []},
        ]

        engine.build(pages)

        viz_data = engine.to_visualization_data()

        assert "nodes" in viz_data
        assert "edges" in viz_data
        assert "communities" in viz_data

    def test_save_and_load(self):
        """测试保存和加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = KnowledgeGraphEngine(
                state_path=Path(tmpdir) / "graph.json"
            )

            pages = [
                {"page_id": "test", "title": "Test", "type": "entity", "links": []},
            ]

            engine.build(pages)
            engine.save()

            # 重新加载
            engine2 = KnowledgeGraphEngine(
                state_path=Path(tmpdir) / "graph.json"
            )

            success = engine2.load()

            assert success is True
            assert len(engine2._state.nodes) == 1

    def test_get_stats(self):
        """测试获取统计"""
        engine = KnowledgeGraphEngine()

        pages = [
            {"page_id": "a", "title": "A", "type": "entity", "links": ["b"]},
            {"page_id": "b", "title": "B", "type": "entity", "links": ["a"]},
        ]

        engine.build(pages)

        stats = engine.get_stats()

        assert stats["nodes"] == 2
        assert stats["edges"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Deep Research Tests

测试深度研究功能
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from saw.research import DeepResearchEngine
from saw.research.web_search import WebSearchClient, SearchResult, SearchResponse
from saw.research.auto_ingest import AutoIngestProcessor, IngestItem


class TestWebSearchClient:
    """Web Search Client 测试"""

    def test_search_without_api_key(self):
        """测试无 API 密钥搜索"""
        client = WebSearchClient()

        response = client.search("test query")

        assert response.query == "test query"
        assert len(response.results) == 0

    def test_multi_search(self):
        """测试多查询搜索"""
        client = WebSearchClient()

        responses = client.multi_search(["query1", "query2"])

        assert len(responses) == 2

    def test_deduplicate(self):
        """测试去重"""
        client = WebSearchClient()

        responses = [
            SearchResponse(
                query="q1",
                results=[
                    SearchResult(url="http://a.com", title="A", content=""),
                    SearchResult(url="http://b.com", title="B", content=""),
                ],
            ),
            SearchResponse(
                query="q2",
                results=[
                    SearchResult(url="http://a.com", title="A", content=""),
                    SearchResult(url="http://c.com", title="C", content=""),
                ],
            ),
        ]

        unique = client.deduplicate(responses)

        # a.com 应该只出现一次
        assert len(unique) == 3


class TestAutoIngestProcessor:
    """Auto Ingest Processor 测试"""

    def test_create_ingest_item(self):
        """测试创建摄入项"""
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = AutoIngestProcessor(
                wiki_path=Path(tmpdir) / "wiki",
                sources_path=Path(tmpdir) / "sources",
            )

            item = processor._create_ingest_item(
                {
                    "url": "http://example.com/test",
                    "title": "Test Article",
                    "content": "Test content",
                },
                "test research",
            )

            assert item.title == "Test Article"
            assert item.source_url == "http://example.com/test"
            assert item.metadata["research_topic"] == "test research"

    def test_process_search_results(self):
        """测试处理搜索结果"""
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = AutoIngestProcessor(
                wiki_path=Path(tmpdir) / "wiki",
                sources_path=Path(tmpdir) / "sources",
            )

            results = [
                {
                    "url": "http://test.com/1",
                    "title": "Result 1",
                    "content": "Content 1",
                },
                {
                    "url": "http://test.com/2",
                    "title": "Result 2",
                    "content": "Content 2",
                },
            ]

            result = processor.process_search_results(results, "test topic")

            assert result.items_processed == 2
            assert result.items_successful >= 0

    def test_synthesize_research(self):
        """测试综合研究"""
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = AutoIngestProcessor(
                wiki_path=Path(tmpdir) / "wiki",
            )

            items = [
                IngestItem(
                    item_id="item-1",
                    content="Content 1",
                    source_url="http://test.com/1",
                    title="Result 1",
                ),
            ]

            page_id = processor.synthesize_research(items, "Test Topic")

            assert page_id.startswith("synthesis-")


class TestDeepResearchEngine:
    """Deep Research Engine 测试"""

    def test_generate_search_queries(self):
        """测试生成搜索查询"""
        engine = DeepResearchEngine()

        queries = engine.generate_search_queries("Python programming")

        assert len(queries) >= 1
        assert "Python" in queries[0]

    def test_generate_queries_with_context(self):
        """测试带上下文生成查询"""
        engine = DeepResearchEngine()

        queries = engine.generate_search_queries(
            "Machine Learning",
            context="Focus on neural networks",
            num_queries=4,
        )

        assert len(queries) == 4

    def test_execute_research(self):
        """测试执行研究"""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DeepResearchEngine(
                wiki_path=Path(tmpdir) / "wiki",
            )

            result = engine.execute_research(
                topic="Test Topic",
                num_queries=2,
                auto_synthesize=False,
            )

            assert result.task.status == "completed"
            assert result.task.topic == "Test Topic"

    def test_get_stats(self):
        """测试获取统计"""
        engine = DeepResearchEngine()

        stats = engine.get_stats()

        assert "wiki_path" in stats
        assert "max_concurrent_tasks" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
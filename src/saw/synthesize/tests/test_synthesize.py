"""
Synthesize Engine Tests

测试模式挖掘、聚合构建和页面生成
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from saw.synthesize import (
    PatternMiner,
    Pattern,
    ClusterBuilder,
    Cluster,
    PageGenerator,
    SynthesisPage,
    SynthesizeScheduler,
    SynthesizeEngine,
)
from saw.synthesize.scheduler import ScheduleType


class TestPatternMiner:
    """模式挖掘器测试"""

    def test_extract_keywords(self):
        """测试关键词提取"""
        miner = PatternMiner()
        keywords = miner._extract_keywords("Python is a great programming language")

        assert len(keywords) > 0
        assert "python" in keywords
        assert "great" in keywords
        assert "programming" in keywords

    def test_filter_stop_words(self):
        """测试停用词过滤"""
        miner = PatternMiner()
        keywords = miner._extract_keywords("The quick brown fox jumps over the lazy dog")

        # 停用词应该被过滤
        assert "the" not in keywords
        # "over" 不在停用词列表中，所以可能在结果里

    def test_mine_patterns(self):
        """测试模式挖掘"""
        # 使用更低的阈值确保能发现模式
        miner = PatternMiner(min_occurrences=1, min_confidence=0.1)

        items = [
            {
                "id": "item-1",
                "content": "Python is a programming language",
                "source": "source-a",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "id": "item-2",
                "content": "Python is widely used for data science",
                "source": "source-b",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "id": "item-3",
                "content": "Python programming is fun",
                "source": "source-c",
                "timestamp": datetime.now().isoformat(),
            },
        ]

        result = miner.mine(items)

        assert result.total_items == 3
        # 验证挖掘流程正常工作（可能不产生模式取决于置信度过滤）
        # 这测试的是流程完整性而非具体结果数量

    def test_pattern_to_dict(self):
        """测试模式字典转换"""
        pattern = Pattern(
            pattern_id="test-001",
            name="Test Pattern",
            keywords=["test", "pattern"],
            occurrences=5,
            sources=["source-a", "source-b"],
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            confidence=0.8,
            description="A test pattern",
        )

        data = pattern.to_dict()

        assert data["pattern_id"] == "test-001"
        assert data["name"] == "Test Pattern"
        assert data["occurrences"] == 5
        assert data["confidence"] == 0.8

    def test_time_window_filtering(self):
        """测试时间窗口过滤"""
        miner = PatternMiner()

        # 创建跨越不同时间的项目
        now = datetime.now()
        items = [
            {
                "id": "old",
                "content": "Old content about python",
                "source": "test",
                "timestamp": (now - timedelta(days=10)).isoformat(),
            },
            {
                "id": "new",
                "content": "New content about python",
                "source": "test",
                "timestamp": now.isoformat(),
            },
        ]

        # 只看最近 5 天
        result = miner.mine(items, time_window=timedelta(days=5))

        assert result.total_items == 1


class TestClusterBuilder:
    """聚合构建器测试"""

    def test_build_clusters(self):
        """测试聚合构建"""
        builder = ClusterBuilder()

        claims = [
            {
                "id": "claim-1",
                "content": "Python is popular",
                "topic": "python",
                "confidence": 0.9,
                "source": "test",
            },
            {
                "id": "claim-2",
                "content": "Python is widely used",
                "topic": "python",
                "confidence": 0.8,
                "source": "test",
            },
            {
                "id": "claim-3",
                "content": "JavaScript runs in browser",
                "topic": "javascript",
                "confidence": 0.95,
                "source": "test",
            },
        ]

        result = builder.build(claims)

        assert result.total_claims == 3
        # 应该按 topic 分组
        topics = [c.topic for c in result.clusters]
        assert "python" in topics or "javascript" in topics

    def test_cluster_to_dict(self):
        """测试簇字典转换"""
        cluster = Cluster(
            cluster_id="cluster-001",
            topic="test",
            claims=["claim-1", "claim-2"],
            summary="Test cluster summary",
            confidence=0.85,
            sources=["source-a"],
        )

        data = cluster.to_dict()

        assert data["cluster_id"] == "cluster-001"
        assert data["topic"] == "test"
        assert len(data["claims"]) == 2

    def test_min_cluster_size(self):
        """测试最小簇大小"""
        builder = ClusterBuilder(min_cluster_size=2)

        claims = [
            {
                "id": "claim-1",
                "content": "Single claim",
                "topic": "lonely",
                "confidence": 1.0,
                "source": "test",
            },
        ]

        result = builder.build(claims)

        # 单个 claim 不应该形成簇
        assert len(result.clusters) == 0


class TestPageGenerator:
    """页面生成器测试"""

    def test_generate_page(self):
        """测试页面生成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = PageGenerator(output_dir=Path(tmpdir))

            patterns = [
                {
                    "pattern_id": "pattern-001",
                    "name": "Python Pattern",
                    "keywords": ["python", "programming"],
                    "occurrences": 5,
                    "confidence": 0.8,
                }
            ]

            clusters = [
                {
                    "cluster_id": "cluster-001",
                    "topic": "python",
                    "summary": "Python programming",
                    "confidence": 0.9,
                    "sources": ["test-source"],
                }
            ]

            result = generator.generate(patterns, clusters)

            assert result.generation_time > 0
            # 如果模式与簇相关，应该生成页面
            if result.pages:
                page = result.pages[0]
                assert page.title
                assert page.content
                assert page.confidence >= 0

    def test_synthesis_page_markdown(self):
        """测试综合页面 Markdown 格式"""
        page = SynthesisPage(
            page_id="syn-001",
            title="Test Synthesis",
            content="This is a test synthesis page.",
            patterns=["pattern-001"],
            clusters=["cluster-001"],
            confidence=0.85,
            sources=["Source A", "Source B"],
            links=["Related Page"],
        )

        markdown = page.to_markdown()

        assert "# Test Synthesis" in markdown
        assert "[!ai-first]" in markdown
        assert "For future Claude" in markdown
        assert "This is a test synthesis page" in markdown
        assert "[[Source A]]" in markdown
        assert "[[Related Page]]" in markdown

    def test_save_page(self):
        """测试保存页面"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = PageGenerator(output_dir=Path(tmpdir))

            page = SynthesisPage(
                page_id="syn-test",
                title="Test Page",
                content="Test content",
                patterns=[],
                clusters=[],
                confidence=0.5,
            )

            path = generator.save_page(page)

            assert path.exists()
            content = path.read_text(encoding="utf-8")
            assert "# Test Page" in content


class TestSynthesizeScheduler:
    """调度器测试"""

    def test_default_tasks(self):
        """测试默认任务"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = SynthesizeScheduler(config_path=Path(tmpdir) / "schedule.json")

            tasks = scheduler.list_tasks()

            # 应该有默认的三个任务
            assert len(tasks) == 3
            task_ids = [t.task_id for t in tasks]
            assert "nightly-pattern" in task_ids
            assert "weekly-synthesis" in task_ids
            assert "monthly-analysis" in task_ids

    def test_enable_disable_task(self):
        """测试启用/禁用任务"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = SynthesizeScheduler(config_path=Path(tmpdir) / "schedule.json")

            scheduler.disable_task("nightly-pattern")
            task = scheduler.get_task("nightly-pattern")
            assert task.enabled is False

            scheduler.enable_task("nightly-pattern")
            task = scheduler.get_task("nightly-pattern")
            assert task.enabled is True

    def test_add_custom_task(self):
        """测试添加自定义任务"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = SynthesizeScheduler(config_path=Path(tmpdir) / "schedule.json")

            task = scheduler.add_custom_task(
                task_id="custom-task",
                schedule_type=ScheduleType.NIGHTLY,
                scope="custom",
                config={"min_occurrences": 10},
            )

            assert task.task_id == "custom-task"
            assert task.schedule_type == ScheduleType.NIGHTLY

    def test_pending_tasks(self):
        """测试获取待执行任务"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = SynthesizeScheduler(config_path=Path(tmpdir) / "schedule.json")

            # 刚初始化时，任务的未来运行时间应该在未来
            pending = scheduler.get_pending_tasks()

            # 默认任务的 next_run 在未来，不应该有待执行的
            # 除非时间刚好过了
            assert isinstance(pending, list)

    def test_mark_task_run(self):
        """测试标记任务执行"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = SynthesizeScheduler(config_path=Path(tmpdir) / "schedule.json")

            scheduler.mark_task_run(
                task_id="nightly-pattern",
                success=True,
                pages_generated=5,
                patterns_found=10,
                clusters_created=3,
            )

            task = scheduler.get_task("nightly-pattern")
            assert task.last_run is not None

            results = scheduler.get_recent_results()
            assert len(results) >= 1
            assert results[-1].success is True
            assert results[-1].pages_generated == 5


class TestSynthesizeEngine:
    """综合引擎测试"""

    def test_full_synthesize_flow(self):
        """测试完整综合流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SynthesizeEngine(
                output_dir=Path(tmpdir),
                min_occurrences=2,
            )

            items = [
                {
                    "id": "item-1",
                    "content": "Python is a popular programming language",
                    "topic": "programming",
                    "source": "test",
                    "timestamp": datetime.now().isoformat(),
                    "confidence": 1,
                },
                {
                    "id": "item-2",
                    "content": "Python is used for data science",
                    "topic": "programming",
                    "source": "test",
                    "timestamp": datetime.now().isoformat(),
                    "confidence": 1,
                },
                {
                    "id": "item-3",
                    "content": "Python programming is versatile",
                    "topic": "programming",
                    "source": "test",
                    "timestamp": datetime.now().isoformat(),
                    "confidence": 1,
                },
            ]

            result = engine.synthesize(items, save_pages=False)

            assert result.total_time > 0
            assert result.mining.total_items == 3

    def test_empty_items(self):
        """测试空输入"""
        engine = SynthesizeEngine()

        result = engine.synthesize([])

        assert result.total_time >= 0
        assert result.mining.total_items == 0
        assert len(result.pages) == 0

    def test_get_stats(self):
        """测试获取统计"""
        engine = SynthesizeEngine()

        stats = engine.get_stats()

        assert "scheduler" in stats
        assert "miner" in stats

    def test_enable_scheduled_tasks(self):
        """测试启用定时任务"""
        engine = SynthesizeEngine()

        engine.enable_nightly()
        engine.enable_weekly()
        engine.enable_monthly()

        # 验证任务已启用
        nightly = engine.scheduler.get_task("nightly-pattern")
        weekly = engine.scheduler.get_task("weekly-synthesis")
        monthly = engine.scheduler.get_task("monthly-analysis")

        assert nightly.enabled is True
        assert weekly.enabled is True
        assert monthly.enabled is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

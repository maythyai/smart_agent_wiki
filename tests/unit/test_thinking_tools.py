"""
Thinking Tools Tests

测试批判性思维工具集
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from saw.drivers.mcp.tools.challenge import challenge_tool, ChallengeResult
from saw.drivers.mcp.tools.emerge import emerge_tool, EmergeResult
from saw.drivers.mcp.tools.connect import connect_tool, ConnectResult
from saw.drivers.mcp.tools.graduate import graduate_tool, GraduateResult
from saw.drivers.mcp.tools.context import context_tool
from saw.context.loader import ContextLoader, ContextLevel


class TestChallengeTool:
    """Challenge Tool 测试"""

    def test_challenge_basic(self):
        """测试基本挑战功能"""
        result = challenge_tool("Python is the best language")

        assert result.idea == "Python is the best language"
        assert result.confidence_score >= 0
        assert len(result.alternative_perspectives) > 0

    def test_challenge_with_history(self):
        """测试带历史记录的挑战"""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_path = Path(tmpdir) / "history.json"

            # 创建模拟历史
            history_data = {
                "failures": [
                    {
                        "topic": "python",
                        "description": "Python performance issue",
                    }
                ],
                "decisions": [
                    {
                        "topic": "language choice",
                        "decision": "Use Python",
                        "outcome": "failure",
                    }
                ],
            }

            history_path.write_text(
                pytest.helpers.json_dumps(history_data) if hasattr(pytest, "helpers") else __import__("json").dumps(history_data),
                encoding="utf-8",
            )

            result = challenge_tool(
                "Python is great for everything",
                history_path=history_path,
            )

            assert len(result.historical_failures) >= 1

    def test_confidence_score_calculation(self):
        """测试置信度计算"""
        result = challenge_tool("Test idea")

        # 置信度应该在 0-1 之间
        assert 0 <= result.confidence_score <= 1


class TestEmergeTool:
    """Emerge Tool 测试"""

    def test_emerge_basic(self):
        """测试基本发现功能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wiki_path = Path(tmpdir) / "wiki"
            wiki_path.mkdir()

            # 创建测试笔记
            note1 = wiki_path / "note1.md"
            note1.write_text(
                "[[Python]] is great #programming **test**",
                encoding="utf-8",
            )

            note2 = wiki_path / "note2.md"
            note2.write_text(
                "Learning [[Python]] #programming",
                encoding="utf-8",
            )

            result = emerge_tool(days=30, wiki_path=wiki_path)

            assert result.total_notes_scanned >= 0
            assert result.scan_time >= 0

    def test_emerge_no_notes(self):
        """测试无笔记情况"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wiki_path = Path(tmpdir) / "wiki"
            wiki_path.mkdir()

            result = emerge_tool(days=30, wiki_path=wiki_path)

            assert result.total_notes_scanned == 0
            assert len(result.patterns) == 0

    def test_emerge_min_occurrences(self):
        """测试最小出现次数过滤"""
        result = emerge_tool(days=30, min_occurrences=10)

        # 默认情况应该正常返回
        assert isinstance(result, EmergeResult)


class TestConnectTool:
    """Connect Tool 测试"""

    def test_connect_basic(self):
        """测试基本连接功能"""
        result = connect_tool("Python", "JavaScript")

        assert result.topic_a == "Python"
        assert result.topic_b == "JavaScript"
        assert len(result.links_created) >= 2

    def test_connect_with_content(self):
        """测试带内容的连接"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wiki_path = Path(tmpdir) / "wiki"
            wiki_path.mkdir()

            # 创建主题文件
            python_note = wiki_path / "python.md"
            python_note.write_text(
                "# Python\n[[programming]] [[language]]",
                encoding="utf-8",
            )

            js_note = wiki_path / "javascript.md"
            js_note.write_text(
                "# JavaScript\n[[programming]] [[web]]",
                encoding="utf-8",
            )

            result = connect_tool("python", "javascript", wiki_path=wiki_path)

            # 应该发现 programming 共同概念
            assert len(result.connections) >= 1

    def test_connect_action_ideas(self):
        """测试可行动想法生成"""
        result = connect_tool("A", "B")

        if result.connections:
            assert len(result.action_ideas) > 0


class TestGraduateTool:
    """Graduate Tool 测试"""

    def test_graduate_low_maturity(self):
        """测试低成熟度想法"""
        result = graduate_tool("just an idea")

        assert result.maturity_score < 0.5
        assert result.project_spec is None

    def test_graduate_high_maturity(self):
        """测试高成熟度想法"""
        detailed_idea = """
        Build a new API service

        Goals:
        - Create REST API
        - Support 1000 users
        - Launch by December

        Team: 3 developers
        Budget: $50k
        """

        result = graduate_tool(detailed_idea)

        assert result.maturity_score >= 0.5
        assert result.project_spec is not None
        assert len(result.task_breakdown) > 0

    def test_graduate_project_spec(self):
        """测试项目规格生成"""
        result = graduate_tool(
            "Build a comprehensive documentation system with multiple phases",
        )

        if result.project_spec:
            assert result.project_spec.name
            assert len(result.project_spec.goals) > 0

    def test_graduate_kanban(self):
        """测试看板初始化"""
        result = graduate_tool(
            "Detailed project idea with clear timeline and budget",
        )

        if result.kanban:
            assert "TODO" in result.kanban.columns
            assert "Done" in result.kanban.columns

    def test_auto_create_files(self):
        """测试自动创建文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wiki_path = Path(tmpdir) / "wiki"

            result = graduate_tool(
                "Build a complete system with all features",
                wiki_path=wiki_path,
                auto_create=True,
            )

            if result.maturity_score >= 0.5 and result.created_files:
                # 验证文件存在
                for path in result.created_files:
                    assert Path(path).exists()


class TestContextTool:
    """Context Tool 测试"""

    def test_context_l0(self):
        """测试 L0 级别"""
        result = context_tool("l0")

        assert result.level == ContextLevel.L0
        assert result.token_estimate <= ContextLoader.TOKEN_BUDGETS[ContextLevel.L0]

    def test_context_l1(self):
        """测试 L1 级别"""
        result = context_tool("l1")

        assert result.level == ContextLevel.L1

    def test_context_l2(self):
        """测试 L2 级别"""
        result = context_tool("l2")

        assert result.level == ContextLevel.L2

    def test_context_l3(self):
        """测试 L3 级别"""
        result = context_tool("l3")

        assert result.level == ContextLevel.L3

    def test_context_default_level(self):
        """测试默认级别"""
        result = context_tool("invalid")

        # 无效级别应该返回 L1
        assert result.level == ContextLevel.L1


class TestContextLoader:
    """Context Loader 测试"""

    def test_loader_basic(self):
        """测试基本加载功能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ContextLoader(
                wiki_path=Path(tmpdir) / "wiki",
                state_path=Path(tmpdir) / "state.json",
            )

            bundle = loader.load(ContextLevel.L1)

            assert bundle.level == ContextLevel.L1

    def test_add_critical_fact(self):
        """测试添加关键事实"""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ContextLoader(state_path=Path(tmpdir) / "state.json")

            fact = loader.add_critical_fact(
                content="Test fact",
                category="identity",
                priority=5,
            )

            assert fact.content == "Test fact"
            assert fact.category == "identity"

    def test_add_decision(self):
        """测试添加决策"""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ContextLoader(state_path=Path(tmpdir) / "state.json")

            dec = loader.add_decision(
                topic="test",
                decision="Test decision",
                rationale="Test rationale",
            )

            assert dec.topic == "test"
            assert dec.decision == "Test decision"

    def test_get_stats(self):
        """测试获取统计"""
        loader = ContextLoader()

        stats = loader.get_stats()

        assert "critical_facts" in stats
        assert "decisions" in stats
        assert "token_budgets" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
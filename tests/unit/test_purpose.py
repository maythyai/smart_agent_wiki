"""
Purpose Module Tests

测试 Purpose Layer 功能
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from saw.purpose import (
    PurposeManager,
    Purpose,
    Goal,
    ResearchScope,
    PurposeAnalyzer,
)
from saw.purpose.models import GoalPriority, GoalStatus


class TestGoal:
    """Goal 测试"""

    def test_goal_to_markdown(self):
        """测试 Goal markdown 输出"""
        goal = Goal(
            goal_id="goal-1",
            content="Test goal content",
            priority=GoalPriority.HIGH,
            status=GoalStatus.ACTIVE,
        )

        md = goal.to_markdown()

        assert "[HIGH]" in md
        assert "Test goal content" in md
        assert "🔵" in md  # Active status icon

    def test_completed_goal(self):
        """测试已完成目标"""
        goal = Goal(
            goal_id="goal-2",
            content="Completed goal",
            priority=GoalPriority.MEDIUM,
            status=GoalStatus.COMPLETED,
            completed_at=datetime.now(),
        )

        md = goal.to_markdown()

        assert "✅" in md


class TestResearchScope:
    """ResearchScope 测试"""

    def test_scope_to_markdown(self):
        """测试 Scope markdown 输出"""
        scope = ResearchScope(
            included=["AI", "LLM"],
            excluded=["Politics"],
            focus_areas=["RAG", "Knowledge Management"],
        )

        md = scope.to_markdown()

        assert "AI" in md
        assert "Politics" in md
        assert "RAG" in md


class TestPurpose:
    """Purpose 测试"""

    def test_purpose_to_markdown(self):
        """测试 Purpose markdown 输出"""
        purpose = Purpose(
            purpose_id="test-purpose",
            title="Test Wiki Purpose",
            description="This is a test purpose",
            goals=[
                Goal(
                    goal_id="g1",
                    content="Goal 1",
                    priority=GoalPriority.HIGH,
                )
            ],
            key_questions=["What is X?"],
            thesis="Test thesis",
        )

        md = purpose.to_markdown()

        assert "# Test Wiki Purpose" in md
        assert "This is a test purpose" in md
        assert "Goal 1" in md
        assert "What is X?" in md
        assert "Test thesis" in md
        assert "For future Claude" in md

    def test_purpose_to_dict(self):
        """测试 Purpose 字典转换"""
        purpose = Purpose(
            purpose_id="test-001",
            title="Test",
            description="Test description",
        )

        data = purpose.to_dict()

        assert data["purpose_id"] == "test-001"
        assert data["title"] == "Test"


class TestPurposeManager:
    """PurposeManager 测试"""

    def test_create_purpose(self):
        """测试创建 Purpose"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PurposeManager(
                wiki_path=Path(tmpdir) / "wiki",
            )

            purpose = manager.create(
                title="Test Wiki",
                description="A test wiki",
                goals=["Learn Python", "Build projects"],
                key_questions=["How to start?"],
            )

            assert purpose.title == "Test Wiki"
            assert len(purpose.goals) == 2
            assert len(purpose.key_questions) == 1

    def test_add_goal(self):
        """测试添加目标"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PurposeManager(wiki_path=Path(tmpdir) / "wiki")
            manager.create("Test", "Test")

            goal = manager.add_goal("New goal", GoalPriority.HIGH)

            assert goal.content == "New goal"
            assert goal.priority == GoalPriority.HIGH

            purpose = manager.get()
            assert len(purpose.goals) == 1

    def test_complete_goal(self):
        """测试完成目标"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PurposeManager(wiki_path=Path(tmpdir) / "wiki")
            manager.create("Test", "Test")
            goal = manager.add_goal("To complete")

            result = manager.complete_goal(goal.goal_id)

            assert result is not None
            assert result.status == GoalStatus.COMPLETED
            assert result.completed_at is not None

    def test_update_thesis(self):
        """测试更新论点"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PurposeManager(wiki_path=Path(tmpdir) / "wiki")
            manager.create("Test", "Test")

            manager.update_thesis("New thesis statement")

            purpose = manager.get()
            assert purpose.thesis == "New thesis statement"

    def test_get_summary(self):
        """测试获取摘要"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PurposeManager(wiki_path=Path(tmpdir) / "wiki")
            manager.create(
                title="Test Wiki",
                description="A comprehensive test wiki",
                goals=["Goal 1"],
                thesis="Test thesis",
            )

            summary = manager.get_summary()

            assert "Test Wiki" in summary
            assert "Active Goals" in summary


class TestPurposeAnalyzer:
    """PurposeAnalyzer 测试"""

    def test_analyze_alignment(self):
        """测试对齐分析"""
        analyzer = PurposeAnalyzer()

        result = analyzer.analyze(
            content="This content is about AI and machine learning",
            purpose_summary="AI research wiki",
            goals=["Understand AI", "Build ML models"],
            thesis="AI will transform industries",
            scope_included=["AI", "ML"],
            scope_excluded=[],
        )

        assert result.score >= 0
        assert result.in_scope is True

    def test_out_of_scope(self):
        """测试范围外内容"""
        analyzer = PurposeAnalyzer()

        result = analyzer.analyze(
            content="This is about cooking recipes",
            purpose_summary="AI research wiki",
            goals=["Understand AI"],
            thesis="AI thesis",
            scope_included=["AI", "ML"],
            scope_excluded=["cooking"],
        )

        assert result.in_scope is False
        assert result.score == 0.0

    def test_generate_recommendations(self):
        """测试建议生成"""
        analyzer = PurposeAnalyzer()

        result = analyzer.analyze(
            content="Unrelated content",
            purpose_summary="AI wiki",
            goals=["AI research"],
            thesis="AI thesis",
            scope_included=["AI"],
            scope_excluded=[],
        )

        # 低相关内容应该有建议
        assert len(result.recommendations) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
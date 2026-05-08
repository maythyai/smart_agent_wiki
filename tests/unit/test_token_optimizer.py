"""
Token Optimizer 模块测试
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from saw.token_optimizer import (
    AnatomyIndex,
    FileEntry,
    Cerebrum,
    BugLog,
    BugEntry,
    BugStatus,
    SessionTracker,
    TokenLedger,
)
from saw.token_optimizer.models import LearningType


class TestAnatomyIndex:
    """Anatomy Index 测试"""

    def test_estimate_tokens_code(self):
        """测试代码文件 Token 估算"""
        from saw.token_optimizer.anatomy import estimate_tokens

        # 代码文件
        code = "def hello():\n    return 'world'"
        tokens = estimate_tokens(code, is_code=True)
        assert tokens > 0
        # 大约 35 字符 / 3.5 = 10 tokens
        assert 5 <= tokens <= 20

    def test_estimate_tokens_text(self):
        """测试文本文件 Token 估算"""
        from saw.token_optimizer.anatomy import estimate_tokens

        text = "This is a simple text for testing."
        tokens = estimate_tokens(text, is_code=False)
        assert tokens > 0
        # 大约 35 字符 / 4 = 9 tokens
        assert 5 <= tokens <= 15

    def test_file_entry_to_markdown(self):
        """测试文件条目转 markdown"""
        entry = FileEntry(
            path="src/main.py",
            description="Main entry point",
            estimated_tokens=150,
            is_directory=False,
            language="python",
        )
        line = entry.to_markdown_line()
        assert "`main.py`" in line
        assert "Main entry point" in line
        assert "~150 tok" in line

    def test_anatomy_index_scan_directory(self, tmp_path):
        """测试目录扫描"""
        # 创建测试文件
        (tmp_path / "main.py").write_text("def main(): pass")
        (tmp_path / "README.md").write_text("# Test Project")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "test.pyc").write_text("compiled")

        index = AnatomyIndex(project_root=tmp_path)
        entries = index.scan_directory()

        # 应该包含 .py 和 .md 文件
        assert "main.py" in entries or any("main.py" in p for p in entries)
        assert "README.md" in entries or any("README.md" in p for p in entries)
        # 不应该包含 __pycache__
        assert not any("__pycache__" in p for p in entries)

    def test_anatomy_index_markdown_roundtrip(self, tmp_path):
        """测试 markdown 序列化/反序列化"""
        index = AnatomyIndex(project_root=tmp_path)
        index.entries = {
            "src": FileEntry(path="src", description="", estimated_tokens=0, is_directory=True),
            "src/main.py": FileEntry(
                path="src/main.py",
                description="Main entry point",
                estimated_tokens=150,
                is_directory=False,
            ),
        }

        md = index.to_markdown()
        assert "## src/" in md
        assert "main.py" in md
        assert "~150 tok" in md

        # 反向解析
        parsed = AnatomyIndex.from_markdown(md, tmp_path)
        assert "src/main.py" in parsed.entries

    def test_find_by_pattern(self, tmp_path):
        """测试模式搜索"""
        index = AnatomyIndex(project_root=tmp_path)
        index.entries = {
            "src/main.py": FileEntry(path="src/main.py", description="Main", estimated_tokens=100, is_directory=False),
            "src/utils.py": FileEntry(path="src/utils.py", description="Utils", estimated_tokens=50, is_directory=False),
            "tests/test_main.py": FileEntry(path="tests/test_main.py", description="Tests", estimated_tokens=80, is_directory=False),
        }

        results = index.find_by_pattern("*.py")
        assert len(results) == 3

        # 测试路径匹配
        results = index.find_by_pattern("*test_main*")
        assert len(results) == 1
        assert results[0].path == "tests/test_main.py"


class TestCerebrum:
    """Cerebrum 学习记忆测试"""

    def test_add_preference(self, tmp_path):
        """测试添加偏好"""
        cerebrum = Cerebrum(storage_path=tmp_path / "cerebrum.md")
        entry = cerebrum.add_preference("Use type hints in all functions")

        assert len(cerebrum.preferences) == 1
        assert entry.entry_type == LearningType.USER_PREFERENCE
        assert "type hints" in entry.content

    def test_add_do_not_repeat(self, tmp_path):
        """测试添加 Do-Not-Repeat"""
        cerebrum = Cerebrum(storage_path=tmp_path / "cerebrum.md")
        entry = cerebrum.add_do_not_repeat(
            mistake="Used mutable default argument",
            correction="Use None default and check inside function",
            date="2026-05-05",
        )

        assert len(cerebrum.do_not_repeat) == 1
        assert "2026-05-05" in entry.content
        assert "mutable default" in entry.content.lower()

    def test_check_do_not_repeat(self, tmp_path):
        """测试检查 Do-Not-Repeat"""
        cerebrum = Cerebrum(storage_path=tmp_path / "cerebrum.md")
        cerebrum.add_do_not_repeat("Use var instead of let", "Use const by default")

        # 测试大小写不敏感的搜索
        result = cerebrum.check_do_not_repeat("use var instead of let")
        assert result is not None

        result = cerebrum.check_do_not_repeat("something unrelated")
        assert result is None

    def test_search(self, tmp_path):
        """测试搜索"""
        cerebrum = Cerebrum(storage_path=tmp_path / "cerebrum.md")
        cerebrum.add_preference("Use TypeScript for frontend")
        cerebrum.add_learning("React components should be functional")
        cerebrum.add_do_not_repeat("Use any type", "Use unknown and type guards")

        results = cerebrum.search("typescript")
        assert len(results) >= 1

        results = cerebrum.search("react")
        assert len(results) >= 1

    def test_save_and_load(self, tmp_path):
        """测试保存和加载"""
        storage = tmp_path / "cerebrum.md"
        cerebrum = Cerebrum(storage_path=storage)
        cerebrum.add_preference("Use pytest for testing")
        cerebrum.add_learning("FastAPI works well with Pydantic")
        cerebrum.save()

        # 重新加载
        cerebrum2 = Cerebrum(storage_path=storage)
        assert len(cerebrum2.preferences) >= 1
        assert len(cerebrum2.learnings) >= 1


class TestBugLog:
    """Bug Log 测试"""

    def test_add_bug(self, tmp_path):
        """测试添加 Bug"""
        buglog = BugLog(storage_path=tmp_path / "buglog.json")
        bug = buglog.add_bug(
            error_message="TypeError: 'NoneType' object is not subscriptable",
            file="src/api/users.py",
            root_cause="API returned None instead of expected dict",
            fix="Added null check before accessing dict",
            tags=["null-check", "api"],
        )

        assert bug.id == "bug-001"
        assert bug.occurrences == 1
        assert bug.status == BugStatus.FIXED
        assert len(buglog.bugs) == 1

    def test_similar_bug_detection(self, tmp_path):
        """测试相似 Bug 检测"""
        buglog = BugLog(storage_path=tmp_path / "buglog.json")
        buglog.add_bug(
            error_message="TypeError: 'NoneType' object is not subscriptable",
            file="src/api.py",
            root_cause="None returned",
            fix="Add check",
            tags=["null"],
        )

        # 添加相似 Bug，应该增加 occurrences
        bug2 = buglog.add_bug(
            error_message="TypeError: 'NoneType' object is not subscriptable",
            file="src/api.py",
            root_cause="Same issue",
            fix="Same fix",
        )

        assert len(buglog.bugs) == 1  # 只有一个 Bug 记录
        assert bug2.occurrences == 2

    def test_search_bugs(self, tmp_path):
        """测试 Bug 搜索"""
        buglog = BugLog(storage_path=tmp_path / "buglog.json")
        buglog.add_bug(
            error_message="ImportError: No module named 'requests'",
            file="src/main.py",
            root_cause="Missing dependency",
            fix="pip install requests",
            tags=["import", "dependency"],
        )
        buglog.add_bug(
            error_message="KeyError: 'user_id'",
            file="src/auth.py",
            root_cause="Missing key",
            fix="Use .get() with default",
            tags=["dict", "key"],
        )

        results = buglog.search(query="ImportError")
        assert len(results) == 1

        results = buglog.search(tags=["import"])
        assert len(results) == 1

        results = buglog.search(file="auth")
        assert len(results) == 1

    def test_get_fix_for_error(self, tmp_path):
        """测试获取错误修复方案"""
        buglog = BugLog(storage_path=tmp_path / "buglog.json")
        buglog.add_bug(
            error_message="SyntaxError: invalid syntax at line 10",
            file="src/parser.py",
            root_cause="Missing colon",
            fix="Add : after if statement",
        )

        fix = buglog.get_fix_for_error("SyntaxError: invalid syntax at line 20")
        assert fix is not None
        # 修复内容包含 "add"
        assert "add" in fix.fix.lower()


class TestSessionTracker:
    """Session Tracker 测试"""

    def test_track_first_read(self):
        """测试首次读取追踪"""
        tracker = SessionTracker()
        result = tracker.track_read("src/main.py", 100)

        assert result["first_read"] is True
        assert result["read_count"] == 1
        assert "warning" not in result

    def test_track_repeated_read(self):
        """测试重复读取检测"""
        tracker = SessionTracker()
        tracker.track_read("src/main.py", 100)
        result = tracker.track_read("src/main.py", 100)

        assert result["first_read"] is False
        assert result["read_count"] == 2
        assert "warning" in result

    def test_anatomy_hit_tracking(self):
        """测试 Anatomy 命中追踪"""
        tracker = SessionTracker()
        tracker.record_anatomy_hit(tokens_saved=500)

        stats = tracker.get_stats()
        assert stats.anatomy_hits == 1

    def test_should_skip_read(self):
        """测试跳过读取判断"""
        tracker = SessionTracker()

        # 首次读取不跳过
        assert tracker.should_skip_read("src/main.py") is None

        tracker.track_read("src/main.py", 100)

        # 第一次读取后 read_count=1，仍然返回 None
        result = tracker.should_skip_read("src/main.py")
        assert result is None

        # 第二次读取
        tracker.track_read("src/main.py", 100)

        # read_count=2 时会有警告
        result = tracker.should_skip_read("src/main.py")
        assert result is not None
        assert "already read" in result.lower()

    def test_get_summary(self):
        """测试获取摘要"""
        tracker = SessionTracker(session_id="test-123")
        tracker.track_read("src/main.py", 100)
        tracker.track_read("src/utils.py", 50)
        tracker.track_read("src/main.py", 100)  # 重复
        tracker.record_anatomy_hit()

        summary = tracker.get_summary()
        assert summary["session_id"] == "test-123"
        assert summary["total_reads"] == 3
        assert summary["unique_files"] == 2
        assert summary["repeated_reads"] == 1

    def test_get_top_files(self):
        """测试获取最常读取文件"""
        tracker = SessionTracker()
        tracker.track_read("src/a.py", 100)
        tracker.track_read("src/a.py", 100)
        tracker.track_read("src/a.py", 100)
        tracker.track_read("src/b.py", 50)

        top = tracker.get_top_files()
        assert len(top) == 2
        assert top[0][0] == "src/a.py"
        assert top[0][1] == 3  # 读取次数


class TestTokenLedger:
    """Token Ledger 测试"""

    def test_start_end_session(self, tmp_path):
        """测试会话开始和结束"""
        ledger = TokenLedger(storage_path=tmp_path / "ledger.json")
        session = ledger.start_session()

        assert session.session_id is not None
        assert session.start_time is not None
        assert session.end_time is None

        ended = ledger.end_session()
        assert ended is not None
        assert ended.end_time is not None

    def test_record_read(self, tmp_path):
        """测试记录读取"""
        ledger = TokenLedger(storage_path=tmp_path / "ledger.json")
        ledger.start_session()

        stats = ledger.record_read(100, was_anatomy_hit=True)
        assert stats["lifetime"]["total_reads"] == 1
        assert stats["lifetime"]["anatomy_hits"] == 1

    def test_record_write(self, tmp_path):
        """测试记录写入"""
        ledger = TokenLedger(storage_path=tmp_path / "ledger.json")
        ledger.start_session()

        stats = ledger.record_write(200, file_path="src/main.py")
        assert stats["lifetime"]["total_writes"] == 1
        assert stats["lifetime"]["total_tokens"] == 200

    def test_savings_report(self, tmp_path):
        """测试节省报告"""
        ledger = TokenLedger(storage_path=tmp_path / "ledger.json")
        ledger.start_session()

        # 记录一些操作
        ledger.record_read(100, was_anatomy_hit=True)
        ledger.record_read(200, was_repeated_read=True)

        report = ledger.get_savings_report()
        assert report["estimated_savings_tokens"] > 0
        assert report["savings_percentage"] > 0

    def test_save_and_load(self, tmp_path):
        """测试保存和加载"""
        storage = tmp_path / "ledger.json"
        ledger = TokenLedger(storage_path=storage)
        ledger.start_session()
        ledger.record_read(100)
        ledger.record_write(50)
        ledger.end_session()

        # 重新加载
        ledger2 = TokenLedger(storage_path=storage)
        assert ledger2.lifetime.total_sessions == 1
        assert ledger2.lifetime.total_reads == 1
        assert ledger2.lifetime.total_writes == 1

    def test_reset(self, tmp_path):
        """测试重置"""
        ledger = TokenLedger(storage_path=tmp_path / "ledger.json")
        ledger.start_session()
        ledger.record_read(100)
        ledger.reset()

        assert ledger.lifetime.total_tokens == 0
        assert ledger.lifetime.total_sessions == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

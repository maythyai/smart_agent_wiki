"""
Bug Log - Bug 记忆库

基于 OpenWolf 的 buglog.json 概念实现：
- 记录 Bug 修复历史
- 避免重复调试
- 支持搜索和匹配
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import BugEntry, BugStatus


class BugLog:
    """
    Bug 记忆库管理器

    管理 Bug 修复记录，支持：
    - 记录 Bug 详情和修复方案
    - 按 ID、标签、错误消息搜索
    - 检测重复 Bug
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        初始化 BugLog

        Args:
            storage_path: 存储文件路径，默认为 .wolf/buglog.json
        """
        self.storage_path = storage_path
        self.bugs: dict[str, BugEntry] = {}
        self._next_id = 1

        if storage_path and storage_path.exists():
            self.load()

    def add_bug(
        self,
        error_message: str,
        file: str,
        root_cause: str,
        fix: str,
        tags: Optional[list[str]] = None,
        related_bugs: Optional[list[str]] = None,
    ) -> BugEntry:
        """
        添加 Bug 记录

        Args:
            error_message: 错误消息
            file: 涉及的文件
            root_cause: 根本原因
            fix: 修复方案
            tags: 标签列表
            related_bugs: 相关 Bug ID 列表

        Returns:
            创建的 Bug 条目
        """
        # 检查是否已存在相同 Bug
        existing = self._find_similar(error_message, file)
        if existing:
            existing.occurrences += 1
            existing.last_seen = datetime.now()
            self.save()
            return existing

        bug_id = f"bug-{self._next_id:03d}"
        self._next_id += 1

        entry = BugEntry(
            id=bug_id,
            error_message=error_message,
            file=file,
            root_cause=root_cause,
            fix=fix,
            tags=tags or [],
            related_bugs=related_bugs or [],
            occurrences=1,
            status=BugStatus.FIXED,
            timestamp=datetime.now(),
            last_seen=datetime.now(),
        )

        self.bugs[bug_id] = entry
        self.save()
        return entry

    def _find_similar(self, error_message: str, file: str) -> Optional[BugEntry]:
        """
        查找相似的 Bug

        Args:
            error_message: 错误消息
            file: 文件路径

        Returns:
            如果找到相似 Bug 则返回，否则返回 None
        """
        for bug in self.bugs.values():
            if bug.file == file and self._is_similar_error(bug.error_message, error_message):
                return bug
        return None

    def _is_similar_error(self, error1: str, error2: str) -> bool:
        """
        判断两个错误消息是否相似

        Args:
            error1: 第一个错误消息
            error2: 第二个错误消息

        Returns:
            是否相似
        """
        # 标准化错误消息
        def normalize(msg: str) -> str:
            # 移除变量部分（如路径、数字等）
            msg = re.sub(r"'.*?'", "''", msg)
            msg = re.sub(r'".*?"', '""', msg)
            msg = re.sub(r"\d+", "N", msg)
            msg = re.sub(r"/[\w/.-]+", "/path", msg)
            return msg.lower().strip()

        return normalize(error1) == normalize(error2)

    def search(
        self,
        query: Optional[str] = None,
        tags: Optional[list[str]] = None,
        file: Optional[str] = None,
        status: Optional[BugStatus] = None,
    ) -> list[BugEntry]:
        """
        搜索 Bug 记录

        Args:
            query: 搜索关键词（匹配错误消息）
            tags: 标签过滤
            file: 文件过滤
            status: 状态过滤

        Returns:
            匹配的 Bug 条目列表
        """
        results = []

        for bug in self.bugs.values():
            # 标签过滤
            if tags and not any(t in bug.tags for t in tags):
                continue

            # 文件过滤
            if file and file not in bug.file:
                continue

            # 状态过滤
            if status and bug.status != status:
                continue

            # 关键词搜索
            if query:
                query_lower = query.lower()
                if (query_lower not in bug.error_message.lower() and
                    query_lower not in bug.root_cause.lower() and
                    query_lower not in bug.fix.lower() and
                    query_lower not in bug.id.lower()):
                    continue

            results.append(bug)

        # 按时间倒序排列
        results.sort(key=lambda b: b.timestamp, reverse=True)
        return results

    def get_by_id(self, bug_id: str) -> Optional[BugEntry]:
        """
        根据 ID 获取 Bug

        Args:
            bug_id: Bug ID

        Returns:
            Bug 条目，不存在则返回 None
        """
        return self.bugs.get(bug_id)

    def get_fix_for_error(self, error_message: str) -> Optional[BugEntry]:
        """
        获取错误的修复方案

        Args:
            error_message: 错误消息

        Returns:
            如果找到匹配的 Bug 则返回，否则返回 None
        """
        for bug in self.bugs.values():
            if self._is_similar_error(bug.error_message, error_message):
                return bug
        return None

    def update_status(self, bug_id: str, status: BugStatus) -> None:
        """
        更新 Bug 状态

        Args:
            bug_id: Bug ID
            status: 新状态
        """
        if bug_id in self.bugs:
            self.bugs[bug_id].status = status
            self.save()

    def relate_bugs(self, bug_id: str, related_ids: list[str]) -> None:
        """
        关联相关 Bug

        Args:
            bug_id: Bug ID
            related_ids: 相关 Bug ID 列表
        """
        if bug_id in self.bugs:
            bug = self.bugs[bug_id]
            for rid in related_ids:
                if rid not in bug.related_bugs:
                    bug.related_bugs.append(rid)
            self.save()

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "total": len(self.bugs),
            "fixed": sum(1 for b in self.bugs.values() if b.status == BugStatus.FIXED),
            "open": sum(1 for b in self.bugs.values() if b.status == BugStatus.OPEN),
            "wont_fix": sum(1 for b in self.bugs.values() if b.status == BugStatus.WONT_FIX),
            "total_occurrences": sum(b.occurrences for b in self.bugs.values()),
        }

    def to_json(self) -> dict:
        """
        转换为 JSON 格式

        Returns:
            JSON 兼容的字典
        """
        return {
            "version": 1,
            "bugs": [bug.to_dict() for bug in self.bugs.values()],
        }

    def save(self) -> None:
        """保存到文件"""
        if self.storage_path:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            content = json.dumps(self.to_json(), indent=2, ensure_ascii=False)
            self.storage_path.write_text(content, encoding="utf-8")

    def load(self) -> None:
        """从文件加载"""
        if not self.storage_path or not self.storage_path.exists():
            return

        try:
            content = json.loads(self.storage_path.read_text(encoding="utf-8"))
            self.bugs = {
                bug["id"]: BugEntry.from_dict(bug)
                for bug in content.get("bugs", [])
            }

            # 更新下一个 ID
            if self.bugs:
                max_id = max(int(bid.split("-")[1]) for bid in self.bugs.keys())
                self._next_id = max_id + 1
        except (json.JSONDecodeError, KeyError, ValueError):
            # 文件损坏时重新初始化
            self.bugs = {}
            self._next_id = 1

    def clear(self) -> None:
        """清除所有记录"""
        self.bugs.clear()
        self._next_id = 1
        self.save()

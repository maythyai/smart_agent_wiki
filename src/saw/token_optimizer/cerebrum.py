"""
Cerebrum - 学习记忆管理

基于 OpenWolf 的 cerebrum.md 概念实现：
- 记录用户偏好
- 积累关键学习
- 维护 Do-Not-Repeat 列表
- 保存决策日志
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import LearningEntry, LearningType


class Cerebrum:
    """
    学习记忆管理器

    管理跨会话的学习记录，包括：
    - User Preferences: 用户偏好
    - Key Learnings: 关键学习
    - Do-Not-Repeat: 避免重复的错误
    - Decision Log: 决策日志
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        初始化 Cerebrum

        Args:
            storage_path: 存储文件路径，默认为 .wolf/cerebrum.md
        """
        self.storage_path = storage_path
        self.preferences: list[LearningEntry] = []
        self.learnings: list[LearningEntry] = []
        self.do_not_repeat: list[LearningEntry] = []
        self.decisions: list[LearningEntry] = []

        if storage_path and storage_path.exists():
            self.load()

    def add_preference(self, content: str, context: Optional[str] = None) -> LearningEntry:
        """
        添加用户偏好

        Args:
            content: 偏好内容
            context: 可选的上下文

        Returns:
            创建的学习条目
        """
        entry = LearningEntry(
            entry_type=LearningType.USER_PREFERENCE,
            content=content,
            context=context,
        )
        self.preferences.append(entry)
        self.save()
        return entry

    def add_learning(self, content: str, context: Optional[str] = None) -> LearningEntry:
        """
        添加关键学习

        Args:
            content: 学习内容
            context: 可选的上下文

        Returns:
            创建的学习条目
        """
        entry = LearningEntry(
            entry_type=LearningType.KEY_LEARNING,
            content=content,
            context=context,
        )
        self.learnings.append(entry)
        self.save()
        return entry

    def add_do_not_repeat(
        self,
        mistake: str,
        correction: str,
        date: Optional[str] = None
    ) -> LearningEntry:
        """
        添加 Do-Not-Repeat 条目

        Args:
            mistake: 错误描述
            correction: 正确做法
            date: 日期字符串，默认为今天

        Returns:
            创建的学习条目
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        content = f"{mistake} — {correction}"

        entry = LearningEntry(
            entry_type=LearningType.DO_NOT_REPEAT,
            content=f"{date}: {content}",
        )
        self.do_not_repeat.append(entry)
        self.save()
        return entry

    def add_decision(
        self,
        decision: str,
        rationale: str,
        alternatives: Optional[str] = None
    ) -> LearningEntry:
        """
        添加决策日志

        Args:
            decision: 决策内容
            rationale: 决策理由
            alternatives: 被拒绝的替代方案

        Returns:
            创建的学习条目
        """
        content = f"{decision}"
        if rationale:
            content += f" — {rationale}"
        if alternatives:
            content += f" (rejected: {alternatives})"

        entry = LearningEntry(
            entry_type=LearningType.DECISION_LOG,
            content=content,
        )
        self.decisions.append(entry)
        self.save()
        return entry

    def search(self, query: str) -> list[tuple[LearningType, LearningEntry]]:
        """
        搜索学习记录

        Args:
            query: 搜索关键词

        Returns:
            匹配的 (类型, 条目) 列表
        """
        query = query.lower()
        results = []

        for entry in self.preferences:
            if query in entry.content.lower():
                results.append((LearningType.USER_PREFERENCE, entry))

        for entry in self.learnings:
            if query in entry.content.lower():
                results.append((LearningType.KEY_LEARNING, entry))

        for entry in self.do_not_repeat:
            if query in entry.content.lower():
                results.append((LearningType.DO_NOT_REPEAT, entry))

        for entry in self.decisions:
            if query in entry.content.lower():
                results.append((LearningType.DECISION_LOG, entry))

        return results

    def check_do_not_repeat(self, action: str) -> Optional[LearningEntry]:
        """
        检查行动是否在 Do-Not-Repeat 列表中

        Args:
            action: 要检查的行动描述

        Returns:
            如果匹配则返回条目，否则返回 None
        """
        action_lower = action.lower()
        for entry in self.do_not_repeat:
            if action_lower in entry.content.lower():
                return entry
        return None

    def to_markdown(self) -> str:
        """
        转换为 markdown 格式

        格式与 OpenWolf 的 cerebrum.md 兼容
        """
        lines = [
            "# Cerebrum",
            "",
            "> Smart Agent Wiki's learning memory. Updated automatically.",
            f"> Last updated: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "## User Preferences",
            "",
        ]

        if self.preferences:
            for entry in self.preferences:
                lines.append(entry.to_markdown())
        else:
            lines.append("<!-- How the user likes things done. -->")

        lines.extend([
            "",
            "## Key Learnings",
            "",
        ])

        if self.learnings:
            for entry in self.learnings:
                lines.append(entry.to_markdown())
        else:
            lines.append("<!-- Project-specific conventions discovered during development. -->")

        lines.extend([
            "",
            "## Do-Not-Repeat",
            "",
        ])

        if self.do_not_repeat:
            for entry in self.do_not_repeat:
                lines.append(entry.to_markdown())
        else:
            lines.extend([
                "<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->",
                "<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->",
            ])

        lines.extend([
            "",
            "## Decision Log",
            "",
        ])

        if self.decisions:
            for entry in self.decisions:
                lines.append(entry.to_markdown())
        else:
            lines.append("<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->")

        return "\n".join(lines)

    def save(self) -> None:
        """保存到文件"""
        if self.storage_path:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.write_text(self.to_markdown(), encoding="utf-8")

    def load(self) -> None:
        """从文件加载"""
        if not self.storage_path or not self.storage_path.exists():
            return

        content = self.storage_path.read_text(encoding="utf-8")
        self._parse_markdown(content)

    def _parse_markdown(self, content: str) -> None:
        """
        解析 markdown 内容

        Args:
            content: markdown 文本
        """
        current_section = None

        for line in content.split("\n"):
            # 检测章节标题
            if line.startswith("## User Preferences"):
                current_section = "preferences"
            elif line.startswith("## Key Learnings"):
                current_section = "learnings"
            elif line.startswith("## Do-Not-Repeat"):
                current_section = "do_not_repeat"
            elif line.startswith("## Decision Log"):
                current_section = "decisions"
            elif line.startswith("## "):
                current_section = None
            elif line.startswith("- ") and current_section:
                # 解析列表项
                item_content = line[2:].strip()

                entry = LearningEntry(
                    entry_type=self._get_entry_type(current_section),
                    content=item_content,
                )

                if current_section == "preferences":
                    self.preferences.append(entry)
                elif current_section == "learnings":
                    self.learnings.append(entry)
                elif current_section == "do_not_repeat":
                    self.do_not_repeat.append(entry)
                elif current_section == "decisions":
                    self.decisions.append(entry)

    def _get_entry_type(self, section: str) -> LearningType:
        """根据章节名获取条目类型"""
        mapping = {
            "preferences": LearningType.USER_PREFERENCE,
            "learnings": LearningType.KEY_LEARNING,
            "do_not_repeat": LearningType.DO_NOT_REPEAT,
            "decisions": LearningType.DECISION_LOG,
        }
        return mapping.get(section, LearningType.KEY_LEARNING)

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "preferences": len(self.preferences),
            "learnings": len(self.learnings),
            "do_not_repeat": len(self.do_not_repeat),
            "decisions": len(self.decisions),
            "total": (
                len(self.preferences) +
                len(self.learnings) +
                len(self.do_not_repeat) +
                len(self.decisions)
            ),
        }

    def clear(self, section: Optional[str] = None) -> None:
        """
        清除学习记录

        Args:
            section: 要清除的章节，None 表示清除全部
        """
        if section == "preferences":
            self.preferences.clear()
        elif section == "learnings":
            self.learnings.clear()
        elif section == "do_not_repeat":
            self.do_not_repeat.clear()
        elif section == "decisions":
            self.decisions.clear()
        else:
            self.preferences.clear()
            self.learnings.clear()
            self.do_not_repeat.clear()
            self.decisions.clear()

        self.save()

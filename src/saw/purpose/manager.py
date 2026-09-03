"""
Purpose Manager - Purpose 管理器

管理 Wiki 的意图和目标定义
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Purpose, Goal, GoalPriority, GoalStatus, ResearchScope


class PurposeManager:
    """
    Purpose 管理器

    管理 purpose.md 的创建、更新和查询：
    1. 定义 Wiki 存在的原因
    2. 跟踪目标状态
    3. 管理研究范围
    4. 记录演进论点
    """

    def __init__(
        self,
        wiki_path: Optional[Path] = None,
        purpose_path: Optional[Path] = None,
    ):
        """
        初始化管理器

        Args:
            wiki_path: Wiki 目录路径
            purpose_path: purpose.md 文件路径
        """
        self.wiki_path = wiki_path or Path(".saw/wiki")
        self.purpose_path = purpose_path or self.wiki_path / "purpose.md"
        self._purpose: Optional[Purpose] = None

        self.load()

    def load(self) -> Optional[Purpose]:
        """加载 purpose.md"""
        if not self.purpose_path.exists():
            return None

        try:
            content = self.purpose_path.read_text(encoding="utf-8")
            self._purpose = self._parse_markdown(content)
            return self._purpose
        except Exception:
            return None

    def _parse_markdown(self, content: str) -> Purpose:
        """解析 markdown 内容为 Purpose"""
        # 简单解析实现
        lines = content.split("\n")

        title = ""
        description = ""
        goals: list[Goal] = []
        key_questions: list[str] = []
        thesis = ""
        scope = ResearchScope()

        current_section = ""
        in_goals = False
        in_questions = False

        for line in lines:
            # 标题
            if line.startswith("# ") and not title:
                title = line[2:].strip()
                continue

            # 章节
            if line.startswith("## "):
                current_section = line[3:].lower()
                in_goals = "goal" in current_section
                in_questions = "question" in current_section
                continue

            # 描述
            if current_section == "description" and line.strip():
                description += line.strip() + " "

            # 论点
            if current_section == "evolving thesis" and line.startswith("> "):
                thesis = line[2:].strip()

            # 目标
            if in_goals and line.startswith("- "):
                goal_text = line[2:]
                # 解析状态图标
                status = GoalStatus.ACTIVE
                if "✅" in goal_text:
                    status = GoalStatus.COMPLETED
                    goal_text = goal_text.replace("✅", "")
                elif "⏸️" in goal_text:
                    status = GoalStatus.PAUSED
                    goal_text = goal_text.replace("⏸️", "")
                elif "❌" in goal_text:
                    status = GoalStatus.ABANDONED
                    goal_text = goal_text.replace("❌", "")

                # 解析优先级
                priority = GoalPriority.MEDIUM
                if "[CRITICAL]" in goal_text:
                    priority = GoalPriority.CRITICAL
                    goal_text = goal_text.replace("[CRITICAL]", "")
                elif "[HIGH]" in goal_text:
                    priority = GoalPriority.HIGH
                    goal_text = goal_text.replace("[HIGH]", "")
                elif "[LOW]" in goal_text:
                    priority = GoalPriority.LOW
                    goal_text = goal_text.replace("[LOW]", "")

                goal = Goal(
                    goal_id=f"goal-{len(goals) + 1}",
                    content=goal_text.strip(),
                    priority=priority,
                    status=status,
                )
                goals.append(goal)

            # 关键问题
            if in_questions and line.startswith("- [ ]"):
                question = line[5:].strip()
                key_questions.append(question)

        return Purpose(
            purpose_id="main-purpose",
            title=title or "Untitled Purpose",
            description=description.strip() or "No description defined.",
            goals=goals,
            key_questions=key_questions,
            thesis=thesis,
            scope=scope,
        )

    def save(self) -> None:
        """保存 purpose.md"""
        if not self._purpose:
            return

        self.purpose_path.parent.mkdir(parents=True, exist_ok=True)
        self.purpose_path.write_text(
            self._purpose.to_markdown(),
            encoding="utf-8"
        )

    def create(
        self,
        title: str,
        description: str,
        goals: Optional[list[str]] = None,
        key_questions: Optional[list[str]] = None,
        thesis: str = "",
    ) -> Purpose:
        """
        创建新的 Purpose

        Args:
            title: 标题
            description: 描述
            goals: 目标列表
            key_questions: 关键问题列表
            thesis: 初始论点

        Returns:
            创建的 Purpose
        """
        goal_objs = []
        if goals:
            for i, g in enumerate(goals):
                goal_objs.append(Goal(
                    goal_id=f"goal-{i + 1}",
                    content=g,
                    priority=GoalPriority.MEDIUM,
                ))

        self._purpose = Purpose(
            purpose_id="main-purpose",
            title=title,
            description=description,
            goals=goal_objs,
            key_questions=key_questions or [],
            thesis=thesis,
        )

        self.save()
        return self._purpose

    def get(self) -> Optional[Purpose]:
        """获取当前 Purpose"""
        return self._purpose

    def add_goal(
        self,
        content: str,
        priority: GoalPriority = GoalPriority.MEDIUM,
    ) -> Goal:
        """
        添加目标

        Args:
            content: 目标内容
            priority: 优先级

        Returns:
            添加的目标
        """
        if not self._purpose:
            self._purpose = Purpose(
                purpose_id="main-purpose",
                title="Default Purpose",
                description="Auto-created purpose",
            )

        goal = Goal(
            goal_id=f"goal-{len(self._purpose.goals) + 1}",
            content=content,
            priority=priority,
        )

        self._purpose.goals.append(goal)
        self._purpose.updated_at = datetime.now()
        self.save()

        return goal

    def complete_goal(self, goal_id: str) -> Optional[Goal]:
        """完成目标"""
        if not self._purpose:
            return None

        for goal in self._purpose.goals:
            if goal.goal_id == goal_id:
                goal.status = GoalStatus.COMPLETED
                goal.completed_at = datetime.now()
                self._purpose.updated_at = datetime.now()
                self.save()
                return goal

        return None

    def update_thesis(self, thesis: str) -> None:
        """更新演进论点"""
        if not self._purpose:
            return

        self._purpose.thesis = thesis
        self._purpose.updated_at = datetime.now()
        self.save()

    def add_key_question(self, question: str) -> None:
        """添加关键问题"""
        if not self._purpose:
            return

        self._purpose.key_questions.append(question)
        self._purpose.updated_at = datetime.now()
        self.save()

    def answer_question(self, question: str) -> bool:
        """标记问题已回答（移除）"""
        if not self._purpose:
            return False

        if question in self._purpose.key_questions:
            self._purpose.key_questions.remove(question)
            self._purpose.updated_at = datetime.now()
            self.save()
            return True

        return False

    def set_scope(
        self,
        included: Optional[list[str]] = None,
        excluded: Optional[list[str]] = None,
        focus_areas: Optional[list[str]] = None,
    ) -> None:
        """设置研究范围"""
        if not self._purpose:
            return

        self._purpose.scope = ResearchScope(
            included=included or [],
            excluded=excluded or [],
            focus_areas=focus_areas or [],
        )
        self._purpose.updated_at = datetime.now()
        self.save()

    def get_summary(self) -> str:
        """获取 Purpose 摘要（供 LLM 使用）"""
        if not self._purpose:
            return "No purpose defined."

        lines = [
            f"**Title**: {self._purpose.title}",
            f"**Description**: {self._purpose.description[:200]}",
        ]

        if self._purpose.thesis:
            lines.append(f"**Thesis**: {self._purpose.thesis}")

        active_goals = [
            g for g in self._purpose.goals
            if g.status == GoalStatus.ACTIVE
        ]
        if active_goals:
            lines.append(f"**Active Goals**: {len(active_goals)}")

        if self._purpose.key_questions:
            lines.append(f"**Open Questions**: {len(self._purpose.key_questions)}")

        return "\n".join(lines)
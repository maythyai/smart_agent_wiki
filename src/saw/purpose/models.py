"""
Purpose Models - 意图数据模型

定义 Wiki 的方向性目标
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class GoalPriority(Enum):
    """目标优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GoalStatus(Enum):
    """目标状态"""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"


@dataclass
class Goal:
    """
    目标定义

    Wiki 试图达成的具体目标
    """
    goal_id: str
    content: str
    priority: GoalPriority = GoalPriority.MEDIUM
    status: GoalStatus = GoalStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metrics: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """转换为 markdown 格式"""
        status_icon = {
            GoalStatus.ACTIVE: "🔵",
            GoalStatus.COMPLETED: "✅",
            GoalStatus.PAUSED: "⏸️",
            GoalStatus.ABANDONED: "❌",
        }.get(self.status, "⚪")

        return f"- {status_icon} [{self.priority.value.upper()}] {self.content}"


@dataclass
class ResearchScope:
    """
    研究范围

    定义 Wiki 关注的领域边界
    """
    included: list[str] = field(default_factory=list)
    excluded: list[str] = field(default_factory=list)
    focus_areas: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """转换为 markdown 格式"""
        lines = []

        if self.included:
            lines.append("**Included:**")
            for item in self.included:
                lines.append(f"- {item}")
            lines.append("")

        if self.excluded:
            lines.append("**Excluded:**")
            for item in self.excluded:
                lines.append(f"- {item}")
            lines.append("")

        if self.focus_areas:
            lines.append("**Focus Areas:**")
            for item in self.focus_areas:
                lines.append(f"- {item}")

        return "\n".join(lines)


@dataclass
class Purpose:
    """
    Purpose 定义

    Wiki 的"灵魂" - 为什么存在，追求什么
    """
    purpose_id: str
    title: str
    description: str
    goals: list[Goal] = field(default_factory=list)
    key_questions: list[str] = field(default_factory=list)
    scope: Optional[ResearchScope] = None
    thesis: str = ""  # 演进中的论点
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_markdown(self) -> str:
        """转换为 markdown 格式"""
        lines = [
            f"# {self.title}",
            "",
            f"> Purpose ID: `{self.purpose_id}`",
            f"> Created: {self.created_at.strftime('%Y-%m-%d')}",
            f"> Updated: {self.updated_at.strftime('%Y-%m-%d')}",
            "",
            "---",
            "",
            "## Description",
            "",
            self.description,
            "",
        ]

        if self.thesis:
            lines.extend([
                "## Evolving Thesis",
                "",
                f"> {self.thesis}",
                "",
            ])

        if self.goals:
            lines.extend([
                "## Goals",
                "",
            ])
            for goal in self.goals:
                lines.append(goal.to_markdown())
            lines.append("")

        if self.key_questions:
            lines.extend([
                "## Key Questions",
                "",
            ])
            for q in self.key_questions:
                lines.append(f"- [ ] {q}")
            lines.append("")

        if self.scope:
            lines.extend([
                "## Scope",
                "",
            ])
            lines.append(self.scope.to_markdown())
            lines.append("")

        lines.extend([
            "---",
            "",
            "## For future Claude",
            "",
            f"This purpose.md defines why this wiki exists. "
            f"Read this during every ingest and query for context. "
            f"Current thesis: {self.thesis or 'Not yet defined'}.",
            "",
            f"*Last updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')}*",
        ])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "purpose_id": self.purpose_id,
            "title": self.title,
            "description": self.description,
            "goals": [
                {
                    "goal_id": g.goal_id,
                    "content": g.content,
                    "priority": g.priority.value,
                    "status": g.status.value,
                    "created_at": g.created_at.isoformat(),
                    "completed_at": g.completed_at.isoformat() if g.completed_at else None,
                    "metrics": g.metrics,
                }
                for g in self.goals
            ],
            "key_questions": self.key_questions,
            "scope": {
                "included": self.scope.included,
                "excluded": self.scope.excluded,
                "focus_areas": self.scope.focus_areas,
            } if self.scope else None,
            "thesis": self.thesis,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
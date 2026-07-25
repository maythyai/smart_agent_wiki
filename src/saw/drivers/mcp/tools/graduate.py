"""
saw_graduate - Graduate Tool

将想法升级为项目
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ProjectSpec:
    """项目规格"""
    name: str
    description: str
    goals: list[str]
    success_criteria: list[str]


@dataclass
class TaskBreakdown:
    """任务分解"""
    phase: str
    tasks: list[str]


@dataclass
class KanbanBoard:
    """看板"""
    columns: dict[str, list[str]]


@dataclass
class GraduateResult:
    """升级结果"""
    idea: str
    maturity_score: float  # 0-1
    project_spec: Optional[ProjectSpec] = None
    task_breakdown: list[TaskBreakdown] = field(default_factory=list)
    kanban: Optional[KanbanBoard] = None
    created_files: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


def graduate_tool(
    idea: str,
    wiki_path: Optional[Path] = None,
    auto_create: bool = False,
) -> GraduateResult:
    """
    将想法升级为项目

    分析想法成熟度，生成项目规格，
    创建任务分解，初始化看板。

    Args:
        idea: 想法内容
        wiki_path: Wiki 目录路径
        auto_create: 是否自动创建文件

    Returns:
        升级结果
    """
    wiki_path = wiki_path or Path(".saw/wiki")

    # 1. 分析成熟度
    maturity_score = _analyze_maturity(idea)

    result = GraduateResult(
        idea=idea,
        maturity_score=maturity_score,
    )

    # 2. 如果成熟度足够，生成项目规格
    if maturity_score >= 0.5:
        result.project_spec = _generate_project_spec(idea)

        # 3. 生成任务分解
        result.task_breakdown = _generate_task_breakdown(result.project_spec)

        # 4. 初始化看板
        result.kanban = _initialize_kanban(result.task_breakdown)

        # 5. 创建文件（如果启用）
        if auto_create:
            result.created_files = _create_project_files(
                result.project_spec,
                result.task_breakdown,
                wiki_path,
            )

    return result


def _analyze_maturity(idea: str) -> float:
    """
    分析想法成熟度

    基于多个指标：
    - 明确性（长度、结构）
    - 具体性（数字、日期）
    - 可行性（资源提及）
    """
    score = 0.0

    # 长度检查
    word_count = len(idea.split())
    if word_count >= 10:
        score += 0.2
    if word_count >= 30:
        score += 0.1

    # 结构检查（是否有列表或分段）
    if "\n" in idea or "-" in idea:
        score += 0.2

    # 具体性检查（是否有数字）
    if any(char.isdigit() for char in idea):
        score += 0.2

    # 可行性检查（关键词）
    feasibility_keywords = [
        "budget", "timeline", "team", "resources",
        "goal", "objective", "deadline", "milestone",
        "预算", "时间", "团队", "资源", "目标", "截止",
    ]
    for keyword in feasibility_keywords:
        if keyword.lower() in idea.lower():
            score += 0.1
            break

    return min(1.0, score)


def _generate_project_spec(idea: str) -> ProjectSpec:
    """生成项目规格"""
    # 从想法提取名称
    name = idea.split("\n")[0][:50]
    if not name:
        name = "New Project"

    # 简单生成描述
    description = f"Project generated from idea: {idea[:200]}"

    # 默认目标
    goals = [
        "Complete initial implementation",
        "Validate core assumptions",
        "Document findings",
    ]

    # 成功标准
    success_criteria = [
        "All core features implemented",
        "Tests passing",
        "Documentation complete",
    ]

    return ProjectSpec(
        name=name,
        description=description,
        goals=goals,
        success_criteria=success_criteria,
    )


def _generate_task_breakdown(spec: ProjectSpec) -> list[TaskBreakdown]:
    """生成任务分解"""
    return [
        TaskBreakdown(
            phase="Phase 1: Setup",
            tasks=[
                "Create project structure",
                "Set up development environment",
                "Initialize documentation",
            ],
        ),
        TaskBreakdown(
            phase="Phase 2: Implementation",
            tasks=[
                "Implement core functionality",
                "Write unit tests",
                "Create integration tests",
            ],
        ),
        TaskBreakdown(
            phase="Phase 3: Delivery",
            tasks=[
                "Complete documentation",
                "Perform code review",
                "Release and deploy",
            ],
        ),
    ]


def _initialize_kanban(breakdown: list[TaskBreakdown]) -> KanbanBoard:
    """初始化看板"""
    todo_tasks = []
    for tb in breakdown:
        todo_tasks.extend(tb.tasks)

    return KanbanBoard(
        columns={
            "TODO": todo_tasks,
            "In Progress": [],
            "Review": [],
            "Done": [],
        }
    )


def _create_project_files(
    spec: ProjectSpec,
    breakdown: list[TaskBreakdown],
    wiki_path: Path,
) -> list[str]:
    """创建项目文件"""
    created = []

    # 创建项目页面
    project_path = wiki_path / "projects" / f"{spec.name.replace(' ', '-')}.md"
    project_path.parent.mkdir(parents=True, exist_ok=True)

    content = format_project_page(spec, breakdown)
    project_path.write_text(content, encoding="utf-8")
    created.append(str(project_path))

    return created


def format_project_page(spec: ProjectSpec, breakdown: list[TaskBreakdown]) -> str:
    """格式化项目页面"""
    lines = [
        f"# {spec.name}",
        "",
        "> [!ai-first] This page is optimized for LLM retrieval",
        f"> Generated: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## For future Claude",
        "",
        f"This project was graduated from an idea. Goals: {', '.join(spec.goals[:3])}.",
        "",
        "---",
        "",
        "## Description",
        "",
        spec.description,
        "",
        "## Goals",
        "",
    ]

    for goal in spec.goals:
        lines.append(f"- [ ] {goal}")

    lines.extend([
        "",
        "## Success Criteria",
        "",
    ])

    for criterion in spec.success_criteria:
        lines.append(f"- [ ] {criterion}")

    lines.extend([
        "",
        "## Task Breakdown",
        "",
    ])

    for tb in breakdown:
        lines.append(f"### {tb.phase}")
        lines.append("")
        for task in tb.tasks:
            lines.append(f"- [ ] {task}")
        lines.append("")

    lines.extend([
        "---",
        "",
        f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
    ])

    return "\n".join(lines)


def format_graduate_result(result: GraduateResult) -> str:
    """格式化升级结果"""
    lines = [
        f"# Graduate: {result.idea[:50]}...",
        "",
        f"**Maturity Score**: {result.maturity_score:.2f}",
        "",
    ]

    if result.maturity_score < 0.5:
        lines.extend([
            "## Assessment",
            "",
            "This idea needs more development before becoming a project.",
            "",
            "### Recommendations",
            "",
            "- Add more specific details",
            "- Define clear goals",
            "- Identify required resources",
            "- Set a timeline",
        ])
    else:
        if result.project_spec:
            lines.extend([
                "## Project Specification",
                "",
                f"**Name**: {result.project_spec.name}",
                "",
                f"**Description**: {result.project_spec.description[:200]}",
                "",
                "### Goals",
                "",
            ])

            for goal in result.project_spec.goals:
                lines.append(f"- {goal}")

            lines.append("")

        if result.task_breakdown:
            lines.extend([
                "## Task Breakdown",
                "",
            ])

            for tb in result.task_breakdown:
                lines.append(f"### {tb.phase}")
                for task in tb.tasks:
                    lines.append(f"- [ ] {task}")
                lines.append("")

        if result.kanban:
            lines.extend([
                "## Kanban Board",
                "",
            ])

            for column, tasks in result.kanban.columns.items():
                lines.append(f"### {column}")
                for task in tasks[:5]:  # 限制显示
                    lines.append(f"- {task}")
                lines.append("")

        if result.created_files:
            lines.extend([
                "## Created Files",
                "",
            ])

            for path in result.created_files:
                lines.append(f"- [[{path}]]")

            lines.append("")

    lines.extend([
        "---",
        f"*Generated: {result.created_at.strftime('%Y-%m-%d %H:%M')}*",
    ])

    return "\n".join(lines)
"""
saw_connect - Connect Tool

桥接不相关领域
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import re


@dataclass
class Connection:
    """连接"""
    concept: str
    source_a: str
    source_b: str
    insight: str


@dataclass
class ConnectResult:
    """连接结果"""
    topic_a: str
    topic_b: str
    connections: list[Connection] = field(default_factory=list)
    cross_insights: list[str] = field(default_factory=list)
    action_ideas: list[str] = field(default_factory=list)
    links_created: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


def connect_tool(
    topic_a: str,
    topic_b: str,
    wiki_path: Optional[Path] = None,
) -> ConnectResult:
    """
    桥接两个不相关领域

    找到两个主题的关联概念，生成交叉洞察，
    建议可行动的想法，创建双向链接。

    Args:
        topic_a: 第一个主题
        topic_b: 第二个主题
        wiki_path: Wiki 目录路径

    Returns:
        连接结果
    """
    wiki_path = wiki_path or Path(".saw/wiki")

    connections = []
    cross_insights = []
    action_ideas = []
    links_created = []

    # 1. 获取两个主题的内容
    content_a = _get_topic_content(topic_a, wiki_path)
    content_b = _get_topic_content(topic_b, wiki_path)

    # 2. 提取关键词
    keywords_a = _extract_keywords(content_a)
    keywords_b = _extract_keywords(content_b)

    # 3. 找共同概念
    common_keywords = keywords_a & keywords_b

    for keyword in common_keywords:
        connection = Connection(
            concept=keyword,
            source_a=f"[[{topic_a}]]",
            source_b=f"[[{topic_b}]]",
            insight=f"'{keyword}' appears in both topics",
        )
        connections.append(connection)

    # 4. 生成交叉洞察
    for keyword in list(common_keywords)[:3]:
        cross_insights.append(
            f"The concept of '{keyword}' bridges {topic_a} and {topic_b}, "
            f"suggesting a potential synergy."
        )

    # 5. 生成可行动想法
    if connections:
        action_ideas.extend([
            f"Explore how '{topic_a}' principles apply to '{topic_b}'",
            f"Document the connection at '{topic_a} ↔ {topic_b}'",
            "Create a synthesis page combining both perspectives",
        ])

    # 6. 创建双向链接
    links_created.append(f"[[{topic_a}]] → [[{topic_b}]]")
    links_created.append(f"[[{topic_b}]] → [[{topic_a}]]")

    return ConnectResult(
        topic_a=topic_a,
        topic_b=topic_b,
        connections=connections,
        cross_insights=cross_insights,
        action_ideas=action_ideas,
        links_created=links_created,
    )


def _get_topic_content(topic: str, wiki_path: Path) -> str:
    """获取主题内容"""
    # 尝试多种可能的文件名
    possible_names = [
        f"{topic}.md",
        f"{topic.replace(' ', '-')}.md",
        f"{topic.lower()}.md",
        f"{topic.replace(' ', '_').lower()}.md",
    ]

    for name in possible_names:
        path = wiki_path / name
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except Exception:
                continue

    return ""


def _extract_keywords(content: str) -> set[str]:
    """提取关键词"""
    # 简单实现：提取双括号链接和标签
    keywords = set()

    # 双括号链接
    wiki_links = re.findall(r"\[\[([^\]]+)\]\]", content)
    keywords.update(wiki_links)

    # 标签
    tags = re.findall(r"#(\w+)", content)
    keywords.update(tags)

    # 清理
    keywords = {k.lower().strip() for k in keywords if len(k) > 2}

    return keywords


def format_connect_result(result: ConnectResult) -> str:
    """格式化连接结果"""
    lines = [
        f"# Connect: {result.topic_a} ↔ {result.topic_b}",
        "",
        "## Connections Found",
        "",
    ]

    if result.connections:
        for conn in result.connections:
            lines.append(f"### {conn.concept}")
            lines.append("")
            lines.append(f"- {conn.source_a}")
            lines.append(f"- {conn.source_b}")
            lines.append(f"- *Insight*: {conn.insight}")
            lines.append("")
    else:
        lines.append("No direct connections found.")
        lines.append("")

    lines.extend([
        "## Cross Insights",
        "",
    ])

    if result.cross_insights:
        for insight in result.cross_insights:
            lines.append(f"- {insight}")
        lines.append("")
    else:
        lines.append("No cross insights generated.")
        lines.append("")

    lines.extend([
        "## Action Ideas",
        "",
    ])

    if result.action_ideas:
        for idea in result.action_ideas:
            lines.append(f"- [ ] {idea}")
        lines.append("")
    else:
        lines.append("No action ideas generated.")
        lines.append("")

    lines.extend([
        "## Links Created",
        "",
    ])

    for link in result.links_created:
        lines.append(f"- {link}")

    lines.extend([
        "",
        "---",
        f"*Generated: {result.created_at.strftime('%Y-%m-%d %H:%M')}*",
    ])

    return "\n".join(lines)
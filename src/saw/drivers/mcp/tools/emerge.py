"""
saw_emerge - Emerge Tool

发现未命名的模式
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import re


@dataclass
class UnnamedPattern:
    """未命名模式"""
    pattern_id: str
    occurrences: list[str]  # 出现位置
    suggested_name: str
    suggested_definition: str
    confidence: float


@dataclass
class EmergeResult:
    """发现结果"""
    patterns: list[UnnamedPattern] = field(default_factory=list)
    total_notes_scanned: int = 0
    scan_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


def emerge_tool(
    days: int = 30,
    min_occurrences: int = 3,
    wiki_path: Optional[Path] = None,
) -> EmergeResult:
    """
    发现未命名模式

    扫描近 N 天笔记，识别重复概念，
    建议命名和定义，生成模式页面草稿。

    Args:
        days: 扫描天数范围
        min_occurrences: 最小出现次数
        wiki_path: Wiki 目录路径

    Returns:
        发现结果
    """
    wiki_path = wiki_path or Path(".saw/wiki")

    start_time = datetime.now()
    cutoff_date = datetime.now() - timedelta(days=days)

    patterns: dict[str, list[str]] = {}
    total_notes = 0

    # 1. 扫描近 N 天笔记
    for md_file in wiki_path.glob("**/*.md"):
        # 检查文件修改时间
        try:
            mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
            if mtime < cutoff_date:
                continue
        except Exception:
            continue

        total_notes += 1

        try:
            content = md_file.read_text(encoding="utf-8")

            # 提取关键概念
            concepts = _extract_concepts(content)

            for concept in concepts:
                if concept not in patterns:
                    patterns[concept] = []

                patterns[concept].append(md_file.name)

        except Exception:
            continue

    # 2. 识别重复概念
    unnamed_patterns = []

    for concept, occurrences in patterns.items():
        if len(occurrences) >= min_occurrences:
            pattern = UnnamedPattern(
                pattern_id=f"emerge-{len(unnamed_patterns) + 1}",
                occurrences=occurrences,
                suggested_name=_suggest_name(concept),
                suggested_definition=_suggest_definition(concept, occurrences),
                confidence=min(1.0, len(occurrences) / 10.0),
            )

            unnamed_patterns.append(pattern)

    scan_time = (datetime.now() - start_time).total_seconds()

    return EmergeResult(
        patterns=unnamed_patterns,
        total_notes_scanned=total_notes,
        scan_time=scan_time,
    )


def _extract_concepts(content: str) -> list[str]:
    """提取概念"""
    # 基于常见模式提取
    concepts = []

    # 1. 提取双括号链接 [[...]]
    wiki_links = re.findall(r"\[\[([^\]]+)\]\]", content)
    concepts.extend(wiki_links)

    # 2. 提取标签 #...
    tags = re.findall(r"#(\w+)", content)
    concepts.extend(tags)

    # 3. 提取强调内容 **...**
    bolds = re.findall(r"\*\*([^*]+)\*\*", content)
    concepts.extend([b.strip() for b in bolds if len(b.strip()) > 3])

    # 4. 提取关键短语
    # 简单：提取 capitalized 单词组合
    caps = re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", content)
    concepts.extend(caps)

    return concepts


def _suggest_name(concept: str) -> str:
    """建议命名"""
    # 清理概念
    name = concept.strip()

    # 如果是标签，去掉 #
    if name.startswith("#"):
        name = name[1:]

    # 如果有空格，转为标题格式
    if " " in name:
        name = name.title()

    return f"{name} Pattern"


def _suggest_definition(concept: str, occurrences: list[str]) -> str:
    """建议定义"""
    return (
        f"A recurring pattern observed across {len(occurrences)} notes. "
        f"Key concept: '{concept}'. "
        f"Sources: {', '.join(occurrences[:3])}."
    )


def format_emerge_result(result: EmergeResult) -> str:
    """格式化发现结果"""
    lines = [
        "# Emerge: Unnamed Patterns",
        "",
        f"**Notes Scanned**: {result.total_notes_scanned}",
        f"**Patterns Found**: {len(result.patterns)}",
        f"**Scan Time**: {result.scan_time:.2f}s",
        "",
    ]

    if result.patterns:
        lines.append("---")
        lines.append("")

        for pattern in result.patterns:
            lines.append(f"## {pattern.suggested_name}")
            lines.append("")
            lines.append(f"**Confidence**: {pattern.confidence:.2f}")
            lines.append("")
            lines.append("### Definition")
            lines.append("")
            lines.append(pattern.suggested_definition)
            lines.append("")
            lines.append("### Occurrences")
            lines.append("")

            for occ in pattern.occurrences[:5]:
                lines.append(f"- [[{occ}]]")

            lines.append("")
            lines.append("---")
            lines.append("")

        lines.append("### Next Step")
        lines.append("")
        lines.append("1. Review suggested names")
        lines.append("2. Edit definitions")
        lines.append("3. Create pattern pages")
    else:
        lines.append("No unnamed patterns found.")

    return "\n".join(lines)
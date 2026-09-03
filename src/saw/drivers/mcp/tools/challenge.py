"""
saw_challenge - Challenge Tool

用用户自己的历史反驳当前想法
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import json


@dataclass
class ChallengeResult:
    """反驳结果"""
    idea: str
    challenges: list[str]
    historical_failures: list[str]
    alternative_perspectives: list[str]
    confidence_score: float
    created_at: datetime


def challenge_tool(
    idea: str,
    wiki_path: Optional[Path] = None,
    history_path: Optional[Path] = None,
) -> ChallengeResult:
    """
    挑战一个想法

    搜索历史决策和失败，找到相关相反观点，
    生成结构化反驳，要求用户确认或调整。

    Args:
        idea: 要挑战的想法
        wiki_path: Wiki 目录路径
        history_path: 历史记录路径

    Returns:
        反驳结果
    """
    wiki_path = wiki_path or Path(".saw/wiki")
    history_path = history_path or Path(".saw/history.json")

    challenges = []
    historical_failures = []
    alternative_perspectives = []

    # 1. 搜索历史失败
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text(encoding="utf-8"))

            for entry in history.get("failures", []):
                # 找到相关失败
                if _is_related(idea, entry.get("topic", "")):
                    historical_failures.append(
                        f"- {entry.get('description', 'Unknown failure')}"
                    )

            # 找到相关决策
            for entry in history.get("decisions", []):
                if entry.get("outcome") == "failure":
                    if _is_related(idea, entry.get("topic", "")):
                        historical_failures.append(
                            f"- Decision: {entry.get('decision', 'Unknown')} → {entry.get('outcome', 'failure')}"
                        )

        except (json.JSONDecodeError, KeyError):
            pass

    # 2. 搜索 Wiki 中相反观点
    for md_file in wiki_path.glob("**/*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")

            # 寻找反驳标记
            if "counter:" in content.lower() or "challenge:" in content.lower():
                for line in content.split("\n"):
                    if "counter:" in line.lower() or "challenge:" in line.lower():
                        challenge_text = line.split(":")[-1].strip()
                        if challenge_text and _is_related(idea, challenge_text):
                            challenges.append(f"- {challenge_text}")

        except Exception:
            continue

    # 3. 生成替代视角
    # 基于常见反驳模式
    alternative_patterns = [
        "What if the opposite were true?",
        "What evidence would contradict this?",
        "What are the edge cases?",
        "What assumptions does this rely on?",
        "What would a skeptic say?",
    ]

    for pattern in alternative_patterns:
        alternative_perspectives.append(f"- {pattern}")

    # 4. 计算置信度分数
    # 基于历史失败数量和反驳强度
    confidence_score = 1.0 - (
        len(historical_failures) * 0.2 +
        len(challenges) * 0.1
    )
    confidence_score = max(0.1, min(1.0, confidence_score))

    return ChallengeResult(
        idea=idea,
        challenges=challenges[:5],
        historical_failures=historical_failures[:5],
        alternative_perspectives=alternative_perspectives,
        confidence_score=confidence_score,
        created_at=datetime.now(),
    )


def _is_related(text_a: str, text_b: str) -> bool:
    """检查两个文本是否相关"""
    # 简单关键词匹配
    keywords_a = set(text_a.lower().split())
    keywords_b = set(text_b.lower().split())

    # 移除常见词
    common_words = {"the", "a", "is", "are", "to", "for", "of", "in", "on"}
    keywords_a -= common_words
    keywords_b -= common_words

    # 计算交集
    intersection = keywords_a & keywords_b

    return len(intersection) >= 1


def format_challenge_result(result: ChallengeResult) -> str:
    """格式化反驳结果"""
    lines = [
        f"# Challenge: {result.idea}",
        "",
        f"**Confidence Score**: {result.confidence_score:.2f}",
        "",
        "## Historical Failures",
        "",
    ]

    if result.historical_failures:
        lines.extend(result.historical_failures)
    else:
        lines.append("No relevant historical failures found.")

    lines.extend([
        "",
        "## Counter Arguments",
        "",
    ])

    if result.challenges:
        lines.extend(result.challenges)
    else:
        lines.append("No counter arguments found in wiki.")

    lines.extend([
        "",
        "## Alternative Perspectives",
        "",
    ])

    lines.extend(result.alternative_perspectives)

    lines.extend([
        "",
        "---",
        "",
        f"*Generated: {result.created_at.strftime('%Y-%m-%d %H:%M')}*",
        "",
        "### Next Step",
        "",
        "Review these challenges and:",
        "1. Confirm the idea is still valid",
        "2. Adjust the idea to address challenges",
        "3. Reject the idea based on evidence",
    ])

    return "\n".join(lines)
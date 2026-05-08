"""
Context Loader - 渐进式上下文加载

基于 Token 优化策略的分层上下文加载
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from enum import Enum
import json


class ContextLevel(Enum):
    """上下文级别"""
    L0 = "l0"  # 仅 CRITICAL_FACTS (~120 tokens)
    L1 = "l1"  # + 当前项目状态 (~500 tokens)
    L2 = "l2"  # + 相关历史决策 (~1500 tokens)
    L3 = "l3"  # + 完整上下文 (~5000 tokens)


@dataclass
class CriticalFact:
    """关键事实"""
    fact_id: str
    content: str
    category: str  # identity, preference, constraint, ongoing
    priority: int  # 1-5
    expires_at: Optional[datetime] = None

    def to_markdown(self) -> str:
        """转换为 markdown"""
        return f"- [{self.category.upper()}] {self.content}"


@dataclass
class ProjectState:
    """项目状态"""
    name: str
    phase: str
    active_tasks: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    recent_decisions: list[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class HistoricalDecision:
    """历史决策"""
    decision_id: str
    topic: str
    decision: str
    rationale: str
    outcome: str  # success, partial, failure
    made_at: datetime
    related_topics: list[str] = field(default_factory=list)


@dataclass
class ContextBundle:
    """上下文包"""
    level: ContextLevel
    critical_facts: list[CriticalFact] = field(default_factory=list)
    project_state: Optional[ProjectState] = None
    historical_decisions: list[HistoricalDecision] = field(default_factory=list)
    full_context: str = ""
    token_estimate: int = 0
    loaded_at: datetime = field(default_factory=datetime.now)

    def to_markdown(self) -> str:
        """转换为 markdown"""
        lines = [
            f"# Context Level: {self.level.value}",
            f"> Loaded: {self.loaded_at.strftime('%Y-%m-%d %H:%M')}",
            f"> Token Estimate: {self.token_estimate}",
            "",
        ]

        if self.critical_facts:
            lines.append("## Critical Facts")
            lines.append("")
            for fact in self.critical_facts:
                lines.append(fact.to_markdown())
            lines.append("")

        if self.project_state:
            lines.append("## Project State")
            lines.append("")
            lines.append(f"**Project**: {self.project_state.name}")
            lines.append(f"**Phase**: {self.project_state.phase}")
            if self.project_state.active_tasks:
                lines.append(f"**Active Tasks**: {len(self.project_state.active_tasks)}")
            if self.project_state.blockers:
                lines.append(f"**Blockers**: {', '.join(self.project_state.blockers)}")
            lines.append("")

        if self.historical_decisions:
            lines.append("## Historical Decisions")
            lines.append("")
            for dec in self.historical_decisions[:5]:
                lines.append(f"- [{dec.topic}] {dec.decision} ({dec.outcome})")
            lines.append("")

        if self.full_context:
            lines.append("## Full Context")
            lines.append("")
            lines.append(self.full_context[:2000])  # 截断

        return "\n".join(lines)


class ContextLoader:
    """
    渐进式上下文加载器

    按级别加载上下文，控制 token 消耗：
    - L0: 核心身份和约束 (~120 tokens)
    - L1: 当前项目状态 (~500 tokens)
    - L2: 相关历史决策 (~1500 tokens)
    - L3: 完整上下文 (~5000 tokens)
    """

    # Token 预算
    TOKEN_BUDGETS = {
        ContextLevel.L0: 120,
        ContextLevel.L1: 500,
        ContextLevel.L2: 1500,
        ContextLevel.L3: 5000,
    }

    def __init__(
        self,
        wiki_path: Optional[Path] = None,
        state_path: Optional[Path] = None,
    ):
        """
        初始化上下文加载器

        Args:
            wiki_path: Wiki 目录路径
            state_path: 状态文件路径
        """
        self.wiki_path = wiki_path or Path(".saw/wiki")
        self.state_path = state_path or Path(".saw/state.json")
        self._critical_facts: list[CriticalFact] = []
        self._decisions: list[HistoricalDecision] = []

        self._load_persistent_data()

    def _load_persistent_data(self) -> None:
        """加载持久化数据"""
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))

                for f_data in data.get("critical_facts", []):
                    fact = CriticalFact(
                        fact_id=f_data["fact_id"],
                        content=f_data["content"],
                        category=f_data["category"],
                        priority=f_data.get("priority", 3),
                        expires_at=datetime.fromisoformat(f_data["expires_at"]) if f_data.get("expires_at") else None,
                    )
                    self._critical_facts.append(fact)

                for d_data in data.get("decisions", []):
                    dec = HistoricalDecision(
                        decision_id=d_data["decision_id"],
                        topic=d_data["topic"],
                        decision=d_data["decision"],
                        rationale=d_data.get("rationale", ""),
                        outcome=d_data.get("outcome", "unknown"),
                        made_at=datetime.fromisoformat(d_data["made_at"]),
                        related_topics=d_data.get("related_topics", []),
                    )
                    self._decisions.append(dec)

            except (json.JSONDecodeError, KeyError):
                pass

    def load(self, level: ContextLevel = ContextLevel.L1) -> ContextBundle:
        """
        加载指定级别的上下文

        Args:
            level: 上下文级别

        Returns:
            上下文包
        """
        bundle = ContextBundle(level=level)

        # L0: 基础事实
        bundle.critical_facts = self._get_critical_facts(level)
        bundle.token_estimate = len(bundle.critical_facts) * 15

        # L1: 项目状态
        if level.value >= ContextLevel.L1.value:
            bundle.project_state = self._get_project_state()
            bundle.token_estimate += 200

        # L2: 历史决策
        if level.value >= ContextLevel.L2.value:
            bundle.historical_decisions = self._get_decisions(level)
            bundle.token_estimate += len(bundle.historical_decisions) * 100

        # L3: 完整上下文
        if level.value >= ContextLevel.L3.value:
            bundle.full_context = self._get_full_context()
            bundle.token_estimate += 2000

        # 确保不超过预算
        bundle.token_estimate = min(bundle.token_estimate, self.TOKEN_BUDGETS[level])

        return bundle

    def _get_critical_facts(self, level: ContextLevel) -> list[CriticalFact]:
        """获取关键事实"""
        # 过滤过期事实
        now = datetime.now()
        valid_facts = [
            f for f in self._critical_facts
            if f.expires_at is None or f.expires_at > now
        ]

        # 按优先级排序
        sorted_facts = sorted(valid_facts, key=lambda f: -f.priority)

        # 根据级别限制数量
        limits = {
            ContextLevel.L0: 8,
            ContextLevel.L1: 15,
            ContextLevel.L2: 25,
            ContextLevel.L3: 50,
        }

        return sorted_facts[:limits[level]]

    def _get_project_state(self) -> Optional[ProjectState]:
        """获取项目状态"""
        state_file = self.wiki_path / "PROJECT_STATE.md"

        if state_file.exists():
            content = state_file.read_text(encoding="utf-8")

            # 解析 markdown
            # 简单实现：提取关键信息
            name = "Smart Agent Wiki"
            phase = "development"

            if "phase:" in content.lower():
                for line in content.split("\n"):
                    if "phase:" in line.lower():
                        phase = line.split(":")[-1].strip()

            return ProjectState(
                name=name,
                phase=phase,
                last_updated=datetime.now(),
            )

        return ProjectState(
            name="Smart Agent Wiki",
            phase="active",
        )

    def _get_decisions(self, level: ContextLevel) -> list[HistoricalDecision]:
        """获取历史决策"""
        # 按时间排序
        sorted_decisions = sorted(
            self._decisions,
            key=lambda d: -d.made_at.timestamp()
        )

        limits = {
            ContextLevel.L0: 0,
            ContextLevel.L1: 3,
            ContextLevel.L2: 10,
            ContextLevel.L3: 30,
        }

        return sorted_decisions[:limits[level]]

    def _get_full_context(self) -> str:
        """获取完整上下文"""
        # 从 wiki 目录聚合
        context_parts = []

        for md_file in self.wiki_path.glob("**/*.md"):
            if md_file.name.startswith("_"):
                continue
            try:
                content = md_file.read_text(encoding="utf-8")
                context_parts.append(f"### {md_file.name}\n\n{content[:500]}")
            except Exception:
                continue

        return "\n\n---\n\n".join(context_parts[:10])

    def add_critical_fact(
        self,
        content: str,
        category: str,
        priority: int = 3,
        expires_in: Optional[timedelta] = None,
    ) -> CriticalFact:
        """
        添加关键事实

        Args:
            content: 事实内容
            category: 类别
            priority: 优先级
            expires_in: 过期时间

        Returns:
            添加的事实
        """
        fact = CriticalFact(
            fact_id=f"fact-{len(self._critical_facts) + 1}",
            content=content,
            category=category,
            priority=priority,
            expires_at=datetime.now() + expires_in if expires_in else None,
        )

        self._critical_facts.append(fact)
        self._save()

        return fact

    def add_decision(
        self,
        topic: str,
        decision: str,
        rationale: str,
        outcome: str = "success",
    ) -> HistoricalDecision:
        """
        添加历史决策

        Args:
            topic: 主题
            decision: 决策内容
            rationale: 理由
            outcome: 结果

        Returns:
            添加的决策
        """
        dec = HistoricalDecision(
            decision_id=f"dec-{len(self._decisions) + 1}",
            topic=topic,
            decision=decision,
            rationale=rationale,
            outcome=outcome,
            made_at=datetime.now(),
        )

        self._decisions.append(dec)
        self._save()

        return dec

    def _save(self) -> None:
        """保存持久化数据"""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "critical_facts": [
                {
                    "fact_id": f.fact_id,
                    "content": f.content,
                    "category": f.category,
                    "priority": f.priority,
                    "expires_at": f.expires_at.isoformat() if f.expires_at else None,
                }
                for f in self._critical_facts
            ],
            "decisions": [
                {
                    "decision_id": d.decision_id,
                    "topic": d.topic,
                    "decision": d.decision,
                    "rationale": d.rationale,
                    "outcome": d.outcome,
                    "made_at": d.made_at.isoformat(),
                    "related_topics": d.related_topics,
                }
                for d in self._decisions
            ],
        }

        self.state_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def get_stats(self) -> dict:
        """获取统计"""
        return {
            "critical_facts": len(self._critical_facts),
            "decisions": len(self._decisions),
            "token_budgets": {
                level.value: budget for level, budget in self.TOKEN_BUDGETS.items()
            },
        }
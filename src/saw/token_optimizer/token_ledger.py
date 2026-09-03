"""
Token Ledger - Token 消耗账本

基于 OpenWolf 的 token-ledger.json 概念实现：
- 记录每次操作的 Token 消耗
- 统计会话和生命周期数据
- 计算节省量
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid


@dataclass
class SessionRecord:
    """会话记录"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_tokens: int = 0
    total_reads: int = 0
    total_writes: int = 0
    anatomy_hits: int = 0
    anatomy_misses: int = 0
    repeated_reads_blocked: int = 0


@dataclass
class LifetimeStats:
    """生命周期统计"""
    total_tokens: int = 0
    total_reads: int = 0
    total_writes: int = 0
    total_sessions: int = 0
    anatomy_hits: int = 0
    anatomy_misses: int = 0
    repeated_reads_blocked: int = 0
    estimated_savings: int = 0


class TokenLedger:
    """
    Token 消耗账本

    功能：
    - 追踪每次操作的 Token 消耗
    - 统计会话级和生命周期级数据
    - 计算节省量
    """

    # 平均每次重复读取节省的 Token（基于 OpenWolf 数据）
    AVG_TOKENS_PER_REPEATED_READ_SAVED = 500

    # Anatomy 命中时平均节省的 Token
    AVG_TOKENS_PER_ANATOMY_HIT_SAVED = 800

    def __init__(self, storage_path: Optional[Path] = None):
        """
        初始化 Token Ledger

        Args:
            storage_path: 存储文件路径，默认为 .wolf/token-ledger.json
        """
        self.storage_path = storage_path
        self.lifetime = LifetimeStats()
        self.current_session: Optional[SessionRecord] = None
        self._session_history: list[SessionRecord] = []

        if storage_path and storage_path.exists():
            self.load()

    def start_session(self, session_id: Optional[str] = None) -> SessionRecord:
        """
        开始新会话

        Args:
            session_id: 会话 ID，默认自动生成

        Returns:
            新的会话记录
        """
        # 结束之前的会话
        if self.current_session and not self.current_session.end_time:
            self.end_session()

        session = SessionRecord(
            session_id=session_id or str(uuid.uuid4())[:8],
            start_time=datetime.now(),
        )
        self.current_session = session
        self.lifetime.total_sessions += 1

        self.save()
        return session

    def end_session(self) -> Optional[SessionRecord]:
        """
        结束当前会话

        Returns:
            结束的会话记录
        """
        if not self.current_session:
            return None

        self.current_session.end_time = datetime.now()
        self._session_history.append(self.current_session)

        self.save()
        session = self.current_session
        self.current_session = None
        return session

    def record_read(
        self,
        tokens: int,
        file_path: Optional[str] = None,
        was_anatomy_hit: bool = False,
        was_repeated_read: bool = False,
    ) -> dict:
        """
        记录读取操作

        Args:
            tokens: 消耗的 Token 数
            file_path: 文件路径
            was_anatomy_hit: 是否为 Anatomy 命中
            was_repeated_read: 是否为重复读取

        Returns:
            更新后的统计信息
        """
        self.lifetime.total_reads += 1
        self.lifetime.total_tokens += tokens

        if was_anatomy_hit:
            self.lifetime.anatomy_hits += 1
            self.lifetime.estimated_savings += self.AVG_TOKENS_PER_ANATOMY_HIT_SAVED
        else:
            self.lifetime.anatomy_misses += 1

        if was_repeated_read:
            self.lifetime.repeated_reads_blocked += 1
            self.lifetime.estimated_savings += self.AVG_TOKENS_PER_REPEATED_READ_SAVED

        if self.current_session:
            self.current_session.total_reads += 1
            self.current_session.total_tokens += tokens
            if was_anatomy_hit:
                self.current_session.anatomy_hits += 1
            else:
                self.current_session.anatomy_misses += 1
            if was_repeated_read:
                self.current_session.repeated_reads_blocked += 1

        self.save()
        return self.get_stats()

    def record_write(self, tokens: int, file_path: Optional[str] = None) -> dict:
        """
        记录写入操作

        Args:
            tokens: 消耗的 Token 数
            file_path: 文件路径

        Returns:
            更新后的统计信息
        """
        self.lifetime.total_writes += 1
        self.lifetime.total_tokens += tokens

        if self.current_session:
            self.current_session.total_writes += 1
            self.current_session.total_tokens += tokens

        self.save()
        return self.get_stats()

    def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return {
            "lifetime": {
                "total_tokens": self.lifetime.total_tokens,
                "total_reads": self.lifetime.total_reads,
                "total_writes": self.lifetime.total_writes,
                "total_sessions": self.lifetime.total_sessions,
                "anatomy_hits": self.lifetime.anatomy_hits,
                "anatomy_misses": self.lifetime.anatomy_misses,
                "repeated_reads_blocked": self.lifetime.repeated_reads_blocked,
                "estimated_savings": self.lifetime.estimated_savings,
                "anatomy_hit_rate": (
                    round(
                        self.lifetime.anatomy_hits /
                        (self.lifetime.anatomy_hits + self.lifetime.anatomy_misses) * 100, 1
                    )
                    if (self.lifetime.anatomy_hits + self.lifetime.anatomy_misses) > 0 else 0
                ),
            },
            "current_session": (
                {
                    "session_id": self.current_session.session_id,
                    "duration_seconds": (
                        (datetime.now() - self.current_session.start_time).total_seconds()
                        if self.current_session.start_time else 0
                    ),
                    "total_tokens": self.current_session.total_tokens,
                    "total_reads": self.current_session.total_reads,
                    "total_writes": self.current_session.total_writes,
                    "anatomy_hits": self.current_session.anatomy_hits,
                    "anatomy_misses": self.current_session.anatomy_misses,
                    "repeated_reads_blocked": self.current_session.repeated_reads_blocked,
                }
                if self.current_session else None
            ),
        }

    def get_savings_report(self) -> dict:
        """
        获取节省报告

        Returns:
            节省报告字典
        """
        # 估算无优化时的 Token 消耗
        estimated_without_optimization = (
            self.lifetime.total_tokens +
            self.lifetime.estimated_savings
        )

        savings_percentage = (
            round(
                self.lifetime.estimated_savings /
                estimated_without_optimization * 100, 1
            )
            if estimated_without_optimization > 0 else 0
        )

        return {
            "estimated_savings_tokens": self.lifetime.estimated_savings,
            "savings_percentage": savings_percentage,
            "savings_breakdown": {
                "anatomy_hits": {
                    "count": self.lifetime.anatomy_hits,
                    "tokens_saved": self.lifetime.anatomy_hits * self.AVG_TOKENS_PER_ANATOMY_HIT_SAVED,
                },
                "repeated_reads_blocked": {
                    "count": self.lifetime.repeated_reads_blocked,
                    "tokens_saved": self.lifetime.repeated_reads_blocked * self.AVG_TOKENS_PER_REPEATED_READ_SAVED,
                },
            },
            "comparison": {
                "with_optimization": self.lifetime.total_tokens,
                "without_optimization": estimated_without_optimization,
            },
        }

    def get_session_history(self, limit: int = 10) -> list[dict]:
        """
        获取会话历史

        Args:
            limit: 返回数量限制

        Returns:
            会话记录列表
        """
        sessions = self._session_history[-limit:]
        return [
            {
                "session_id": s.session_id,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "duration_seconds": (
                    (s.end_time - s.start_time).total_seconds()
                    if s.end_time else None
                ),
                "total_tokens": s.total_tokens,
                "total_reads": s.total_reads,
                "total_writes": s.total_writes,
            }
            for s in sessions
        ]

    def to_json(self) -> dict:
        """
        转换为 JSON 格式

        Returns:
            JSON 兼容的字典
        """
        return {
            "version": 1,
            "lifetime": {
                "total_tokens": self.lifetime.total_tokens,
                "total_reads": self.lifetime.total_reads,
                "total_writes": self.lifetime.total_writes,
                "total_sessions": self.lifetime.total_sessions,
                "anatomy_hits": self.lifetime.anatomy_hits,
                "anatomy_misses": self.lifetime.anatomy_misses,
                "repeated_reads_blocked": self.lifetime.repeated_reads_blocked,
                "estimated_savings": self.lifetime.estimated_savings,
            },
            "session_history": [
                {
                    "session_id": s.session_id,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat() if s.end_time else None,
                    "total_tokens": s.total_tokens,
                    "total_reads": s.total_reads,
                    "total_writes": s.total_writes,
                    "anatomy_hits": s.anatomy_hits,
                    "anatomy_misses": s.anatomy_misses,
                    "repeated_reads_blocked": s.repeated_reads_blocked,
                }
                for s in self._session_history
            ],
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

            # 加载生命周期统计
            lifetime_data = content.get("lifetime", {})
            self.lifetime = LifetimeStats(
                total_tokens=lifetime_data.get("total_tokens", 0),
                total_reads=lifetime_data.get("total_reads", 0),
                total_writes=lifetime_data.get("total_writes", 0),
                total_sessions=lifetime_data.get("total_sessions", 0),
                anatomy_hits=lifetime_data.get("anatomy_hits", 0),
                anatomy_misses=lifetime_data.get("anatomy_misses", 0),
                repeated_reads_blocked=lifetime_data.get("repeated_reads_blocked", 0),
                estimated_savings=lifetime_data.get("estimated_savings", 0),
            )

            # 加载会话历史
            self._session_history = []
            for s in content.get("session_history", []):
                session = SessionRecord(
                    session_id=s["session_id"],
                    start_time=datetime.fromisoformat(s["start_time"]),
                    end_time=datetime.fromisoformat(s["end_time"]) if s.get("end_time") else None,
                    total_tokens=s.get("total_tokens", 0),
                    total_reads=s.get("total_reads", 0),
                    total_writes=s.get("total_writes", 0),
                    anatomy_hits=s.get("anatomy_hits", 0),
                    anatomy_misses=s.get("anatomy_misses", 0),
                    repeated_reads_blocked=s.get("repeated_reads_blocked", 0),
                )
                self._session_history.append(session)

        except (json.JSONDecodeError, KeyError, ValueError):
            # 文件损坏时重新初始化
            self.lifetime = LifetimeStats()
            self._session_history = []

    def reset(self) -> None:
        """重置所有统计"""
        self.lifetime = LifetimeStats()
        self.current_session = None
        self._session_history = []
        self.save()

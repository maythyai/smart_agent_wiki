"""
Session Tracker - 会话级读取追踪

基于 OpenWolf 的重复读取检测机制实现：
- 追踪当前会话中已读取的文件
- 检测并警告重复读取
- 统计每个文件的读取次数和 Token 消耗
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid


@dataclass
class ReadRecord:
    """读取记录"""
    file_path: str
    tokens: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SessionStats:
    """会话统计"""
    total_reads: int = 0
    total_tokens: int = 0
    unique_files: int = 0
    repeated_reads: int = 0
    anatomy_hits: int = 0
    anatomy_misses: int = 0


class SessionTracker:
    """
    会话级读取追踪器

    功能：
    - 追踪已读取文件
    - 检测重复读取
    - 统计 Token 消耗
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        初始化会话追踪器

        Args:
            session_id: 会话 ID，默认自动生成
        """
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.start_time = datetime.now()
        self._reads: dict[str, list[ReadRecord]] = defaultdict(list)
        self._stats = SessionStats()

    def track_read(self, file_path: str, tokens: int) -> dict:
        """
        追踪文件读取

        Args:
            file_path: 文件路径
            tokens: 估算的 Token 数

        Returns:
            包含追踪信息的字典：
            - first_read: 是否首次读取
            - read_count: 读取次数
            - total_tokens: 该文件累计 Token
            - warning: 重复读取警告（如果有）
        """
        # 标准化路径
        file_path = str(Path(file_path))

        is_first_read = file_path not in self._reads

        record = ReadRecord(file_path=file_path, tokens=tokens)
        self._reads[file_path].append(record)

        # 更新统计
        self._stats.total_reads += 1
        self._stats.total_tokens += tokens

        if is_first_read:
            self._stats.unique_files += 1
        else:
            self._stats.repeated_reads += 1

        read_count = len(self._reads[file_path])
        total_tokens = sum(r.tokens for r in self._reads[file_path])

        result = {
            "first_read": is_first_read,
            "read_count": read_count,
            "total_tokens": total_tokens,
        }

        # 生成警告
        if read_count > 1:
            result["warning"] = (
                f"[TokenOptimizer] File '{file_path}' read {read_count} times "
                f"this session. Consider using cached content."
            )

        return result

    def was_read(self, file_path: str) -> bool:
        """
        检查文件是否已读取

        Args:
            file_path: 文件路径

        Returns:
            是否已读取
        """
        return str(Path(file_path)) in self._reads

    def get_read_count(self, file_path: str) -> int:
        """
        获取文件读取次数

        Args:
            file_path: 文件路径

        Returns:
            读取次数
        """
        return len(self._reads.get(str(Path(file_path)), []))

    def get_file_tokens(self, file_path: str) -> int:
        """
        获取文件累计 Token

        Args:
            file_path: 文件路径

        Returns:
            累计 Token 数
        """
        records = self._reads.get(str(Path(file_path)), [])
        return sum(r.tokens for r in records)

    def record_anatomy_hit(self, tokens_saved: int = 0) -> None:
        """
        记录 Anatomy 命中（文件摘要替代了完整读取）

        Args:
            tokens_saved: 节省的 Token 数
        """
        self._stats.anatomy_hits += 1
        self._stats.total_tokens -= tokens_saved

    def record_anatomy_miss(self) -> None:
        """记录 Anatomy 未命中"""
        self._stats.anatomy_misses += 1

    def get_stats(self) -> SessionStats:
        """获取会话统计"""
        return self._stats

    def get_summary(self) -> dict:
        """
        获取会话摘要

        Returns:
            包含会话信息的字典
        """
        duration = (datetime.now() - self.start_time).total_seconds()

        return {
            "session_id": self.session_id,
            "duration_seconds": round(duration, 1),
            "total_reads": self._stats.total_reads,
            "total_tokens": self._stats.total_tokens,
            "unique_files": self._stats.unique_files,
            "repeated_reads": self._stats.repeated_reads,
            "anatomy_hits": self._stats.anatomy_hits,
            "anatomy_misses": self._stats.anatomy_misses,
            "repeat_rate": (
                round(self._stats.repeated_reads / self._stats.total_reads * 100, 1)
                if self._stats.total_reads > 0 else 0
            ),
            "anatomy_hit_rate": (
                round(
                    self._stats.anatomy_hits /
                    (self._stats.anatomy_hits + self._stats.anatomy_misses) * 100, 1
                )
                if (self._stats.anatomy_hits + self._stats.anatomy_misses) > 0 else 0
            ),
        }

    def get_top_files(self, limit: int = 10) -> list[tuple[str, int, int]]:
        """
        获取读取最多的文件

        Args:
            limit: 返回数量限制

        Returns:
            (文件路径, 读取次数, Token 数) 列表
        """
        file_stats = [
            (path, len(records), sum(r.tokens for r in records))
            for path, records in self._reads.items()
        ]
        # 按读取次数降序
        file_stats.sort(key=lambda x: x[1], reverse=True)
        return file_stats[:limit]

    def clear(self) -> None:
        """清除追踪记录"""
        self._reads.clear()
        self._stats = SessionStats()
        self.start_time = datetime.now()

    def should_skip_read(self, file_path: str) -> Optional[str]:
        """
        判断是否应该跳过读取

        Args:
            file_path: 文件路径

        Returns:
            如果应该跳过，返回原因；否则返回 None
        """
        file_path = str(Path(file_path))

        if file_path not in self._reads:
            return None

        read_count = len(self._reads[file_path])

        if read_count >= 3:
            return f"File read {read_count} times. Consider refactoring to reduce dependency on this file."

        if read_count >= 2:
            return "File already read this session. Use cached content if available."

        return None

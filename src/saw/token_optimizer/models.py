"""
Token 优化模块的数据模型定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class LearningType(Enum):
    """学习记录类型"""
    USER_PREFERENCE = "user_preference"
    KEY_LEARNING = "key_learning"
    DO_NOT_REPEAT = "do_not_repeat"
    DECISION_LOG = "decision_log"


class BugStatus(Enum):
    """Bug 状态"""
    OPEN = "open"
    FIXED = "fixed"
    WONT_FIX = "wont_fix"


@dataclass
class FileEntry:
    """文件索引条目"""
    path: str
    description: str
    estimated_tokens: int
    last_modified: Optional[datetime] = None
    checksum: Optional[str] = None
    is_directory: bool = False
    language: Optional[str] = None

    def to_markdown_line(self) -> str:
        """转换为 markdown 行格式"""
        if self.is_directory:
            return f"\n## {self.path}/\n"
        return f"- `{Path(self.path).name}` - {self.description} (~{self.estimated_tokens} tok)"


@dataclass
class LearningEntry:
    """学习记录条目"""
    entry_type: LearningType
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Optional[str] = None

    def to_markdown(self) -> str:
        """转换为 markdown 格式"""
        date_str = self.timestamp.strftime("%Y-%m-%d")
        if self.entry_type == LearningType.DO_NOT_REPEAT:
            return f"- {date_str}: {self.content}"
        elif self.entry_type == LearningType.DECISION_LOG:
            return f"- **{date_str}**: {self.content}"
        return f"- {self.content}"


@dataclass
class BugEntry:
    """Bug 记录条目"""
    id: str
    error_message: str
    file: str
    root_cause: str
    fix: str
    tags: list[str] = field(default_factory=list)
    related_bugs: list[str] = field(default_factory=list)
    occurrences: int = 1
    status: BugStatus = BugStatus.OPEN
    timestamp: datetime = field(default_factory=datetime.now)
    last_seen: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "error_message": self.error_message,
            "file": self.file,
            "root_cause": self.root_cause,
            "fix": self.fix,
            "tags": self.tags,
            "related_bugs": self.related_bugs,
            "occurrences": self.occurrences,
            "status": self.status.value,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BugEntry":
        """从字典创建"""
        return cls(
            id=data["id"],
            error_message=data["error_message"],
            file=data["file"],
            root_cause=data["root_cause"],
            fix=data["fix"],
            tags=data.get("tags", []),
            related_bugs=data.get("related_bugs", []),
            occurrences=data.get("occurrences", 1),
            status=BugStatus(data.get("status", "open")),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            last_seen=datetime.fromisoformat(data["last_seen"]) if data.get("last_seen") else None,
        )


@dataclass
class SessionRead:
    """会话读取记录"""
    file_path: str
    tokens: int
    timestamp: datetime = field(default_factory=datetime.now)
    read_count: int = 1


@dataclass
class TokenLedgerEntry:
    """Token 账本条目"""
    timestamp: datetime
    action: str
    file_path: Optional[str]
    tokens_used: int
    session_id: str
    was_anatomy_hit: bool = False
    was_repeated_read: bool = False

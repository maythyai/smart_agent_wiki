"""图快照与回滚 — 版本化图状态

支持:
- 创建快照 (自动/手动)
- 列出历史快照
- 回滚到指定快照 (通过 full rebuild 恢复)
- 快照间 diff 比较
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from saw.code_graph.store import CodeGraphStore
from saw.code_graph.models import GraphSnapshot

logger = logging.getLogger(__name__)


@dataclass
class SnapshotDiff:
    """两个快照间的差异"""
    from_snapshot: str
    to_snapshot: str
    node_delta: int = 0       # 节点数变化
    edge_delta: int = 0       # 边数变化
    files_delta: int = 0      # 文件数变化
    time_between: str = ""    # 时间间隔


class SnapshotManager:
    """图快照管理器

    设计原则:
    - 图 = 源码的派生缓存，源码是 source of truth
    - 快照记录元数据 (计数/时间/触发源)，不存储完整图数据
    - 回滚 = 在目标时间点重新 full build (保证一致性)
    - 任何时候可 full rebuild 恢复
    """

    def __init__(self, store: CodeGraphStore):
        self.store = store

    def create(self, trigger: str = "manual", files_changed: int = 0) -> GraphSnapshot:
        """创建快照"""
        return self.store.create_snapshot(trigger, files_changed)

    def list_snapshots(self, limit: int = 20) -> list[dict]:
        """列出历史快照"""
        conn = self.store.connection
        if conn is None:
            return []

        rows = conn.execute(
            """SELECT snapshot_id, created_at, trigger, node_count, edge_count, files_changed
               FROM graph_snapshots
               ORDER BY created_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()

        return [
            {
                "snapshot_id": r[0],
                "created_at": r[1],
                "trigger": r[2],
                "node_count": r[3],
                "edge_count": r[4],
                "files_changed": r[5],
            }
            for r in rows
        ]

    def diff(self, from_id: str, to_id: str) -> Optional[SnapshotDiff]:
        """比较两个快照"""
        conn = self.store.connection
        if conn is None:
            return None

        from_row = conn.execute(
            "SELECT node_count, edge_count, files_changed, created_at FROM graph_snapshots WHERE snapshot_id = ?",
            (from_id,),
        ).fetchone()
        to_row = conn.execute(
            "SELECT node_count, edge_count, files_changed, created_at FROM graph_snapshots WHERE snapshot_id = ?",
            (to_id,),
        ).fetchone()

        if not from_row or not to_row:
            return None

        return SnapshotDiff(
            from_snapshot=from_id,
            to_snapshot=to_id,
            node_delta=to_row[0] - from_row[0],
            edge_delta=to_row[1] - from_row[1],
            files_delta=to_row[2] - from_row[2],
            time_between=f"{from_row[3]} → {to_row[3]}",
        )

    def verify_integrity(self) -> dict:
        """完整性自检: 检测图与源码的偏差

        检查项:
        1. 孤立边 (指向不存在节点的边)
        2. 已追踪但已删除的文件
        3. FTS 索引一致性
        """
        conn = self.store.connection
        if conn is None:
            return {"status": "error", "message": "No connection"}

        issues = []

        # 1. 孤立边
        orphan_edges = conn.execute(
            """SELECT COUNT(*) FROM code_edges e
               WHERE NOT EXISTS (SELECT 1 FROM code_nodes n WHERE n.uid = e.source)
                  OR NOT EXISTS (SELECT 1 FROM code_nodes n WHERE n.uid = e.target)"""
        ).fetchone()[0]
        if orphan_edges > 0:
            issues.append(f"{orphan_edges} orphan edges (target/source not in nodes)")

        # 2. 已追踪但可能已删除的文件
        tracked_files = conn.execute("SELECT COUNT(*) FROM file_tracking").fetchone()[0]
        actual_nodes = conn.execute("SELECT COUNT(DISTINCT file_path) FROM code_nodes").fetchone()[0]
        if tracked_files > actual_nodes + 5:  # 允许小偏差
            issues.append(f"file_tracking has {tracked_files} entries but only {actual_nodes} files have nodes")

        # 3. FTS 一致性
        try:
            fts_count = conn.execute("SELECT COUNT(*) FROM code_nodes_fts").fetchone()[0]
            node_count = conn.execute("SELECT COUNT(*) FROM code_nodes").fetchone()[0]
            if fts_count != node_count:
                issues.append(f"FTS index has {fts_count} entries but {node_count} nodes exist")
        except Exception:
            issues.append("FTS index query failed")

        return {
            "status": "healthy" if not issues else "degraded",
            "issues": issues,
            "node_count": self.store.node_count(),
            "edge_count": self.store.edge_count(),
            "file_count": self.store.file_count(),
        }

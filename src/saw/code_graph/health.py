"""可观测性 — 健康检查、指标收集、告警

提供:
- 结构化健康报告 (JSON)
- 构建/查询指标追踪
- 告警规则 (图过期、解析错误率、orphan 边)
- 变更日志摘要
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from saw.code_graph.store import CodeGraphStore

logger = logging.getLogger(__name__)


@dataclass
class HealthReport:
    """健康报告"""
    status: str = "healthy"  # healthy | degraded | critical
    timestamp: str = ""
    checks: dict = field(default_factory=dict)
    alerts: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


@dataclass
class BuildMetrics:
    """构建指标"""
    trigger: str = ""
    files_parsed: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    nodes_created: int = 0
    edges_created: int = 0
    duration_ms: float = 0.0
    error_rate: float = 0.0
    timestamp: str = ""


@dataclass
class QueryMetrics:
    """查询指标"""
    query_type: str = ""
    target: str = ""
    results_count: int = 0
    duration_ms: float = 0.0
    cache_hit: bool = False
    timestamp: str = ""


class HealthMonitor:
    """健康监控器

    告警规则:
    - 图过期 > N 天 (默认 7)
    - 解析错误率 > 阈值 (默认 10%)
    - orphan 边 > 阈值 (默认 50)
    - 节点数为 0 (空图)
    """

    def __init__(
        self,
        store: CodeGraphStore,
        stale_days: int = 7,
        error_rate_threshold: float = 0.1,
        orphan_threshold: int = 50,
    ):
        self.store = store
        self.stale_days = stale_days
        self.error_rate_threshold = error_rate_threshold
        self.orphan_threshold = orphan_threshold

        # 指标历史 (内存，最近 100 条)
        self._build_history: list[BuildMetrics] = []
        self._query_history: list[QueryMetrics] = []

    def check_health(self) -> HealthReport:
        """执行完整健康检查"""
        report = HealthReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # 基础指标
        node_count = self.store.node_count()
        edge_count = self.store.edge_count()
        file_count = self.store.file_count()
        report.metrics = {
            "nodes": node_count,
            "edges": edge_count,
            "files": file_count,
            "db_size_bytes": self.store.db_path.stat().st_size if self.store.db_path.exists() else 0,
        }

        # Check 1: 空图
        if node_count == 0:
            report.checks["empty_graph"] = "FAIL"
            report.alerts.append("Graph is empty. Run 'saw code-graph build' to populate.")
        else:
            report.checks["empty_graph"] = "PASS"

        # Check 2: Orphan 边
        health = self.store.health_check()
        orphan_count = health.get("orphan_edges", 0)
        if orphan_count > self.orphan_threshold:
            report.checks["orphan_edges"] = "WARN"
            report.alerts.append(
                f"{orphan_count} orphan edges (threshold: {self.orphan_threshold}). "
                f"Run postprocess to resolve bare names."
            )
        else:
            report.checks["orphan_edges"] = "PASS"

        # Check 3: 图过期
        last_build = self._get_last_build_time()
        if last_build:
            days_since = self._days_since(last_build)
            report.metrics["days_since_last_build"] = round(days_since, 1)
            if days_since > self.stale_days:
                report.checks["staleness"] = "WARN"
                report.alerts.append(
                    f"Graph is {days_since:.0f} days old (threshold: {self.stale_days}). "
                    f"Run 'saw code-graph update' to refresh."
                )
            else:
                report.checks["staleness"] = "PASS"
        else:
            report.checks["staleness"] = "UNKNOWN"

        # Check 4: 解析错误率
        if self._build_history:
            recent = self._build_history[-10:]
            avg_error_rate = sum(b.error_rate for b in recent) / len(recent)
            report.metrics["avg_error_rate"] = round(avg_error_rate, 3)
            if avg_error_rate > self.error_rate_threshold:
                report.checks["error_rate"] = "WARN"
                report.alerts.append(
                    f"Average parse error rate {avg_error_rate:.1%} exceeds threshold "
                    f"{self.error_rate_threshold:.0%}."
                )
            else:
                report.checks["error_rate"] = "PASS"
        else:
            report.checks["error_rate"] = "NO_DATA"

        # Check 5: FTS 索引
        try:
            conn = self.store._conn
            if conn:
                fts_count = conn.execute("SELECT COUNT(*) FROM code_nodes_fts").fetchone()[0]
                if fts_count == node_count:
                    report.checks["fts_index"] = "PASS"
                else:
                    report.checks["fts_index"] = "WARN"
                    report.alerts.append(
                        f"FTS index has {fts_count} entries but {node_count} nodes exist."
                    )
        except Exception:
            report.checks["fts_index"] = "ERROR"

        # 综合状态
        fail_count = sum(1 for v in report.checks.values() if v == "FAIL")
        warn_count = sum(1 for v in report.checks.values() if v == "WARN")
        if fail_count > 0:
            report.status = "critical"
        elif warn_count > 0:
            report.status = "degraded"
        else:
            report.status = "healthy"

        return report

    # ─── 指标记录 ─────────────────────────────────────────────────

    def record_build(self, metrics: BuildMetrics) -> None:
        """记录构建指标"""
        metrics.timestamp = datetime.now(timezone.utc).isoformat()
        self._build_history.append(metrics)
        if len(self._build_history) > 100:
            self._build_history = self._build_history[-100:]

    def record_query(self, metrics: QueryMetrics) -> None:
        """记录查询指标"""
        metrics.timestamp = datetime.now(timezone.utc).isoformat()
        self._query_history.append(metrics)
        if len(self._query_history) > 100:
            self._query_history = self._query_history[-100:]

    def get_build_stats(self) -> dict:
        """构建统计摘要"""
        if not self._build_history:
            return {"count": 0}
        recent = self._build_history[-20:]
        return {
            "count": len(self._build_history),
            "avg_duration_ms": round(sum(b.duration_ms for b in recent) / len(recent), 1),
            "avg_files_parsed": round(sum(b.files_parsed for b in recent) / len(recent), 1),
            "avg_error_rate": round(sum(b.error_rate for b in recent) / len(recent), 3),
            "last_build": self._build_history[-1].timestamp,
        }

    def get_query_stats(self) -> dict:
        """查询统计摘要"""
        if not self._query_history:
            return {"count": 0}
        recent = self._query_history[-20:]
        return {
            "count": len(self._query_history),
            "avg_duration_ms": round(sum(q.duration_ms for q in recent) / len(recent), 1),
            "cache_hit_rate": round(
                sum(1 for q in recent if q.cache_hit) / len(recent), 3
            ),
        }

    # ─── 变更日志 ─────────────────────────────────────────────────

    def change_log(self, limit: int = 10) -> list[dict]:
        """最近构建的变更日志"""
        conn = self.store._conn
        if conn is None:
            return []
        rows = conn.execute(
            """SELECT snapshot_id, created_at, trigger, node_count, edge_count, files_changed
               FROM graph_snapshots ORDER BY created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [
            {
                "id": r[0],
                "time": r[1],
                "trigger": r[2],
                "nodes": r[3],
                "edges": r[4],
                "files_changed": r[5],
            }
            for r in rows
        ]

    # ─── 内部工具 ─────────────────────────────────────────────────

    def _get_last_build_time(self) -> Optional[str]:
        """获取最近构建时间"""
        conn = self.store._conn
        if conn is None:
            return None
        row = conn.execute(
            "SELECT MAX(last_parsed_at) FROM file_tracking"
        ).fetchone()
        return row[0] if row and row[0] else None

    @staticmethod
    def _days_since(iso_time: str) -> float:
        """计算距今天数"""
        try:
            dt = datetime.fromisoformat(iso_time)
            now = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return (now - dt).total_seconds() / 86400
        except (ValueError, TypeError):
            return 999.0

"""Govern 集成 — 代码变更触发文档过期检测

将 Code Graph 的变更检测能力接入 SAW Govern 引擎:
- 代码变更 → 影响分析 → 关联文档 → 过期标记
- 定期全局过期扫描
- 与 Wiki 页面 freshness 联动
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from saw.code_graph.engine import CodeGraphEngine
from saw.code_graph.bridge import BridgeLayer, StaleDoc, CrossImpactResult

logger = logging.getLogger(__name__)


@dataclass
class GovernReport:
    """治理报告"""
    timestamp: str = ""
    changed_files: list[str] = field(default_factory=list)
    affected_symbols: int = 0
    stale_docs: list[dict] = field(default_factory=list)
    critical_count: int = 0
    warning_count: int = 0
    recommendations: list[str] = field(default_factory=list)


class CodeGovernIntegration:
    """代码治理集成

    职责:
    1. 监听代码变更 (通过 CodeGraphEngine.detect_changes)
    2. 通过 BridgeLayer 传播影响到文档
    3. 生成治理报告 + 修复建议
    """

    def __init__(self, engine: CodeGraphEngine, bridge: BridgeLayer):
        self.engine = engine
        self.bridge = bridge

    def on_code_change(self, changed_files: Optional[list[str]] = None) -> GovernReport:
        """代码变更事件处理

        Args:
            changed_files: 变更文件列表 (None = 自动检测)

        Returns:
            GovernReport 治理报告
        """
        report = GovernReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # 1. 检测变更
        if changed_files is None:
            changes = self.engine.detect_changes()
            changed_files = changes.get("changed_files", [])

        report.changed_files = changed_files

        if not changed_files:
            report.recommendations.append("No code changes detected.")
            return report

        # 2. 跨图影响分析
        impact = self.bridge.cross_impact(changed_files)
        report.affected_symbols = len(impact.affected_symbols)

        # 3. 过期文档
        for stale in impact.stale_docs:
            report.stale_docs.append({
                "page_id": stale.page_id,
                "page_title": stale.page_title,
                "reason": stale.reason,
                "severity": stale.severity,
                "affected_symbols": stale.affected_symbols,
            })
            if stale.severity == "critical":
                report.critical_count += 1
            elif stale.severity == "warning":
                report.warning_count += 1

        # 4. 生成建议
        report.recommendations = self._generate_recommendations(report, impact)

        return report

    def full_audit(self) -> GovernReport:
        """全局审计: 扫描所有锚定关系的一致性"""
        report = GovernReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # 检查已删除代码的锚定
        stale = self.bridge.check_staleness()
        for doc in stale:
            report.stale_docs.append({
                "page_id": doc.page_id,
                "page_title": doc.page_title,
                "reason": doc.reason,
                "severity": doc.severity,
                "affected_symbols": doc.affected_symbols,
            })
            if doc.severity == "critical":
                report.critical_count += 1
            else:
                report.warning_count += 1

        # 图健康检查
        health = self.engine.health()
        if health.get("orphan_edges", 0) > 0:
            report.recommendations.append(
                f"Graph has {health['orphan_edges']} orphan edges. Run postprocess to resolve."
            )

        if report.critical_count > 0:
            report.recommendations.insert(0,
                f"URGENT: {report.critical_count} docs reference deleted code. Update immediately."
            )

        return report

    def _generate_recommendations(
        self, report: GovernReport, impact: CrossImpactResult
    ) -> list[str]:
        """生成修复建议"""
        recs = []

        if report.critical_count > 0:
            recs.append(
                f"{report.critical_count} critical: docs anchored to heavily-depended code that changed."
            )

        if report.warning_count > 0:
            recs.append(
                f"{report.warning_count} warnings: docs may be outdated after code changes."
            )

        # 具体建议
        for stale in impact.stale_docs:
            if stale.severity == "critical":
                recs.append(
                    f"  → Update '{stale.page_title}': symbols {stale.affected_symbols[:3]} changed significantly."
                )

        if not recs:
            recs.append("All anchored docs are up to date.")

        return recs

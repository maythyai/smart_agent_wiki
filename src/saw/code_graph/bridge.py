"""Bridge Layer — 双图融合: Code Graph ↔ Wiki Knowledge Graph

实现:
- doc→code 锚定: Wiki 页面通过 code_anchors 关联代码符号
- code→doc 反向索引: 代码符号关联相关文档
- 跨图影响传播: 代码变更 → 文档过期检测
- 统一社区视图: 代码模块 ↔ 文档主题对齐
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from saw.code_graph.models import CodeNode, NodeKind
from saw.code_graph.store import CodeGraphStore

logger = logging.getLogger(__name__)


@dataclass
class DocAnchor:
    """文档→代码锚定"""
    page_id: str
    page_title: str
    code_uids: list[str] = field(default_factory=list)
    last_synced: str = ""


@dataclass
class CodeDocLink:
    """代码→文档反向链接"""
    code_uid: str
    code_name: str
    page_ids: list[str] = field(default_factory=list)


@dataclass
class StaleDoc:
    """过期文档"""
    page_id: str
    page_title: str
    reason: str  # "code_changed" | "code_deleted" | "never_synced"
    affected_symbols: list[str] = field(default_factory=list)
    last_code_change: str = ""
    severity: str = "warning"  # "info" | "warning" | "critical"


@dataclass
class CrossImpactResult:
    """跨图影响分析结果"""
    changed_files: list[str] = field(default_factory=list)
    affected_symbols: list[str] = field(default_factory=list)
    stale_docs: list[StaleDoc] = field(default_factory=list)
    total_at_risk: int = 0


class BridgeLayer:
    """双图融合桥接层

    松耦合设计: Code Graph 和 Wiki KG 更新频率不同，
    Bridge 通过锚定表维护映射关系，不合并两图。
    """

    def __init__(
        self,
        code_store: CodeGraphStore,
        wiki_path: Optional[Path] = None,
    ):
        self.code_store = code_store
        self.wiki_path = wiki_path or Path(".saw/wiki")
        self._anchors: dict[str, DocAnchor] = {}  # page_id → DocAnchor
        self._reverse_index: dict[str, list[str]] = {}  # code_uid → [page_ids]

    # ─── 锚定管理 ─────────────────────────────────────────────────

    def anchor_page(self, page_id: str, page_title: str, code_uids: list[str]) -> DocAnchor:
        """将 Wiki 页面锚定到代码符号

        Args:
            page_id: Wiki 页面 ID
            page_title: 页面标题
            code_uids: 关联的代码符号 UID 列表
        """
        # 清除旧锚定的反向索引条目 (防止 re-anchor 时残留)
        old = self._anchors.get(page_id)
        if old:
            for uid in old.code_uids:
                if uid in self._reverse_index:
                    self._reverse_index[uid] = [
                        p for p in self._reverse_index[uid] if p != page_id
                    ]
                    if not self._reverse_index[uid]:
                        del self._reverse_index[uid]

        anchor = DocAnchor(
            page_id=page_id,
            page_title=page_title,
            code_uids=code_uids,
            last_synced=datetime.now(timezone.utc).isoformat(),
        )
        self._anchors[page_id] = anchor

        # 更新反向索引
        for uid in code_uids:
            if uid not in self._reverse_index:
                self._reverse_index[uid] = []
            if page_id not in self._reverse_index[uid]:
                self._reverse_index[uid].append(page_id)

        return anchor

    def unanchor_page(self, page_id: str) -> None:
        """移除页面锚定"""
        anchor = self._anchors.pop(page_id, None)
        if anchor:
            for uid in anchor.code_uids:
                if uid in self._reverse_index:
                    self._reverse_index[uid] = [
                        p for p in self._reverse_index[uid] if p != page_id
                    ]

    # ─── 查询 ─────────────────────────────────────────────────────

    def code_to_docs(self, code_uid: str) -> list[DocAnchor]:
        """给定代码符号，找到所有关联的 Wiki 文档"""
        page_ids = self._reverse_index.get(code_uid, [])
        return [self._anchors[pid] for pid in page_ids if pid in self._anchors]

    def docs_to_code(self, page_id: str) -> list[CodeNode]:
        """给定 Wiki 页面，找到所有锚定的代码符号"""
        anchor = self._anchors.get(page_id)
        if not anchor:
            return []
        nodes = []
        for uid in anchor.code_uids:
            node = self.code_store.get_node(uid)
            if node:
                nodes.append(node)
        return nodes

    def get_all_anchors(self) -> list[DocAnchor]:
        """获取所有锚定关系"""
        return list(self._anchors.values())

    # ─── 跨图影响传播 ─────────────────────────────────────────────

    def cross_impact(self, changed_files: list[str]) -> CrossImpactResult:
        """代码变更 → 受影响的代码符号 → 关联的 Wiki 文档 → 过期风险

        Args:
            changed_files: 变更的文件路径列表

        Returns:
            CrossImpactResult 包含过期文档列表
        """
        result = CrossImpactResult(changed_files=changed_files)

        # 1. 找到变更文件中的所有符号
        affected_symbols = []
        for file_path in changed_files:
            nodes = self.code_store.get_nodes_by_file(file_path)
            for node in nodes:
                if node.kind != NodeKind.FILE:
                    affected_symbols.append(node.uid)

        result.affected_symbols = affected_symbols

        # 2. 通过反向索引找到关联文档
        stale_page_ids: set[str] = set()
        for uid in affected_symbols:
            page_ids = self._reverse_index.get(uid, [])
            stale_page_ids.update(page_ids)

        # 3. 生成过期文档报告
        for page_id in stale_page_ids:
            anchor = self._anchors.get(page_id)
            if not anchor:
                continue

            # 确定哪些锚定符号受影响
            affected_anchors = [
                uid for uid in anchor.code_uids if uid in affected_symbols
            ]

            stale = StaleDoc(
                page_id=page_id,
                page_title=anchor.page_title,
                reason="code_changed",
                affected_symbols=affected_anchors,
                last_code_change=datetime.now(timezone.utc).isoformat(),
                severity=self._assess_severity(affected_anchors),
            )
            result.stale_docs.append(stale)

        result.total_at_risk = len(result.stale_docs)
        return result

    def check_staleness(self) -> list[StaleDoc]:
        """全局过期检查: 找出所有锚定了已删除/不存在代码的文档"""
        stale_docs = []

        for page_id, anchor in self._anchors.items():
            missing = []
            for uid in anchor.code_uids:
                node = self.code_store.get_node(uid)
                if node is None:
                    missing.append(uid)

            if missing:
                stale_docs.append(StaleDoc(
                    page_id=page_id,
                    page_title=anchor.page_title,
                    reason="code_deleted",
                    affected_symbols=missing,
                    severity="critical" if len(missing) == len(anchor.code_uids) else "warning",
                ))

        return stale_docs

    # ─── Wiki 扫描 (自动发现锚定) ─────────────────────────────────

    def scan_wiki_for_anchors(self) -> int:
        """扫描 Wiki 目录，从 frontmatter 中提取 code_anchors

        支持的 frontmatter 格式:
        ---
        code_anchors:
          - "src/auth.py::AuthService"
          - "src/auth.py::generate_token"
        ---

        Returns:
            发现的锚定数量
        """
        if not self.wiki_path.exists():
            return 0

        count = 0
        for md_file in self.wiki_path.rglob("*.md"):
            anchors = self._extract_anchors_from_frontmatter(md_file)
            if anchors:
                page_id = md_file.stem
                self.anchor_page(page_id, page_id, anchors)
                count += len(anchors)

        logger.info(f"Wiki scan: {count} code anchors from {self.wiki_path}")
        return count

    def _extract_anchors_from_frontmatter(self, file_path: Path) -> list[str]:
        """从 Markdown frontmatter 提取 code_anchors"""
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError:
            return []

        # 解析 YAML frontmatter
        if not content.startswith("---"):
            return []

        end = content.find("---", 3)
        if end == -1:
            return []

        frontmatter = content[3:end]
        anchors = []

        # 简单解析 code_anchors 列表
        in_anchors = False
        for line in frontmatter.split("\n"):
            stripped = line.strip()
            if stripped.startswith("code_anchors:"):
                in_anchors = True
                continue
            if in_anchors:
                if stripped.startswith("- "):
                    # 提取引号内的 UID
                    uid = stripped[2:].strip().strip('"').strip("'")
                    if uid:
                        anchors.append(uid)
                elif stripped and not stripped.startswith("#"):
                    in_anchors = False

        return anchors

    # ─── 统计 ─────────────────────────────────────────────────────

    def stats(self) -> dict:
        """桥接层统计"""
        return {
            "anchored_pages": len(self._anchors),
            "linked_symbols": len(self._reverse_index),
            "total_links": sum(len(v) for v in self._reverse_index.values()),
        }

    # ─── 内部工具 ─────────────────────────────────────────────────

    def _assess_severity(self, affected_symbols: list[str]) -> str:
        """评估过期严重度"""
        if not affected_symbols:
            return "info"

        # 检查是否有高影响符号 (被大量依赖)
        for uid in affected_symbols:
            incoming = self.code_store.get_incoming_edges(uid)
            if len(incoming) >= 5:
                return "critical"

        return "warning" if len(affected_symbols) >= 3 else "info"

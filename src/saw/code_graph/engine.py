"""Code Graph Engine — 六阶段生命周期编排

Parse → Build → PostProcess → Query → Review → Update
"""

from __future__ import annotations

import logging
import time
from collections import deque
from pathlib import Path
from typing import Optional

from saw.code_graph.models import (
    BuildResult,
    CodeEdge,
    CodeNode,
    EdgeType,
    ImpactScore,
    NodeKind,
    EDGE_WEIGHTS,
    DEPTH_DECAY,
    SCORE_FLOOR,
)
from saw.code_graph.parser import CodeParser
from saw.code_graph.store import CodeGraphStore
from saw.code_graph.incremental import IncrementalBuilder
from saw.code_graph.postprocess import PostProcessor
from saw.code_graph.flows import FlowTracer, ExecutionFlow
from saw.code_graph.communities import CommunityDetector, Community, ArchitectureOverview

logger = logging.getLogger(__name__)


class CodeGraphEngine:
    """代码图生命周期引擎

    统一入口，编排六阶段:
    1. Parse: Tree-sitter/AST 解析源码
    2. Build: 持久化到 SQLite
    3. PostProcess: 派生结构 (FTS/社区/流)
    4. Query: 影响分析/图查询/搜索
    5. Review: 变更风险评估
    6. Update: 增量同步
    """

    def __init__(
        self,
        root_path: str | Path,
        db_path: Optional[str | Path] = None,
    ):
        self.root_path = Path(root_path).resolve()

        # 默认 DB 路径: {root}/.saw/code_graph.db
        if db_path is None:
            db_path = self.root_path / ".saw" / "code_graph.db"
        self.db_path = Path(db_path)

        self.store = CodeGraphStore(self.db_path)
        self.parser = CodeParser(self.root_path)
        self.builder = IncrementalBuilder(self.root_path, self.store, self.parser)
        self.postprocessor = PostProcessor(self.store)
        self.flow_tracer = FlowTracer(self.store)
        self.community_detector = CommunityDetector(self.store)

    # ─── Phase 1+2: Parse & Build ────────────────────────────────

    def build(self, full: bool = False, languages: Optional[list[str]] = None, postprocess: bool = True) -> BuildResult:
        """构建代码图

        Args:
            full: True = 全量重建, False = 增量更新
            languages: 限定语言 (e.g., ["python", "typescript"])
            postprocess: 构建后是否自动执行 PostProcess 管线
        """
        if full:
            result = self.builder.full_build(languages)
        else:
            # 首次构建时自动全量
            if self.store.node_count() == 0:
                logger.info("Empty graph detected, running full build")
                result = self.builder.full_build(languages)
            else:
                result = self.builder.incremental_update(languages)

        # Phase 3: PostProcess
        if postprocess and result.files_parsed > 0:
            self.postprocess()

        return result

    def update(self, languages: Optional[list[str]] = None) -> BuildResult:
        """增量更新（Phase 6 快捷入口）"""
        result = self.builder.incremental_update(languages)
        if result.files_parsed > 0:
            self.postprocess()
        return result

    # ─── Phase 3: PostProcess ────────────────────────────────────

    def postprocess(self) -> dict:
        """执行后处理管线: 裸名解析 → 签名 → FTS 校验"""
        return self.postprocessor.run()

    def trace_flows(self, max_depth: int = 10) -> list[ExecutionFlow]:
        """追踪执行流"""
        return self.flow_tracer.trace_flows(max_depth=max_depth)

    def get_affected_flows(self, changed_uids: list[str]) -> list[ExecutionFlow]:
        """获取受变更影响的执行流"""
        return self.flow_tracer.get_affected_flows(changed_uids)

    def detect_communities(self) -> list[Community]:
        """社区检测"""
        return self.community_detector.detect()

    def architecture_overview(self) -> ArchitectureOverview:
        """架构概览: 社区 + hub + bridge"""
        return self.community_detector.architecture_overview()

    # ─── Phase 4: Query ──────────────────────────────────────────

    def get_node(self, uid: str) -> Optional[CodeNode]:
        """按 UID 获取节点"""
        return self.store.get_node(uid)

    def find_nodes_by_name(self, name: str) -> list[CodeNode]:
        """按名称查找节点"""
        return self.store.find_nodes_by_name(name)

    def get_all_nodes(self) -> list[CodeNode]:
        """获取所有节点"""
        return self.store.get_all_nodes()

    def get_outgoing_edges(self, uid: str, types: Optional[list] = None) -> list[CodeEdge]:
        """获取出边"""
        type_strs = [t.value if isinstance(t, EdgeType) else t for t in types] if types else None
        return self.store.get_outgoing_edges(uid, type_strs)

    def get_incoming_edges(self, uid: str, types: Optional[list] = None) -> list[CodeEdge]:
        """获取入边"""
        type_strs = [t.value if isinstance(t, EdgeType) else t for t in types] if types else None
        return self.store.get_incoming_edges(uid, type_strs)

    def search(self, query: str, limit: int = 20) -> list[CodeNode]:
        """FTS5 全文搜索"""
        return self.store.search_nodes_fts(query, limit)

    def impact_analysis(
        self,
        target: str,
        direction: str = "upstream",
        max_depth: int = 3,
        min_score: float = SCORE_FLOOR,
        edge_types: Optional[list[str]] = None,
    ) -> list[ImpactScore]:
        """加权 BFS 影响分析

        算法 (参考 code-review-graph):
        - score = parent_score × edge_weight × depth_decay
        - 最佳分数松弛: 每个节点只保留最高分
        - 分数地板剪枝: score < min_score 时停止

        Args:
            target: 目标符号名或 UID
            direction: 'upstream' (谁依赖我) / 'downstream' (我依赖谁)
            max_depth: 最大遍历深度
            min_score: 分数地板
            edge_types: 限定边类型
        """
        # 查找目标节点
        target_node = self._resolve_target(target)
        if not target_node:
            return []

        # 加权 BFS
        scores: dict[str, ImpactScore] = {}
        queue: deque[tuple[str, float, int]] = deque([(target_node.uid, 1.0, 0)])
        visited: set[str] = {target_node.uid}

        allowed_types = edge_types or [
            EdgeType.CALLS.value, EdgeType.IMPORTS.value,
            EdgeType.INHERITS.value, EdgeType.IMPLEMENTS.value,
            EdgeType.REFERENCES.value,
        ]

        while queue:
            node_uid, parent_score, depth = queue.popleft()

            if depth >= max_depth:
                continue

            # 获取边
            if direction == "upstream":
                edges = self.store.get_incoming_edges(node_uid, allowed_types)
            else:
                edges = self.store.get_outgoing_edges(node_uid, allowed_types)

            for edge in edges:
                neighbor_uid = edge.source if direction == "upstream" else edge.target

                if neighbor_uid in visited:
                    continue

                # 单跳衰减: parent_score 已包含前序累积衰减，此处仅乘一次
                new_score = parent_score * edge.weight * DEPTH_DECAY
                if new_score < min_score:
                    continue

                visited.add(neighbor_uid)

                # 获取邻居节点信息
                neighbor = self.store.get_node(neighbor_uid)
                if neighbor is None:
                    # 可能是裸名边（未解析），跳过
                    continue

                risk_level = self._depth_to_risk(depth + 1)
                scores[neighbor_uid] = ImpactScore(
                    uid=neighbor_uid,
                    name=neighbor.name,
                    kind=neighbor.kind.value,
                    file_path=neighbor.file_path,
                    score=new_score,
                    depth=depth + 1,
                    edge_type=edge.edge_type.value,
                    risk_level=risk_level,
                )

                queue.append((neighbor_uid, new_score, depth + 1))

        # 按分数降序排列
        return sorted(scores.values(), key=lambda x: (-x.score, x.depth))

    def callers_of(self, uid: str) -> list[CodeNode]:
        """谁调用了这个符号"""
        edges = self.store.get_incoming_edges(uid, [EdgeType.CALLS.value])
        nodes = []
        for e in edges:
            n = self.store.get_node(e.source)
            if n:
                nodes.append(n)
        return nodes

    def callees_of(self, uid: str) -> list[CodeNode]:
        """这个符号调用了谁"""
        edges = self.store.get_outgoing_edges(uid, [EdgeType.CALLS.value])
        nodes = []
        for e in edges:
            n = self.store.get_node(e.target)
            if n:
                nodes.append(n)
        return nodes

    def imports_of(self, uid: str) -> list[CodeNode]:
        """这个文件导入了什么"""
        edges = self.store.get_outgoing_edges(uid, [EdgeType.IMPORTS.value])
        nodes = []
        for e in edges:
            n = self.store.get_node(e.target)
            if n:
                nodes.append(n)
        return nodes

    def tests_for(self, uid: str) -> list[CodeNode]:
        """这个符号的测试"""
        edges = self.store.get_incoming_edges(uid, [EdgeType.TESTED_BY.value])
        nodes = []
        for e in edges:
            n = self.store.get_node(e.source)
            if n:
                nodes.append(n)
        return nodes

    # ─── Phase 5: Review ─────────────────────────────────────────

    def detect_changes(self) -> dict:
        """检测当前变更并评估风险

        Returns:
            {
                "changed_files": [...],
                "affected_symbols": [...],
                "risk_score": float,
                "test_gaps": [...],
            }
        """
        changed, removed = self.builder._detect_changes()

        affected_symbols = []
        test_gaps = []
        total_risk = 0.0

        for file_path in changed:
            nodes = self.store.get_nodes_by_file(file_path)
            for node in nodes:
                if node.kind in (NodeKind.FUNCTION, NodeKind.METHOD, NodeKind.CLASS):
                    # 计算影响半径
                    impacts = self.impact_analysis(node.uid, max_depth=2)
                    risk = len(impacts) * 0.1
                    total_risk += risk

                    # 检查测试覆盖
                    tests = self.tests_for(node.uid)
                    if not tests:
                        test_gaps.append(node.uid)

                    affected_symbols.append({
                        "uid": node.uid,
                        "name": node.name,
                        "kind": node.kind.value,
                        "impact_count": len(impacts),
                        "has_tests": len(tests) > 0,
                    })

        return {
            "changed_files": changed,
            "removed_files": removed,
            "affected_symbols": affected_symbols,
            "risk_score": min(total_risk, 1.0),
            "test_gaps": test_gaps,
        }

    # ─── 健康与统计 ───────────────────────────────────────────────

    def health(self) -> dict:
        """健康检查"""
        return self.store.health_check()

    def stats(self) -> dict:
        """图统计"""
        return {
            "nodes": self.store.node_count(),
            "edges": self.store.edge_count(),
            "files": self.store.file_count(),
            "db_path": str(self.db_path),
        }

    # ─── 内部工具 ─────────────────────────────────────────────────

    def _resolve_target(self, target: str) -> Optional[CodeNode]:
        """解析目标: UID 精确匹配 → 名称模糊匹配"""
        # 精确 UID
        node = self.store.get_node(target)
        if node:
            return node

        # 名称匹配
        nodes = self.store.find_nodes_by_name(target)
        if nodes:
            return nodes[0]

        # FTS 搜索降级
        results = self.store.search_nodes_fts(target, limit=1)
        if results:
            return results[0]

        return None

    @staticmethod
    def _depth_to_risk(depth: int) -> str:
        """深度 → 风险等级"""
        if depth == 1:
            return "WILL_BREAK"
        elif depth == 2:
            return "LIKELY_AFFECTED"
        else:
            return "MAY_NEED_TESTING"

    def close(self) -> None:
        """关闭引擎"""
        self.store.close()

    def __enter__(self) -> "CodeGraphEngine":
        return self

    def __exit__(self, *args) -> None:
        self.close()

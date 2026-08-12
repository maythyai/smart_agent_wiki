"""执行流追踪 — 入口点检测 + 前向 BFS + 关键度评分

检测框架入口点（装饰器、命名约定、无入边节点），
沿 CALLS 边前向追踪执行路径，评估关键度。
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from saw.code_graph.models import CodeNode, EdgeType, NodeKind
from saw.code_graph.store import CodeGraphStore

logger = logging.getLogger(__name__)

# 入口点命名约定
ENTRY_POINT_PATTERNS = {
    "main", "app", "run", "start", "serve", "handle",
    "cli", "entry", "bootstrap", "init_app", "create_app",
}

# 安全敏感关键词 (关键度加分)
SECURITY_KEYWORDS = {
    "auth", "login", "password", "token", "secret", "key",
    "permission", "role", "admin", "encrypt", "decrypt",
    "sign", "verify", "validate", "sanitize", "escape",
}


@dataclass
class FlowNode:
    """执行流中的节点"""
    uid: str
    name: str
    kind: str
    file_path: str
    depth: int


@dataclass
class ExecutionFlow:
    """一条执行流"""
    flow_id: str
    entry_point: str          # 入口节点 UID
    entry_name: str
    nodes: list[FlowNode] = field(default_factory=list)
    length: int = 0
    criticality: float = 0.0  # 0-1 关键度
    has_tests: bool = False
    security_sensitive: bool = False
    files_touched: list[str] = field(default_factory=list)


class FlowTracer:
    """执行流追踪器

    算法:
    1. 检测入口点 (框架装饰器 + 命名约定 + 无入边)
    2. 前向 BFS 沿 CALLS 边追踪
    3. 关键度评分 (安全关键词 + 测试覆盖 + 路径长度)
    """

    def __init__(self, store: CodeGraphStore):
        self.store = store

    def trace_flows(self, max_depth: int = 10, min_criticality: float = 0.0) -> list[ExecutionFlow]:
        """追踪所有执行流

        Args:
            max_depth: 最大追踪深度
            min_criticality: 最低关键度阈值

        Returns:
            按关键度降序排列的执行流列表
        """
        start = time.time()

        entry_points = self._detect_entry_points()
        flows = []

        for entry_uid in entry_points:
            flow = self._trace_single_flow(entry_uid, max_depth)
            if flow and flow.criticality >= min_criticality:
                flows.append(flow)

        # 按关键度降序
        flows.sort(key=lambda f: -f.criticality)

        elapsed = (time.time() - start) * 1000
        logger.info(f"Flow tracing: {len(flows)} flows from {len(entry_points)} entries, {elapsed:.0f}ms")
        return flows

    def get_affected_flows(self, changed_uids: list[str], max_depth: int = 10) -> list[ExecutionFlow]:
        """获取受变更影响的执行流

        Args:
            changed_uids: 变更的节点 UID 列表
            max_depth: 最大追踪深度

        Returns:
            包含变更节点的执行流
        """
        all_flows = self.trace_flows(max_depth)
        changed_set = set(changed_uids)

        affected = []
        for flow in all_flows:
            flow_uids = {n.uid for n in flow.nodes}
            if flow_uids & changed_set:
                affected.append(flow)

        return affected

    # ─── 入口点检测 ───────────────────────────────────────────────

    def _detect_entry_points(self) -> list[str]:
        """检测入口点

        策略 (优先级从高到低):
        1. ENDPOINT 类型节点 (框架路由装饰器)
        2. 命名约定匹配 (main, app, run, ...)
        3. 无入边 CALLS 的 FUNCTION/METHOD 节点

        性能: 使用单次 SQL 查询预计算被调用集合，避免 N+1 查询。
        """
        entries = []
        all_nodes = self.store.get_all_nodes()

        # 单次查询: 所有被 CALLS 边指向的 target UID 集合
        called_targets = self.store.get_called_targets(EdgeType.CALLS.value)

        for node in all_nodes:
            if node.kind == NodeKind.ENDPOINT:
                entries.append(node.uid)
                continue

            if node.kind in (NodeKind.FUNCTION, NodeKind.METHOD):
                # 命名约定 (全词匹配，避免 "prune" 匹配 "run" 等误判)
                name_lower = node.name.lower()
                name_tokens = set(name_lower.replace("-", "_").split("_"))
                if name_lower in ENTRY_POINT_PATTERNS or name_tokens & ENTRY_POINT_PATTERNS:
                    entries.append(node.uid)
                    continue

                # 无入边 CALLS (O(1) 集合查找代替 SQL 查询)
                if node.uid not in called_targets and node.kind == NodeKind.FUNCTION:
                    # 排除私有函数和测试
                    if not node.name.startswith("_") and node.kind != NodeKind.TEST:
                        entries.append(node.uid)

        return entries

    # ─── 单流追踪 ─────────────────────────────────────────────────

    def _trace_single_flow(self, entry_uid: str, max_depth: int) -> Optional[ExecutionFlow]:
        """从入口点前向 BFS 追踪执行流"""
        entry_node = self.store.get_node(entry_uid)
        if not entry_node:
            return None

        flow = ExecutionFlow(
            flow_id=entry_uid,
            entry_point=entry_uid,
            entry_name=entry_node.name,
        )

        visited: set[str] = {entry_uid}
        queue: deque[tuple[str, int]] = deque([(entry_uid, 0)])
        files_touched: set[str] = {entry_node.file_path}

        while queue:
            uid, depth = queue.popleft()

            node = self.store.get_node(uid)
            if node:
                flow.nodes.append(FlowNode(
                    uid=uid,
                    name=node.name,
                    kind=node.kind.value,
                    file_path=node.file_path,
                    depth=depth,
                ))
                files_touched.add(node.file_path)

            if depth >= max_depth:
                continue

            # 沿 CALLS 边前向追踪
            outgoing = self.store.get_outgoing_edges(uid, [EdgeType.CALLS.value])
            for edge in outgoing:
                if edge.target not in visited:
                    # 确认 target 是有效节点 (非裸名)
                    target_node = self.store.get_node(edge.target)
                    if target_node:
                        visited.add(edge.target)
                        queue.append((edge.target, depth + 1))

        flow.length = len(flow.nodes)
        flow.files_touched = sorted(files_touched)

        # 关键度评分
        flow.criticality = self._score_criticality(flow)
        flow.security_sensitive = self._check_security(flow)
        # M1: TESTED_BY edges are never generated by the parser — always False.
        flow.has_tests = False

        return flow

    # ─── 关键度评分 ───────────────────────────────────────────────

    def _score_criticality(self, flow: ExecutionFlow) -> float:
        """关键度评分 (0-1)

        因子:
        - 路径长度 (越长越关键)
        - 跨文件数 (越多越关键)
        - 安全敏感 (加分)
        - 测试覆盖 (有测试降分)
        """
        score = 0.0

        # 路径长度因子 (0-0.3)
        score += min(flow.length / 20.0, 1.0) * 0.3

        # 跨文件因子 (0-0.3)
        score += min(len(flow.files_touched) / 5.0, 1.0) * 0.3

        # 安全敏感 (0-0.25)
        if self._check_security(flow):
            score += 0.25

        # 入口点类型 (ENDPOINT 更关键)
        entry_node = self.store.get_node(flow.entry_point)
        if entry_node and entry_node.kind == NodeKind.ENDPOINT:
            score += 0.15

        # 测试覆盖 (有测试降 0.1; M1: TESTED_BY never generated, always False)
        if False:
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _check_security(self, flow: ExecutionFlow) -> bool:
        """检查执行流是否涉及安全敏感操作"""
        for node in flow.nodes:
            name_lower = node.name.lower()
            if any(kw in name_lower for kw in SECURITY_KEYWORDS):
                return True
        return False

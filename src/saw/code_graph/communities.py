"""社区检测 — Leiden/Louvain 图聚类

将代码图按调用/依赖关系聚类为架构模块，
生成社区名称，识别 hub 节点和 bridge 节点。
"""

from __future__ import annotations

import logging
import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from saw.code_graph.models import CodeNode, CodeEdge, EdgeType, NodeKind, EDGE_WEIGHTS
from saw.code_graph.store import CodeGraphStore

logger = logging.getLogger(__name__)


@dataclass
class Community:
    """一个代码社区 (架构模块)"""
    community_id: int
    name: str
    members: list[str] = field(default_factory=list)  # node UIDs
    size: int = 0
    files: list[str] = field(default_factory=list)
    hub_nodes: list[str] = field(default_factory=list)  # 高连接度节点
    description: str = ""


@dataclass
class ArchitectureOverview:
    """架构概览"""
    communities: list[Community] = field(default_factory=list)
    hub_nodes: list[dict] = field(default_factory=list)    # 全局 hub
    bridge_nodes: list[dict] = field(default_factory=list)  # 跨社区桥接
    total_nodes: int = 0
    total_edges: int = 0
    modularity: float = 0.0


class CommunityDetector:
    """社区检测器

    算法选择:
    - 优先: Leiden (igraph) — 更稳定
    - 降级: 简化 Louvain (纯 Python) — 无外部依赖
    - 兜底: 文件级分组 — 按目录聚类
    """

    def __init__(self, store: CodeGraphStore):
        self.store = store

    def detect(self, resolution: float = 1.0) -> list[Community]:
        """执行社区检测

        Args:
            resolution: 分辨率参数 (越大 → 越多社区)

        Returns:
            社区列表
        """
        start = time.time()

        # 尝试 Leiden (igraph)
        communities = self._try_leiden(resolution)

        # 降级: 简化 Louvain
        if communities is None:
            communities = self._louvain_fallback()

        # 兜底: 文件级分组
        if not communities:
            communities = self._file_based_grouping()

        # 生成社区名称和元数据
        for c in communities:
            c.name = self._generate_name(c)
            c.size = len(c.members)
            c.files = self._get_community_files(c)
            c.hub_nodes = self._find_hubs(c)

        elapsed = (time.time() - start) * 1000
        logger.info(f"Community detection: {len(communities)} communities, {elapsed:.0f}ms")
        return communities

    def architecture_overview(self) -> ArchitectureOverview:
        """生成架构概览"""
        communities = self.detect()

        overview = ArchitectureOverview(
            communities=communities,
            total_nodes=self.store.node_count(),
            total_edges=self.store.edge_count(),
        )

        # 全局 hub 节点 (高入度)
        overview.hub_nodes = self._find_global_hubs()

        # Bridge 节点 (跨社区连接)
        overview.bridge_nodes = self._find_bridges(communities)

        return overview

    # ─── Leiden (igraph) ─────────────────────────────────────────

    def _try_leiden(self, resolution: float) -> Optional[list[Community]]:
        """尝试使用 igraph Leiden 算法"""
        try:
            import igraph as ig
        except ImportError:
            return None

        # 构建 igraph 图
        nodes = self.store.get_all_nodes()
        non_file_nodes = [n for n in nodes if n.kind != NodeKind.FILE]
        if not non_file_nodes:
            return []

        uid_to_idx = {n.uid: i for i, n in enumerate(non_file_nodes)}
        g = ig.Graph(directed=False)
        g.add_vertices(len(non_file_nodes))

        # 添加边 (带权重)
        edges = []
        weights = []
        seen_edges: set[tuple[int, int]] = set()

        for node in non_file_nodes:
            outgoing = self.store.get_outgoing_edges(node.uid)
            for edge in outgoing:
                if edge.target in uid_to_idx:
                    src_idx = uid_to_idx[node.uid]
                    tgt_idx = uid_to_idx[edge.target]
                    pair = (min(src_idx, tgt_idx), max(src_idx, tgt_idx))
                    if pair not in seen_edges and src_idx != tgt_idx:
                        seen_edges.add(pair)
                        edges.append(pair)
                        weights.append(edge.weight)

        if edges:
            g.add_edges(edges)
            g.es["weight"] = weights

        # Leiden 聚类
        try:
            partition = g.community_leiden(
                objective_function="modularity",
                weights="weight",
                resolution_parameter=resolution,
                seed=42,  # 可复现
            )
        except Exception:
            return None

        # 转换为 Community 对象
        communities = []
        for comm_id, member_indices in enumerate(partition):
            members = [non_file_nodes[i].uid for i in member_indices]
            communities.append(Community(
                community_id=comm_id,
                name="",
                members=members,
            ))

        return communities

    # ─── Louvain 降级 ─────────────────────────────────────────────

    def _louvain_fallback(self) -> list[Community]:
        """简化 Louvain: 基于连通分量的聚类"""
        nodes = self.store.get_all_nodes()
        non_file_nodes = [n for n in nodes if n.kind != NodeKind.FILE]
        if not non_file_nodes:
            return []

        # 构建邻接表
        adjacency: dict[str, set[str]] = defaultdict(set)
        for node in non_file_nodes:
            outgoing = self.store.get_outgoing_edges(node.uid)
            for edge in outgoing:
                if "::" in edge.target:  # 只处理已解析的边
                    adjacency[node.uid].add(edge.target)
                    adjacency[edge.target].add(node.uid)

        # BFS 连通分量
        visited: set[str] = set()
        communities = []
        comm_id = 0

        for node in non_file_nodes:
            if node.uid in visited:
                continue
            # BFS
            component = []
            queue = [node.uid]
            while queue:
                uid = queue.pop(0)
                if uid in visited:
                    continue
                visited.add(uid)
                component.append(uid)
                for neighbor in adjacency.get(uid, set()):
                    if neighbor not in visited:
                        queue.append(neighbor)

            if component:
                communities.append(Community(
                    community_id=comm_id,
                    name="",
                    members=component,
                ))
                comm_id += 1

        return communities

    # ─── 文件级分组兜底 ───────────────────────────────────────────

    def _file_based_grouping(self) -> list[Community]:
        """按目录/文件分组"""
        nodes = self.store.get_all_nodes()
        file_groups: dict[str, list[str]] = defaultdict(list)

        for node in nodes:
            if node.kind != NodeKind.FILE:
                # 按文件路径的父目录分组
                parts = node.file_path.split("/")
                group_key = "/".join(parts[:-1]) if len(parts) > 1 else parts[0]
                file_groups[group_key].append(node.uid)

        communities = []
        for comm_id, (group, members) in enumerate(file_groups.items()):
            communities.append(Community(
                community_id=comm_id,
                name=group,
                members=members,
            ))

        return communities

    # ─── 社区元数据 ───────────────────────────────────────────────

    def _generate_name(self, community: Community) -> str:
        """从成员词汇生成社区名称"""
        if community.name:
            return community.name

        # 统计成员名称中的词频
        word_freq: dict[str, int] = defaultdict(int)
        for uid in community.members:
            node = self.store.get_node(uid)
            if node:
                # 拆分 camelCase 和 snake_case
                words = self._split_name(node.name)
                for w in words:
                    if len(w) > 2 and w.lower() not in ("the", "and", "for", "get", "set"):
                        word_freq[w.lower()] += 1

        if not word_freq:
            return f"module_{community.community_id}"

        # 取 top-2 高频词
        top_words = sorted(word_freq.items(), key=lambda x: -x[1])[:2]
        return "_".join(w[0] for w in top_words)

    def _get_community_files(self, community: Community) -> list[str]:
        """获取社区涉及的文件列表"""
        files: set[str] = set()
        for uid in community.members:
            node = self.store.get_node(uid)
            if node:
                files.add(node.file_path)
        return sorted(files)

    def _find_hubs(self, community: Community, top_n: int = 3) -> list[str]:
        """找到社区内的高连接度节点"""
        member_set = set(community.members)
        degrees: list[tuple[str, int]] = []

        for uid in community.members:
            out_degree = len(self.store.get_outgoing_edges(uid))
            in_degree = len(self.store.get_incoming_edges(uid))
            # 只计算社区内部的连接
            internal_out = sum(
                1 for e in self.store.get_outgoing_edges(uid)
                if e.target in member_set
            )
            internal_in = sum(
                1 for e in self.store.get_incoming_edges(uid)
                if e.source in member_set
            )
            degrees.append((uid, internal_out + internal_in))

        degrees.sort(key=lambda x: -x[1])
        return [uid for uid, _ in degrees[:top_n]]

    def _find_global_hubs(self, top_n: int = 10) -> list[dict]:
        """全局 hub 节点 (高入度 = 被大量依赖)"""
        nodes = self.store.get_all_nodes()
        hub_scores = []

        for node in nodes:
            if node.kind == NodeKind.FILE:
                continue
            in_degree = len(self.store.get_incoming_edges(node.uid))
            if in_degree > 0:
                hub_scores.append({
                    "uid": node.uid,
                    "name": node.name,
                    "kind": node.kind.value,
                    "in_degree": in_degree,
                    "file_path": node.file_path,
                })

        hub_scores.sort(key=lambda x: -x["in_degree"])
        return hub_scores[:top_n]

    def _find_bridges(self, communities: list[Community]) -> list[dict]:
        """找到跨社区桥接节点"""
        # 建立 uid → community_id 映射
        uid_to_comm: dict[str, int] = {}
        for comm in communities:
            for uid in comm.members:
                uid_to_comm[uid] = comm.community_id

        bridges = []
        for uid, comm_id in uid_to_comm.items():
            # 检查是否有跨社区的边
            outgoing = self.store.get_outgoing_edges(uid)
            cross_community = 0
            for edge in outgoing:
                target_comm = uid_to_comm.get(edge.target)
                if target_comm is not None and target_comm != comm_id:
                    cross_community += 1

            if cross_community > 0:
                node = self.store.get_node(uid)
                if node:
                    bridges.append({
                        "uid": uid,
                        "name": node.name,
                        "community": comm_id,
                        "cross_links": cross_community,
                    })

        bridges.sort(key=lambda x: -x["cross_links"])
        return bridges[:20]

    @staticmethod
    def _split_name(name: str) -> list[str]:
        """拆分 camelCase / snake_case / PascalCase"""
        import re
        # snake_case
        if "_" in name:
            return [p for p in name.split("_") if p]
        # camelCase / PascalCase
        parts = re.sub(r"([A-Z])", r" \1", name).split()
        return [p for p in parts if p]

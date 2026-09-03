"""
Community Detection - Louvain 社区检测

自动发现知识聚类
"""

from dataclasses import dataclass, field


@dataclass
class Community:
    """知识社区"""
    community_id: int
    label: str  # 代表节点标题
    members: list[str]  # node IDs
    cohesion: float  # 内部连接密度
    color: str  # 可视化颜色

    def to_dict(self) -> dict:
        return {
            "community_id": self.community_id,
            "label": self.label,
            "members": self.members,
            "cohesion": self.cohesion,
            "color": self.color,
        }


@dataclass
class CommunityResult:
    """社区检测结果"""
    communities: list[Community] = field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0
    detection_time: float = 0.0


class CommunityDetector:
    """
    Louvain 社区检测器

    基于图拓扑自动发现知识聚类：
    1. 模块度优化
    2. 层级聚合
    3. 内聚度评分
    """

    # 12色调色板（来自 llm_wiki）
    COLORS = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4",
        "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F",
        "#BB8FCE", "#85C1E9", "#F8B500", "#00CED1",
    ]

    def __init__(self):
        self.nodes: dict[str, int] = {}  # node_id -> community_id
        self.communities: dict[int, set[str]] = {}  # community_id -> members

    def detect(
        self,
        nodes: dict[str, dict],
        edges: dict[tuple[str, str], dict],
    ) -> CommunityResult:
        """
        执行 Louvain 算法

        Args:
            nodes: {node_id: node_data}
            edges: {(source, target): edge_data}

        Returns:
            检测结果
        """
        from time import time
        start_time = time()

        # 初始化：每个节点一个社区
        self._initialize(nodes)

        # Phase 1: 局部移动
        improved = True
        # Convergence cap: a node can oscillate between two communities (move
        # A→B then B→A next pass), leaving ``improved`` True forever — an
        # infinite busy-loop. Cap iterations so detect() always terminates.
        max_iterations = 100
        iteration = 0
        while improved and iteration < max_iterations:
            improved = self._phase_one(nodes, edges)
            iteration += 1

        # Phase 2: 社区聚合（简化实现）
        # 不迭代多层，保持单层结果

        # 构建结果
        communities = self._build_communities(nodes, edges)

        detection_time = time() - start_time

        return CommunityResult(
            communities=communities,
            total_nodes=len(nodes),
            total_edges=len(edges),
            detection_time=detection_time,
        )

    def _initialize(self, nodes: dict[str, dict]) -> None:
        """初始化社区"""
        for i, node_id in enumerate(nodes.keys()):
            self.nodes[node_id] = i
            self.communities[i] = {node_id}

    def _phase_one(
        self,
        nodes: dict[str, dict],
        edges: dict[tuple[str, str], dict],
    ) -> bool:
        """
        Phase 1: 局部节点移动

        尝试将每个节点移到能最大化模块度的社区
        """
        improved = False

        for node_id in nodes.keys():
            # 计算当前模块度贡献
            current_community = self.nodes[node_id]

            # 找邻居所属的社区
            neighbor_communities = self._get_neighbor_communities(
                node_id, edges
            )

            # 计算每个候选社区的模块度增益
            best_gain = 0.0
            best_community = current_community

            for community_id in neighbor_communities:
                if community_id == current_community:
                    continue

                gain = self._calculate_modularity_gain(
                    node_id, current_community, community_id, edges
                )

                if gain > best_gain:
                    best_gain = gain
                    best_community = community_id

            # 如果有正增益，移动节点
            if best_community != current_community:
                self._move_node(node_id, current_community, best_community)
                improved = True

        return improved

    def _get_neighbor_communities(
        self,
        node_id: str,
        edges: dict[tuple[str, str], dict],
    ) -> set[int]:
        """获取邻居所属的社区"""
        communities = set()

        for (a, b) in edges.keys():
            if a == node_id and b in self.nodes:
                communities.add(self.nodes[b])
            elif b == node_id and a in self.nodes:
                communities.add(self.nodes[a])

        return communities

    def _calculate_modularity_gain(
        self,
        node_id: str,
        from_community: int,
        to_community: int,
        edges: dict[tuple[str, str], dict],
    ) -> float:
        """
        计算模块度增益

        ΔQ = (ki_in / 2m) - (ki * Σtot / 2m²)

        简化实现：基于边数计算
        """
        # 获取社区边数
        from_edges = self._count_community_edges(from_community, edges)
        to_edges = self._count_community_edges(to_community, edges)

        # 节点与目标社区的连接数
        ki_in = self._count_node_community_edges(node_id, to_community, edges)

        # 节点总连接数
        ki = self._count_node_edges(node_id, edges)

        # 总边数
        m = len(edges)

        # 简化模块度增益计算
        gain = ki_in / (2 * m) if m > 0 else 0

        return gain

    def _move_node(
        self,
        node_id: str,
        from_community: int,
        to_community: int,
    ) -> None:
        """移动节点到新社区"""
        # 从旧社区移除
        self.communities[from_community].discard(node_id)

        # 加入新社区
        if to_community not in self.communities:
            self.communities[to_community] = set()
        self.communities[to_community].add(node_id)

        # 更新节点映射
        self.nodes[node_id] = to_community

    def _count_community_edges(
        self,
        community_id: int,
        edges: dict[tuple[str, str], dict],
    ) -> int:
        """计算社区内部边数"""
        count = 0
        members = self.communities.get(community_id, set())

        for (a, b) in edges.keys():
            if a in members and b in members:
                count += 1

        return count

    def _count_node_edges(
        self,
        node_id: str,
        edges: dict[tuple[str, str], dict],
    ) -> int:
        """计算节点边数"""
        count = 0

        for (a, b) in edges.keys():
            if a == node_id or b == node_id:
                count += 1

        return count

    def _count_node_community_edges(
        self,
        node_id: str,
        community_id: int,
        edges: dict[tuple[str, str], dict],
    ) -> int:
        """计算节点与社区的边数"""
        count = 0
        members = self.communities.get(community_id, set())

        for (a, b) in edges.keys():
            if a == node_id and b in members:
                count += 1
            elif b == node_id and a in members:
                count += 1

        return count

    def _build_communities(
        self,
        nodes: dict[str, dict],
        edges: dict[tuple[str, str], dict],
    ) -> list[Community]:
        """构建社区结果"""
        communities = []

        for i, (community_id, members) in enumerate(sorted(
            self.communities.items(),
            key=lambda x: -len(x[1])  # 按成员数排序
        )):
            if len(members) < 1:
                continue

            # 选择代表节点（度最高的）
            label = self._select_label(members, nodes, edges)

            # 计算内聚度
            cohesion = self._calculate_cohesion(members, edges)

            # 分配颜色
            color = self.COLORS[i % len(self.COLORS)]

            community = Community(
                community_id=community_id,
                label=label,
                members=list(members),
                cohesion=cohesion,
                color=color,
            )

            communities.append(community)

        return communities

    def _select_label(
        self,
        members: set[str],
        nodes: dict[str, dict],
        edges: dict[tuple[str, str], dict],
    ) -> str:
        """选择社区代表标签"""
        best_node = None
        best_degree = -1

        for node_id in members:
            degree = self._count_node_edges(node_id, edges)
            if degree > best_degree:
                best_degree = degree
                best_node = node_id

        if best_node and best_node in nodes:
            return nodes[best_node].get("title", best_node)

        return list(members)[0] if members else "Unknown"

    def _calculate_cohesion(
        self,
        members: set[str],
        edges: dict[tuple[str, str], dict],
    ) -> float:
        """
        计算内聚度

        cohesion = actual_edges / possible_edges
        """
        if len(members) < 2:
            return 1.0

        # 实际内部边数
        actual = self._count_community_edges_internal(members, edges)

        # 可能的最大边数
        possible = len(members) * (len(members) - 1) // 2

        return actual / possible if possible > 0 else 0.0

    def _count_community_edges_internal(
        self,
        members: set[str],
        edges: dict[tuple[str, str], dict],
    ) -> int:
        """计算社区内部边数"""
        count = 0

        for (a, b) in edges.keys():
            if a in members and b in members:
                count += 1

        return count
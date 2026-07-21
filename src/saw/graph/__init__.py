"""
Knowledge Graph Module - 知识图谱引擎

基于 llm_wiki 的 4-Signal 相关性模型实现 + 代码图兼容层
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

from .relevance import RelevanceModel, RelevanceSignal
from .community import CommunityDetector
from .insights import InsightGenerator, GraphInsight
from .graph_engine import KnowledgeGraphEngine


# ─── 向后兼容: KnowledgeGraph 接口 ─────────────────────────────────
# 原 src/saw/graph.py 被本包遮蔽，将兼容层移至此处。
# 供 analysis/impact.py、analysis/process.py、mcp/tools/impact.py 使用。


class KnowledgeGraph:
    """Knowledge graph 兼容层 — 代理到 CodeGraphStore

    保持与现有 analysis 模块的接口兼容:
    - get_node(uid) → Optional[dict]
    - find_nodes_by_name(name) → list[dict]
    - get_incoming_edges(uid, types) → list[dict]
    - get_outgoing_edges(uid, types) → list[dict]
    - get_all_nodes() → list[dict]

    当 CodeGraphStore 可用时使用 SQLite 持久化后端;
    否则降级为内存 dict (向后兼容)。
    """

    def __init__(self, db_path: Optional[str | Path] = None):
        self._store = None
        self._fallback_nodes: dict[str, dict] = {}
        self._fallback_edges: list[dict] = []

        if db_path is not None:
            try:
                from saw.code_graph.store import CodeGraphStore
                self._store = CodeGraphStore(db_path)
            except ImportError:
                pass  # code_graph 未安装，降级到内存模式
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"Failed to open code graph store at {db_path}: {e}. "
                    f"Falling back to empty in-memory graph."
                )

    @property
    def nodes(self) -> dict[str, dict]:
        """兼容属性: 返回所有节点的 dict 视图"""
        if self._store:
            return {n.uid: n.to_dict() for n in self._store.get_all_nodes()}
        return self._fallback_nodes

    @property
    def edges(self) -> list[dict]:
        """兼容属性: 返回所有边的 list 视图"""
        if self._store:
            all_edges = []
            for node in self._store.get_all_nodes():
                for edge in self._store.get_outgoing_edges(node.uid):
                    all_edges.append(edge.to_dict())
            return all_edges
        return self._fallback_edges

    def get_node(self, uid: str) -> Optional[dict]:
        """Get node by UID."""
        if self._store:
            node = self._store.get_node(uid)
            return node.to_dict() if node else None
        return self._fallback_nodes.get(uid)

    def find_nodes_by_name(self, name: str) -> list[dict]:
        """Find nodes by name."""
        if self._store:
            return [n.to_dict() for n in self._store.find_nodes_by_name(name)]
        return [n for n in self._fallback_nodes.values() if n.get('name') == name]

    def get_incoming_edges(self, uid: str, types: list = None) -> list[dict]:
        """Get incoming edges."""
        if self._store:
            return [e.to_dict() for e in self._store.get_incoming_edges(uid, types)]
        types = types or []
        return [e for e in self._fallback_edges
                if e.get('target') == uid and (not types or e.get('type') in types)]

    def get_outgoing_edges(self, uid: str, types: list = None) -> list[dict]:
        """Get outgoing edges."""
        if self._store:
            return [e.to_dict() for e in self._store.get_outgoing_edges(uid, types)]
        types = types or []
        return [e for e in self._fallback_edges
                if e.get('source') == uid and (not types or e.get('type') in types)]

    def get_all_nodes(self) -> list[dict]:
        """Get all nodes."""
        if self._store:
            return [n.to_dict() for n in self._store.get_all_nodes()]
        return list(self._fallback_nodes.values())

    def close(self) -> None:
        """关闭底层存储"""
        if self._store:
            self._store.close()


# ─── 线程安全的全局实例管理 ─────────────────────────────────────────

_lock = threading.Lock()
_graph: Optional[KnowledgeGraph] = None


def get_graph(db_path: Optional[str | Path] = None) -> KnowledgeGraph:
    """Get the global knowledge graph instance (thread-safe).

    Args:
        db_path: 可选的 SQLite 路径。首次调用时传入可初始化持久化后端。
                 未传入时自动发现 CWD 下的 .saw/code_graph.db。
    """
    global _graph
    with _lock:
        if _graph is None:
            # 自动发现: 优先使用传入路径，否则查找 CWD/.saw/code_graph.db
            if db_path is None:
                candidate = Path(".saw/code_graph.db")
                if candidate.exists():
                    db_path = candidate
            _graph = KnowledgeGraph(db_path=db_path)
        return _graph


def set_graph(graph: KnowledgeGraph) -> None:
    """Set the global knowledge graph instance (thread-safe)."""
    global _graph
    with _lock:
        _graph = graph


def reset_graph() -> None:
    """Reset the global instance (for testing)."""
    global _graph
    with _lock:
        if _graph:
            _graph.close()
        _graph = None


__all__ = [
    "RelevanceModel",
    "RelevanceSignal",
    "CommunityDetector",
    "InsightGenerator",
    "GraphInsight",
    "KnowledgeGraphEngine",
    "KnowledgeGraph",
    "get_graph",
    "set_graph",
    "reset_graph",
]
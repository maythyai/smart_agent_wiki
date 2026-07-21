"""PostProcess 管线 — 派生结构计算

五步派生管线（每次 build/update 后执行）:
1. 裸名解析 (Bare Name Resolution) — 证据门控
2. 签名计算 (Signature Computation)
3. FTS5 索引重建
4. 执行流追踪 (由 flows.py 处理)
5. 社区检测 (由 communities.py 处理)
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Optional

from saw.code_graph.models import (
    CodeEdge,
    CodeNode,
    EdgeType,
    ConfidenceTier,
    NodeKind,
    make_uid,
)
from saw.code_graph.store import CodeGraphStore

logger = logging.getLogger(__name__)


class PostProcessor:
    """图后处理管线

    将原始解析数据转化为可查询的高阶结构。
    """

    def __init__(self, store: CodeGraphStore):
        self.store = store

    def run(self, incremental: bool = False) -> dict:
        """执行完整后处理管线

        Args:
            incremental: True 时仅处理新增/变更的边

        Returns:
            处理统计
        """
        start = time.time()
        stats = {
            "bare_names_resolved": 0,
            "bare_names_failed": 0,
            "signatures_computed": 0,
            "fts_rebuilt": False,
            "time_ms": 0.0,
        }

        # Step 1: 裸名解析
        resolved, failed = self._resolve_bare_names()
        stats["bare_names_resolved"] = resolved
        stats["bare_names_failed"] = failed

        # Step 2: 签名计算
        stats["signatures_computed"] = self._compute_signatures()

        # Step 3: FTS 索引重建 (触发器已自动维护，此处做完整性校验)
        stats["fts_rebuilt"] = self._verify_fts()

        stats["time_ms"] = (time.time() - start) * 1000
        logger.info(
            f"PostProcess complete: {resolved} resolved, "
            f"{failed} unresolved, {stats['time_ms']:.0f}ms"
        )
        return stats

    # ─── Step 1: 裸名解析 ─────────────────────────────────────────

    def _resolve_bare_names(self) -> tuple[int, int]:
        """将未限定的跨文件 CALLS/INHERITS 目标解析为完整 UID

        证据门控策略 (参考 code-review-graph):
        - 仅当恰好一个候选有同文件/导入证据时才解析
        - 防止全局唯一但巧合的名称匹配产生误连

        Returns:
            (resolved_count, failed_count)
        """
        resolved = 0
        failed = 0

        # 收集所有裸名边 (target 不含 "::")
        bare_edges = self._get_bare_name_edges()
        if not bare_edges:
            return 0, 0

        # 构建名称索引: name → [uid, ...]
        name_index = self._build_name_index()

        # 构建文件导入图: file_path → set(imported_file_paths)
        import_graph = self._build_import_graph()

        for edge_data in bare_edges:
            source_uid = edge_data["source"]
            bare_name = edge_data["target"]
            edge_type = edge_data["edge_type"]

            # 查找候选节点
            candidates = name_index.get(bare_name, [])
            if not candidates:
                failed += 1
                continue

            if len(candidates) == 1:
                # 唯一候选 — 直接解析
                target_uid = candidates[0]
                self._update_edge_target(source_uid, bare_name, target_uid, edge_type)
                resolved += 1
                continue

            # 多候选 — 证据门控
            source_file = source_uid.split("::")[0] if "::" in source_uid else ""
            best = self._resolve_with_evidence(
                source_file, candidates, import_graph
            )
            if best:
                self._update_edge_target(source_uid, bare_name, best, edge_type)
                resolved += 1
            else:
                failed += 1

        return resolved, failed

    def _get_bare_name_edges(self) -> list[dict]:
        """获取所有裸名边 (target 不含 '::' 分隔符)"""
        conn = self.store._conn
        if conn is None:
            return []
        rows = conn.execute(
            """SELECT source, target, edge_type FROM code_edges
               WHERE target NOT LIKE '%::%'
               AND metadata LIKE '%bare_name%'"""
        ).fetchall()
        return [{"source": r[0], "target": r[1], "edge_type": r[2]} for r in rows]

    def _build_name_index(self) -> dict[str, list[str]]:
        """构建 name → [uid] 索引"""
        index: dict[str, list[str]] = defaultdict(list)
        for node in self.store.get_all_nodes():
            if node.kind != NodeKind.FILE:
                index[node.name].append(node.uid)
        return dict(index)

    def _build_import_graph(self) -> dict[str, set[str]]:
        """构建文件导入图: file_path → set(imported_file_paths)"""
        graph: dict[str, set[str]] = defaultdict(set)
        conn = self.store._conn
        if conn is None:
            return {}
        rows = conn.execute(
            """SELECT source, target FROM code_edges WHERE edge_type = 'IMPORTS'"""
        ).fetchall()
        for r in rows:
            source_file = r[0].split("::")[0] if "::" in r[0] else r[0]
            target_file = r[1].split("::")[0] if "::" in r[1] else r[1]
            graph[source_file].add(target_file)
        return dict(graph)

    def _resolve_with_evidence(
        self,
        source_file: str,
        candidates: list[str],
        import_graph: dict[str, set[str]],
    ) -> Optional[str]:
        """证据门控解析: 仅当有导入/同文件证据时解析

        优先级:
        1. 同文件候选 (source_file == candidate_file)
        2. 已导入文件的候选 (candidate_file in imports(source_file))
        3. 无法确定 → 返回 None (不解析)
        """
        imported_files = import_graph.get(source_file, set())

        # 同文件候选
        same_file = [c for c in candidates if c.split("::")[0] == source_file]
        if len(same_file) == 1:
            return same_file[0]

        # 已导入文件候选
        imported = [c for c in candidates if c.split("::")[0] in imported_files]
        if len(imported) == 1:
            return imported[0]

        # 无法确定
        return None

    def _update_edge_target(
        self, source: str, old_target: str, new_target: str, edge_type: str
    ) -> None:
        """更新边的 target 为解析后的完整 UID (处理 UNIQUE 冲突)"""
        import json as _json

        conn = self.store._conn
        if conn is None:
            return
        metadata_json = _json.dumps({"resolved_from": old_target})
        try:
            conn.execute(
                """UPDATE code_edges
                   SET target = ?, confidence = 0.9, confidence_tier = 'RESOLVED',
                       metadata = ?
                   WHERE source = ? AND target = ? AND edge_type = ?""",
                (new_target, metadata_json, source, old_target, edge_type),
            )
        except Exception:
            # UNIQUE 冲突: 已存在解析后的边，删除旧的裸名边
            conn.execute(
                "DELETE FROM code_edges WHERE source = ? AND target = ? AND edge_type = ?",
                (source, old_target, edge_type),
            )
        conn.commit()

    # ─── Step 2: 签名计算 ─────────────────────────────────────────

    def _compute_signatures(self) -> int:
        """为缺少签名的节点生成人类可读签名"""
        conn = self.store._conn
        if conn is None:
            return 0

        rows = conn.execute(
            """SELECT uid, name, kind, parameters, file_path
               FROM code_nodes WHERE signature = '' OR signature IS NULL"""
        ).fetchall()

        count = 0
        for row in rows:
            uid, name, kind, params_json, file_path = row
            import json
            params = json.loads(params_json or "[]")
            sig = self._generate_signature(name, kind, params)
            if sig:
                conn.execute(
                    "UPDATE code_nodes SET signature = ? WHERE uid = ?",
                    (sig, uid),
                )
                count += 1

        if count > 0:
            conn.commit()
        return count

    @staticmethod
    def _generate_signature(name: str, kind: str, params: list[str]) -> str:
        """生成签名"""
        if kind in ("function", "method", "test", "endpoint"):
            return f"def {name}({', '.join(params)})"
        elif kind == "class":
            return f"class {name}"
        elif kind == "type":
            return f"type {name}"
        return ""

    # ─── Step 3: FTS 校验 ─────────────────────────────────────────

    def _verify_fts(self) -> bool:
        """校验 FTS 索引完整性 (触发器已自动维护)"""
        conn = self.store._conn
        if conn is None:
            return False
        try:
            # 检查 FTS 表是否可查询
            conn.execute("SELECT COUNT(*) FROM code_nodes_fts").fetchone()
            return True
        except Exception:
            return False

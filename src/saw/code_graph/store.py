"""Code Graph SQLite 存储层 — WAL 模式、FTS5、原子文件替换"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from saw.code_graph.models import (
    CodeNode,
    CodeEdge,
    EdgeType,
    NodeKind,
    ConfidenceTier,
    FileTracking,
    GraphSnapshot,
    ParseResult,
)

logger = logging.getLogger(__name__)

_SCHEMA_SQL = """
-- 节点表
CREATE TABLE IF NOT EXISTS code_nodes (
    uid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    file_path TEXT NOT NULL,
    language TEXT NOT NULL,
    start_line INTEGER DEFAULT 0,
    end_line INTEGER DEFAULT 0,
    signature TEXT DEFAULT '',
    parameters TEXT DEFAULT '[]',
    docstring TEXT,
    content_hash TEXT NOT NULL DEFAULT '',
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 边表
CREATE TABLE IF NOT EXISTS code_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    confidence_tier TEXT DEFAULT 'EXTRACTED',
    metadata TEXT DEFAULT '{}',
    UNIQUE(source, target, edge_type)
);

-- 文件追踪表（增量更新用）
CREATE TABLE IF NOT EXISTS file_tracking (
    file_path TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL,
    last_parsed_at TEXT DEFAULT '',
    node_count INTEGER DEFAULT 0,
    edge_count INTEGER DEFAULT 0
);

-- 图快照元数据
CREATE TABLE IF NOT EXISTS graph_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    trigger TEXT NOT NULL,
    node_count INTEGER DEFAULT 0,
    edge_count INTEGER DEFAULT 0,
    files_changed INTEGER DEFAULT 0
);

-- FTS5 全文索引
CREATE VIRTUAL TABLE IF NOT EXISTS code_nodes_fts USING fts5(
    name, signature, file_path,
    content='code_nodes',
    content_rowid='rowid',
    tokenize='porter unicode61'
);

-- FTS5 同步触发器
CREATE TRIGGER IF NOT EXISTS code_nodes_ai AFTER INSERT ON code_nodes BEGIN
    INSERT INTO code_nodes_fts(rowid, name, signature, file_path)
    VALUES (new.rowid, new.name, new.signature, new.file_path);
END;

CREATE TRIGGER IF NOT EXISTS code_nodes_ad AFTER DELETE ON code_nodes BEGIN
    INSERT INTO code_nodes_fts(code_nodes_fts, rowid, name, signature, file_path)
    VALUES ('delete', old.rowid, old.name, old.signature, old.file_path);
END;

CREATE TRIGGER IF NOT EXISTS code_nodes_au AFTER UPDATE ON code_nodes BEGIN
    INSERT INTO code_nodes_fts(code_nodes_fts, rowid, name, signature, file_path)
    VALUES ('delete', old.rowid, old.name, old.signature, old.file_path);
    INSERT INTO code_nodes_fts(rowid, name, signature, file_path)
    VALUES (new.rowid, new.name, new.signature, new.file_path);
END;

-- 索引
CREATE INDEX IF NOT EXISTS idx_edges_source ON code_edges(source, edge_type);
CREATE INDEX IF NOT EXISTS idx_edges_target ON code_edges(target, edge_type);
CREATE INDEX IF NOT EXISTS idx_nodes_file ON code_nodes(file_path);
CREATE INDEX IF NOT EXISTS idx_nodes_kind ON code_nodes(kind);
CREATE INDEX IF NOT EXISTS idx_nodes_name ON code_nodes(name);
CREATE INDEX IF NOT EXISTS idx_file_tracking_hash ON file_tracking(content_hash);
"""


class CodeGraphStore:
    """SQLite-backed 代码图存储

    特性:
    - WAL 模式: 读写并发安全
    - FTS5: 全文搜索 (porter stemmer + unicode61)
    - 原子文件替换: 单事务替换一个文件的所有 nodes/edges
    - 快照版本化: 可回滚到任意历史图状态
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
        self._initialize()

    def _initialize(self) -> None:
        """初始化数据库连接和 schema"""
        self._conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=30.0,
        )
        self._conn.row_factory = sqlite3.Row
        # WAL 模式: 读写并发
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.executescript(_SCHEMA_SQL)
        self._conn.commit()

    @contextmanager
    def _transaction(self):
        """事务上下文管理器 (线程安全)"""
        assert self._conn is not None
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise

    # ─── Node CRUD ───────────────────────────────────────────────

    def upsert_node(self, node: CodeNode) -> None:
        """插入或更新单个节点"""
        assert self._conn is not None
        with self._lock:
            self._conn.execute(
                """INSERT INTO code_nodes
                   (uid, name, kind, file_path, language, start_line, end_line,
                    signature, parameters, docstring, content_hash, metadata,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(uid) DO UPDATE SET
                     name=excluded.name, kind=excluded.kind,
                     start_line=excluded.start_line, end_line=excluded.end_line,
                     signature=excluded.signature, parameters=excluded.parameters,
                     docstring=excluded.docstring, content_hash=excluded.content_hash,
                     metadata=excluded.metadata, updated_at=excluded.updated_at
                """,
                (
                    node.uid, node.name, node.kind.value, node.file_path,
                    node.language, node.start_line, node.end_line,
                    node.signature, json.dumps(node.parameters),
                    node.docstring, node.content_hash, json.dumps(node.metadata),
                    node.created_at, node.updated_at,
                ),
            )
            self._conn.commit()

    def get_node(self, uid: str) -> Optional[CodeNode]:
        """按 UID 获取节点"""
        assert self._conn is not None
        row = self._conn.execute(
            "SELECT * FROM code_nodes WHERE uid = ?", (uid,)
        ).fetchone()
        return self._row_to_node(row) if row else None

    def find_nodes_by_name(self, name: str) -> list[CodeNode]:
        """按名称查找节点"""
        assert self._conn is not None
        rows = self._conn.execute(
            "SELECT * FROM code_nodes WHERE name = ?", (name,)
        ).fetchall()
        return [self._row_to_node(r) for r in rows]

    def get_nodes_by_file(self, file_path: str) -> list[CodeNode]:
        """获取文件的所有节点"""
        assert self._conn is not None
        rows = self._conn.execute(
            "SELECT * FROM code_nodes WHERE file_path = ?", (file_path,)
        ).fetchall()
        return [self._row_to_node(r) for r in rows]

    def get_all_nodes(self) -> list[CodeNode]:
        """获取所有节点"""
        assert self._conn is not None
        rows = self._conn.execute("SELECT * FROM code_nodes").fetchall()
        return [self._row_to_node(r) for r in rows]

    def search_nodes_fts(self, query: str, limit: int = 20) -> list[CodeNode]:
        """FTS5 全文搜索 (安全处理特殊字符)"""
        assert self._conn is not None
        limit = max(1, min(limit, 1000))
        # 转义 FTS5 语法字符，防止 OperationalError
        safe_query = '"' + query.replace('"', '""') + '"'
        try:
            rows = self._conn.execute(
                """SELECT cn.* FROM code_nodes cn
                   JOIN code_nodes_fts fts ON cn.rowid = fts.rowid
                   WHERE code_nodes_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (safe_query, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            # FTS 语法错误降级为 LIKE 查询
            rows = self._conn.execute(
                "SELECT * FROM code_nodes WHERE name LIKE ? OR signature LIKE ? LIMIT ?",
                (f"%{query}%", f"%{query}%", limit),
            ).fetchall()
        return [self._row_to_node(r) for r in rows]

    # ─── Edge CRUD ───────────────────────────────────────────────

    def upsert_edge(self, edge: CodeEdge) -> None:
        """插入或更新单条边"""
        assert self._conn is not None
        with self._lock:
            self._conn.execute(
                """INSERT INTO code_edges
                   (source, target, edge_type, confidence, confidence_tier, metadata)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(source, target, edge_type) DO UPDATE SET
                     confidence=excluded.confidence,
                     confidence_tier=excluded.confidence_tier,
                     metadata=excluded.metadata
                """,
                (
                    edge.source, edge.target, edge.edge_type.value,
                    edge.confidence, edge.confidence_tier.value,
                    json.dumps(edge.metadata),
                ),
            )
            self._conn.commit()

    def get_outgoing_edges(
        self, uid: str, edge_types: Optional[list[str]] = None
    ) -> list[CodeEdge]:
        """获取节点的出边"""
        assert self._conn is not None
        if edge_types:
            placeholders = ",".join("?" * len(edge_types))
            rows = self._conn.execute(
                f"SELECT * FROM code_edges WHERE source = ? AND edge_type IN ({placeholders})",
                [uid] + edge_types,
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM code_edges WHERE source = ?", (uid,)
            ).fetchall()
        return [self._row_to_edge(r) for r in rows]

    def get_incoming_edges(
        self, uid: str, edge_types: Optional[list[str]] = None
    ) -> list[CodeEdge]:
        """获取节点的入边"""
        assert self._conn is not None
        if edge_types:
            placeholders = ",".join("?" * len(edge_types))
            rows = self._conn.execute(
                f"SELECT * FROM code_edges WHERE target = ? AND edge_type IN ({placeholders})",
                [uid] + edge_types,
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM code_edges WHERE target = ?", (uid,)
            ).fetchall()
        return [self._row_to_edge(r) for r in rows]

    # ─── 原子文件替换 ─────────────────────────────────────────────

    def store_file_batch(self, result: ParseResult) -> None:
        """原子替换一个文件的所有 nodes/edges

        单事务内: 删除旧数据 → 插入新数据 → 更新 file_tracking
        """
        with self._transaction() as conn:
            # 删除该文件的旧节点和边
            old_uids = [
                r[0]
                for r in conn.execute(
                    "SELECT uid FROM code_nodes WHERE file_path = ?",
                    (result.file_path,),
                ).fetchall()
            ]
            if old_uids:
                placeholders = ",".join("?" * len(old_uids))
                # 仅删除本文件拥有的边 (source 属于本文件)
                # 不删除其他文件指向本文件的入边，避免跨文件边丢失
                conn.execute(
                    f"DELETE FROM code_edges WHERE source IN ({placeholders})",
                    old_uids,
                )
                conn.execute(
                    f"DELETE FROM code_nodes WHERE uid IN ({placeholders})",
                    old_uids,
                )

            # 插入新节点
            for node in result.nodes:
                conn.execute(
                    """INSERT INTO code_nodes
                       (uid, name, kind, file_path, language, start_line, end_line,
                        signature, parameters, docstring, content_hash, metadata,
                        created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(uid) DO UPDATE SET
                         name=excluded.name, kind=excluded.kind,
                         start_line=excluded.start_line, end_line=excluded.end_line,
                         signature=excluded.signature, parameters=excluded.parameters,
                         docstring=excluded.docstring, content_hash=excluded.content_hash,
                         metadata=excluded.metadata, updated_at=excluded.updated_at
                    """,
                    (
                        node.uid, node.name, node.kind.value, node.file_path,
                        node.language, node.start_line, node.end_line,
                        node.signature, json.dumps(node.parameters),
                        node.docstring, node.content_hash, json.dumps(node.metadata),
                        node.created_at, node.updated_at,
                    ),
                )

            # 插入新边
            for edge in result.edges:
                conn.execute(
                    """INSERT INTO code_edges
                       (source, target, edge_type, confidence, confidence_tier, metadata)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT(source, target, edge_type) DO UPDATE SET
                         confidence=excluded.confidence,
                         confidence_tier=excluded.confidence_tier,
                         metadata=excluded.metadata
                    """,
                    (
                        edge.source, edge.target, edge.edge_type.value,
                        edge.confidence, edge.confidence_tier.value,
                        json.dumps(edge.metadata),
                    ),
                )

            # 更新 file_tracking
            now = datetime.now(timezone.utc).isoformat()
            file_hash = result.nodes[0].content_hash if result.nodes else ""
            conn.execute(
                """INSERT INTO file_tracking (file_path, content_hash, last_parsed_at, node_count, edge_count)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(file_path) DO UPDATE SET
                     content_hash=excluded.content_hash,
                     last_parsed_at=excluded.last_parsed_at,
                     node_count=excluded.node_count,
                     edge_count=excluded.edge_count
                """,
                (result.file_path, file_hash, now, len(result.nodes), len(result.edges)),
            )

    # ─── 文件追踪 ─────────────────────────────────────────────────

    def get_file_hash(self, file_path: str) -> Optional[str]:
        """获取文件的已记录 hash"""
        assert self._conn is not None
        row = self._conn.execute(
            "SELECT content_hash FROM file_tracking WHERE file_path = ?",
            (file_path,),
        ).fetchone()
        return row[0] if row else None

    def get_tracked_files(self) -> list[FileTracking]:
        """获取所有已追踪文件"""
        assert self._conn is not None
        rows = self._conn.execute("SELECT * FROM file_tracking").fetchall()
        return [
            FileTracking(
                file_path=r["file_path"],
                content_hash=r["content_hash"],
                last_parsed_at=r["last_parsed_at"],
                node_count=r["node_count"],
                edge_count=r["edge_count"],
            )
            for r in rows
        ]

    def remove_file(self, file_path: str) -> None:
        """删除文件的所有图数据"""
        with self._transaction() as conn:
            uids = [
                r[0]
                for r in conn.execute(
                    "SELECT uid FROM code_nodes WHERE file_path = ?", (file_path,)
                ).fetchall()
            ]
            if uids:
                placeholders = ",".join("?" * len(uids))
                conn.execute(
                    f"DELETE FROM code_edges WHERE source IN ({placeholders}) OR target IN ({placeholders})",
                    uids + uids,
                )
                conn.execute(
                    f"DELETE FROM code_nodes WHERE uid IN ({placeholders})", uids
                )
            conn.execute("DELETE FROM file_tracking WHERE file_path = ?", (file_path,))

    # ─── 快照 ─────────────────────────────────────────────────────

    def create_snapshot(self, trigger: str, files_changed: int = 0) -> GraphSnapshot:
        """创建图快照"""
        assert self._conn is not None
        snapshot = GraphSnapshot(
            snapshot_id=str(uuid.uuid4())[:8],
            created_at=datetime.now(timezone.utc).isoformat(),
            trigger=trigger,
            node_count=self.node_count(),
            edge_count=self.edge_count(),
            files_changed=files_changed,
        )
        self._conn.execute(
            """INSERT INTO graph_snapshots
               (snapshot_id, created_at, trigger, node_count, edge_count, files_changed)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                snapshot.snapshot_id, snapshot.created_at, snapshot.trigger,
                snapshot.node_count, snapshot.edge_count, snapshot.files_changed,
            ),
        )
        self._conn.commit()
        return snapshot

    # ─── 统计与健康 ───────────────────────────────────────────────

    def node_count(self) -> int:
        """节点总数"""
        assert self._conn is not None
        return self._conn.execute("SELECT COUNT(*) FROM code_nodes").fetchone()[0]

    def edge_count(self) -> int:
        """边总数"""
        assert self._conn is not None
        return self._conn.execute("SELECT COUNT(*) FROM code_edges").fetchone()[0]

    def file_count(self) -> int:
        """已追踪文件数"""
        assert self._conn is not None
        return self._conn.execute("SELECT COUNT(*) FROM file_tracking").fetchone()[0]

    def health_check(self) -> dict:
        """健康检查报告"""
        assert self._conn is not None
        orphan_edges = self._conn.execute(
            """SELECT COUNT(*) FROM code_edges e
               WHERE NOT EXISTS (SELECT 1 FROM code_nodes n WHERE n.uid = e.source)
                  OR NOT EXISTS (SELECT 1 FROM code_nodes n WHERE n.uid = e.target)"""
        ).fetchone()[0]

        return {
            "status": "healthy" if orphan_edges == 0 else "degraded",
            "node_count": self.node_count(),
            "edge_count": self.edge_count(),
            "file_count": self.file_count(),
            "orphan_edges": orphan_edges,
            "db_size_bytes": self.db_path.stat().st_size if self.db_path.exists() else 0,
        }

    # ─── 兼容接口（供现有 analysis 模块使用）─────────────────────────

    def as_knowledge_graph(self) -> "CodeGraphStore":
        """返回自身（已实现 KnowledgeGraph 接口）"""
        return self

    # ─── 内部工具 ─────────────────────────────────────────────────

    @staticmethod
    def _row_to_node(row: sqlite3.Row) -> CodeNode:
        """数据库行 → CodeNode"""
        return CodeNode(
            uid=row["uid"],
            name=row["name"],
            kind=NodeKind(row["kind"]),
            file_path=row["file_path"],
            language=row["language"],
            start_line=row["start_line"],
            end_line=row["end_line"],
            signature=row["signature"],
            parameters=json.loads(row["parameters"] or "[]"),
            docstring=row["docstring"],
            content_hash=row["content_hash"],
            metadata=json.loads(row["metadata"] or "{}"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_edge(row: sqlite3.Row) -> CodeEdge:
        """数据库行 → CodeEdge"""
        return CodeEdge(
            source=row["source"],
            target=row["target"],
            edge_type=EdgeType(row["edge_type"]),
            confidence=row["confidence"],
            confidence_tier=ConfidenceTier(row["confidence_tier"]),
            metadata=json.loads(row["metadata"] or "{}"),
        )

    def close(self) -> None:
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "CodeGraphStore":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def __del__(self):
        self.close()

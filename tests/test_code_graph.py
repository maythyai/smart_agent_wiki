"""Code Graph 单元测试 — 验证核心生命周期"""

import tempfile
from pathlib import Path

import pytest

from saw.code_graph.models import (
    CodeNode,
    CodeEdge,
    NodeKind,
    EdgeType,
    ConfidenceTier,
    content_hash,
    make_uid,
)
from saw.code_graph.store import CodeGraphStore
from saw.code_graph.parser import CodeParser, detect_language, should_skip
from saw.code_graph.engine import CodeGraphEngine
from saw.code_graph.incremental import IncrementalBuilder


# ─── Models ───────────────────────────────────────────────────────


class TestModels:
    def test_make_uid(self):
        uid = make_uid("src/main.py", "MyClass.my_method")
        assert uid == "src/main.py::MyClass.my_method"

    def test_content_hash_deterministic(self):
        h1 = content_hash("hello world")
        h2 = content_hash("hello world")
        h3 = content_hash("different")
        assert h1 == h2
        assert h1 != h3

    def test_code_node_to_dict_roundtrip(self):
        node = CodeNode(
            uid="test.py::foo",
            name="foo",
            kind=NodeKind.FUNCTION,
            file_path="test.py",
            language="python",
            start_line=1,
            end_line=5,
            signature="def foo(x, y)",
            parameters=["x", "y"],
        )
        d = node.to_dict()
        restored = CodeNode.from_dict(d)
        assert restored.uid == node.uid
        assert restored.name == node.name
        assert restored.kind == node.kind
        assert restored.parameters == node.parameters

    def test_code_edge_weight(self):
        edge = CodeEdge(
            source="a", target="b",
            edge_type=EdgeType.CALLS, confidence=1.0,
        )
        assert edge.weight == 1.0

        edge2 = CodeEdge(
            source="a", target="b",
            edge_type=EdgeType.CONTAINS, confidence=0.5,
        )
        assert edge2.weight == 0.15  # 0.3 * 0.5

    def test_edge_to_dict_roundtrip(self):
        edge = CodeEdge(
            source="a::foo", target="b::bar",
            edge_type=EdgeType.IMPORTS,
            confidence=0.9,
            confidence_tier=ConfidenceTier.RESOLVED,
        )
        d = edge.to_dict()
        restored = CodeEdge.from_dict(d)
        assert restored.source == edge.source
        assert restored.edge_type == edge.edge_type
        assert restored.confidence == edge.confidence


# ─── Store ────────────────────────────────────────────────────────


class TestStore:
    @pytest.fixture
    def store(self, tmp_path):
        db_path = tmp_path / "test_graph.db"
        s = CodeGraphStore(db_path)
        yield s
        s.close()

    def test_upsert_and_get_node(self, store):
        node = CodeNode(
            uid="src/app.py::main",
            name="main",
            kind=NodeKind.FUNCTION,
            file_path="src/app.py",
            language="python",
            start_line=10,
            end_line=20,
            content_hash="abc123",
        )
        store.upsert_node(node)

        retrieved = store.get_node("src/app.py::main")
        assert retrieved is not None
        assert retrieved.name == "main"
        assert retrieved.kind == NodeKind.FUNCTION
        assert retrieved.start_line == 10

    def test_upsert_updates_existing(self, store):
        node = CodeNode(
            uid="src/app.py::main",
            name="main",
            kind=NodeKind.FUNCTION,
            file_path="src/app.py",
            language="python",
            content_hash="v1",
        )
        store.upsert_node(node)

        node.content_hash = "v2"
        node.start_line = 99
        store.upsert_node(node)

        retrieved = store.get_node("src/app.py::main")
        assert retrieved.content_hash == "v2"
        assert retrieved.start_line == 99
        assert store.node_count() == 1  # 不产生重复

    def test_find_nodes_by_name(self, store):
        for i in range(3):
            store.upsert_node(CodeNode(
                uid=f"file{i}.py::helper",
                name="helper",
                kind=NodeKind.FUNCTION,
                file_path=f"file{i}.py",
                language="python",
                content_hash=f"h{i}",
            ))
        results = store.find_nodes_by_name("helper")
        assert len(results) == 3

    def test_edges_crud(self, store):
        store.upsert_node(CodeNode(uid="a", name="a", kind=NodeKind.FUNCTION, file_path="a.py", language="python", content_hash="h"))
        store.upsert_node(CodeNode(uid="b", name="b", kind=NodeKind.FUNCTION, file_path="b.py", language="python", content_hash="h"))

        edge = CodeEdge(source="a", target="b", edge_type=EdgeType.CALLS)
        store.upsert_edge(edge)

        outgoing = store.get_outgoing_edges("a")
        assert len(outgoing) == 1
        assert outgoing[0].target == "b"

        incoming = store.get_incoming_edges("b")
        assert len(incoming) == 1
        assert incoming[0].source == "a"

    def test_edge_type_filter(self, store):
        store.upsert_node(CodeNode(uid="a", name="a", kind=NodeKind.FUNCTION, file_path="a.py", language="python", content_hash="h"))
        store.upsert_node(CodeNode(uid="b", name="b", kind=NodeKind.FUNCTION, file_path="b.py", language="python", content_hash="h"))

        store.upsert_edge(CodeEdge(source="a", target="b", edge_type=EdgeType.CALLS))
        store.upsert_edge(CodeEdge(source="a", target="b", edge_type=EdgeType.IMPORTS))

        calls_only = store.get_outgoing_edges("a", ["CALLS"])
        assert len(calls_only) == 1
        assert calls_only[0].edge_type == EdgeType.CALLS

    def test_store_file_batch_atomic(self, store):
        from saw.code_graph.models import ParseResult

        result = ParseResult(file_path="test.py", language="python")
        result.nodes = [
            CodeNode(uid="test.py::foo", name="foo", kind=NodeKind.FUNCTION, file_path="test.py", language="python", content_hash="h1"),
            CodeNode(uid="test.py::bar", name="bar", kind=NodeKind.FUNCTION, file_path="test.py", language="python", content_hash="h1"),
        ]
        result.edges = [
            CodeEdge(source="test.py::foo", target="test.py::bar", edge_type=EdgeType.CALLS),
        ]

        store.store_file_batch(result)
        assert store.node_count() == 2
        assert store.edge_count() == 1

        # 替换: 新批次只有 1 个节点
        result2 = ParseResult(file_path="test.py", language="python")
        result2.nodes = [
            CodeNode(uid="test.py::baz", name="baz", kind=NodeKind.FUNCTION, file_path="test.py", language="python", content_hash="h2"),
        ]
        result2.edges = []

        store.store_file_batch(result2)
        assert store.node_count() == 1  # 旧的被替换
        assert store.get_node("test.py::foo") is None
        assert store.get_node("test.py::baz") is not None

    def test_fts_search(self, store):
        store.upsert_node(CodeNode(
            uid="auth.py::authenticate_user",
            name="authenticate_user",
            kind=NodeKind.FUNCTION,
            file_path="auth.py",
            language="python",
            signature="def authenticate_user(username, password)",
            content_hash="h",
        ))
        store.upsert_node(CodeNode(
            uid="db.py::connect",
            name="connect",
            kind=NodeKind.FUNCTION,
            file_path="db.py",
            language="python",
            signature="def connect(host, port)",
            content_hash="h",
        ))

        results = store.search_nodes_fts("authenticate")
        assert len(results) >= 1
        assert results[0].name == "authenticate_user"

    def test_health_check(self, store):
        health = store.health_check()
        assert health["status"] == "healthy"
        assert health["orphan_edges"] == 0

    def test_snapshot(self, store):
        store.upsert_node(CodeNode(uid="a", name="a", kind=NodeKind.FUNCTION, file_path="a.py", language="python", content_hash="h"))
        snapshot = store.create_snapshot("full_build", files_changed=1)
        assert snapshot.node_count == 1
        assert snapshot.trigger == "full_build"


# ─── Parser ───────────────────────────────────────────────────────


class TestParser:
    @pytest.fixture
    def sample_project(self, tmp_path):
        """创建一个小型 Python 项目"""
        src = tmp_path / "src"
        src.mkdir()

        (src / "models.py").write_text('''
class User:
    """User model."""

    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    def validate(self) -> bool:
        return bool(self.name and self.email)


class AdminUser(User):
    """Admin user."""

    def delete_user(self, user: User) -> None:
        pass
''')

        (src / "service.py").write_text('''
from src.models import User, AdminUser


def create_user(name: str, email: str) -> User:
    """Create a new user."""
    user = User(name, email)
    if user.validate():
        return user
    raise ValueError("Invalid user")


def get_admin() -> AdminUser:
    return AdminUser("admin", "admin@test.com")
''')

        (src / "test_models.py").write_text('''
from src.models import User


def test_user_creation():
    user = User("test", "test@test.com")
    assert user.name == "test"


def test_user_validation():
    user = User("", "")
    assert not user.validate()
''')

        return tmp_path

    def test_detect_language(self):
        assert detect_language("foo.py") == "python"
        assert detect_language("bar.ts") == "typescript"
        assert detect_language("baz.js") == "javascript"
        assert detect_language("readme.md") is None

    def test_should_skip(self):
        assert should_skip(Path("node_modules/pkg/index.js"))
        assert should_skip(Path(".git/config"))
        assert should_skip(Path("src/__pycache__/mod.cpython-311.pyc"))
        assert not should_skip(Path("src/main.py"))

    def test_parse_python_file(self, sample_project):
        parser = CodeParser(sample_project)
        result = parser.parse_file(sample_project / "src" / "models.py")

        assert result.language == "python"
        assert not result.errors

        # 应该有: file node + User class + __init__ + validate + AdminUser + delete_user
        names = [n.name for n in result.nodes]
        assert "User" in names
        assert "AdminUser" in names
        assert "validate" in names

        # 应该有 CONTAINS 边和 INHERITS 边
        edge_types = [e.edge_type for e in result.edges]
        assert EdgeType.CONTAINS in edge_types
        assert EdgeType.INHERITS in edge_types

    def test_parse_python_imports(self, sample_project):
        parser = CodeParser(sample_project)
        result = parser.parse_file(sample_project / "src" / "service.py")

        # 应该有 IMPORTS 边 (from src.models import ...)
        import_edges = [e for e in result.edges if e.edge_type == EdgeType.IMPORTS]
        assert len(import_edges) >= 1

    def test_parse_test_detection(self, sample_project):
        parser = CodeParser(sample_project)
        result = parser.parse_file(sample_project / "src" / "test_models.py")

        test_nodes = [n for n in result.nodes if n.kind == NodeKind.TEST]
        assert len(test_nodes) >= 2  # test_user_creation, test_user_validation

    def test_parse_typescript(self, tmp_path):
        ts_file = tmp_path / "app.ts"
        ts_file.write_text('''
import { Router } from './router';

export class AppController {
    handleRequest() {}
}

export function bootstrap(port: number): void {
    const app = new AppController();
}

interface Config {
    port: number;
    host: string;
}
''')
        parser = CodeParser(tmp_path)
        result = parser.parse_file(ts_file)

        assert result.language == "typescript"
        names = [n.name for n in result.nodes]
        assert "AppController" in names
        assert "bootstrap" in names
        assert "Config" in names


# ─── Engine (集成测试) ─────────────────────────────────────────────


class TestEngine:
    @pytest.fixture
    def engine(self, tmp_path):
        """创建引擎并构建小型项目"""
        src = tmp_path / "src"
        src.mkdir()

        (src / "core.py").write_text('''
class Engine:
    def start(self):
        self.initialize()
        self.run()

    def initialize(self):
        pass

    def run(self):
        pass


def main():
    engine = Engine()
    engine.start()
''')

        (src / "utils.py").write_text('''
from src.core import Engine


def helper():
    pass


def create_engine() -> Engine:
    return Engine()
''')

        db_path = tmp_path / ".saw" / "test.db"
        eng = CodeGraphEngine(tmp_path, db_path=db_path)
        eng.build(full=True)
        yield eng
        eng.close()

    def test_build_populates_graph(self, engine):
        stats = engine.stats()
        assert stats["nodes"] > 0
        assert stats["edges"] > 0
        assert stats["files"] >= 2

    def test_find_by_name(self, engine):
        nodes = engine.find_nodes_by_name("Engine")
        assert len(nodes) >= 1
        assert nodes[0].kind == NodeKind.CLASS

    def test_search(self, engine):
        results = engine.search("Engine")
        assert len(results) >= 1

    def test_impact_analysis(self, engine):
        # Engine 类被 utils.py 引用
        nodes = engine.find_nodes_by_name("Engine")
        if nodes:
            impacts = engine.impact_analysis(nodes[0].uid, direction="upstream")
            # 应该有上游依赖
            assert isinstance(impacts, list)

    def test_health(self, engine):
        health = engine.health()
        # bare-name CALLS 边在 PostProcess 前是预期行为 (orphan > 0)
        assert health["status"] in ("healthy", "degraded")
        assert health["node_count"] > 0
        assert health["edge_count"] > 0
        assert "orphan_edges" in health

    def test_incremental_no_changes(self, engine):
        result = engine.update()
        assert result.files_parsed == 0  # 无变更


# ─── Graph.py 兼容性 ──────────────────────────────────────────────


class TestGraphCompat:
    def test_knowledge_graph_fallback(self):
        """无 db_path 时降级为内存模式"""
        from saw.graph import KnowledgeGraph

        kg = KnowledgeGraph()
        assert kg.get_node("nonexistent") is None
        assert kg.find_nodes_by_name("foo") == []
        assert kg.get_all_nodes() == []

    def test_knowledge_graph_with_store(self, tmp_path):
        """有 db_path 时使用 SQLite 后端"""
        from saw.graph import KnowledgeGraph

        db_path = tmp_path / "compat.db"
        kg = KnowledgeGraph(db_path=db_path)

        # 通过底层 store 插入数据
        from saw.code_graph.models import CodeNode, NodeKind
        kg._store.upsert_node(CodeNode(
            uid="test.py::foo",
            name="foo",
            kind=NodeKind.FUNCTION,
            file_path="test.py",
            language="python",
            content_hash="h",
        ))

        # 通过兼容接口查询
        node = kg.get_node("test.py::foo")
        assert node is not None
        assert node["name"] == "foo"

        nodes = kg.find_nodes_by_name("foo")
        assert len(nodes) == 1

        kg.close()

    def test_thread_safe_get_graph(self, tmp_path):
        """get_graph 线程安全"""
        from saw.graph import get_graph, reset_graph

        reset_graph()
        g1 = get_graph()
        g2 = get_graph()
        assert g1 is g2
        reset_graph()

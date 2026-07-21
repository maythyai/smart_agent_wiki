"""Sprint 4 测试 — Health / Python Resolver / CLI / Benchmarks"""

import time
import pytest
from pathlib import Path

from saw.code_graph.models import CodeNode, CodeEdge, NodeKind, EdgeType, ParseResult
from saw.code_graph.store import CodeGraphStore
from saw.code_graph.engine import CodeGraphEngine
from saw.code_graph.health import HealthMonitor, BuildMetrics
from saw.code_graph.snapshot import SnapshotManager
from saw.code_graph.resolvers.python_resolver import PythonResolver


# ─── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def sample_project(tmp_path):
    """创建一个有 FastAPI 风格的项目"""
    src = tmp_path / "src"
    src.mkdir()

    (src / "main.py").write_text('''
from src.routes import router


def create_app():
    """Create application."""
    app = setup_middleware()
    app.include_router(router)
    return app


def setup_middleware():
    return {"middleware": True}


def main():
    app = create_app()
    run_server(app)


def run_server(app):
    pass
''')

    (src / "routes.py").write_text('''
from src.services import get_user, create_user


def get_user_endpoint(user_id: int):
    """Get user by ID."""
    return get_user(user_id)


def create_user_endpoint(name: str, email: str):
    """Create a new user."""
    return create_user(name, email)


def health_check():
    return {"status": "ok"}
''')

    (src / "services.py").write_text('''
from src.db import query, insert


def get_user(user_id: int):
    """Get user from database."""
    return query("users", user_id)


def create_user(name: str, email: str):
    """Create user in database."""
    validate_email(email)
    return insert("users", {"name": name, "email": email})


def validate_email(email: str) -> bool:
    """Validate email format."""
    return "@" in email
''')

    (src / "db.py").write_text('''
def query(table: str, id: int):
    """Query database."""
    return {"id": id, "table": table}


def insert(table: str, data: dict):
    """Insert into database."""
    return {"inserted": True}


def connect(host: str, port: int):
    """Connect to database."""
    return {"connected": True}
''')

    return tmp_path


@pytest.fixture
def engine(sample_project):
    db_path = sample_project / ".saw" / "test.db"
    eng = CodeGraphEngine(sample_project, db_path=db_path)
    eng.build(full=True, postprocess=True)
    yield eng
    eng.close()


# ─── Health Monitor ───────────────────────────────────────────────


class TestHealthMonitor:
    def test_healthy_graph(self, engine):
        """正常图应报告 healthy"""
        monitor = HealthMonitor(engine.store)
        report = monitor.check_health()
        assert report.status in ("healthy", "degraded")
        assert report.metrics["nodes"] > 0
        assert report.checks["empty_graph"] == "PASS"

    def test_empty_graph_alert(self, tmp_path):
        """空图应报告 critical"""
        db_path = tmp_path / "empty.db"
        store = CodeGraphStore(db_path)
        monitor = HealthMonitor(store)
        report = monitor.check_health()
        assert report.status == "critical"
        assert report.checks["empty_graph"] == "FAIL"
        assert any("empty" in a.lower() for a in report.alerts)
        store.close()

    def test_build_metrics_recording(self, engine):
        """构建指标记录"""
        monitor = HealthMonitor(engine.store)
        monitor.record_build(BuildMetrics(
            trigger="test",
            files_parsed=10,
            files_failed=1,
            duration_ms=500,
            error_rate=0.1,
        ))
        stats = monitor.get_build_stats()
        assert stats["count"] == 1
        assert stats["avg_duration_ms"] == 500

    def test_query_metrics_recording(self, engine):
        """查询指标记录"""
        from saw.code_graph.health import QueryMetrics
        monitor = HealthMonitor(engine.store)
        monitor.record_query(QueryMetrics(
            query_type="search",
            target="test",
            results_count=5,
            duration_ms=10,
        ))
        stats = monitor.get_query_stats()
        assert stats["count"] == 1

    def test_change_log(self, engine):
        """变更日志"""
        monitor = HealthMonitor(engine.store)
        log = monitor.change_log()
        assert len(log) >= 1  # build 时创建了快照
        assert log[0]["trigger"] == "full_build"


# ─── Python Resolver ──────────────────────────────────────────────


class TestPythonResolver:
    def test_endpoint_detection(self):
        """路由装饰器 → ENDPOINT"""
        resolver = PythonResolver()

        result = ParseResult(file_path="app.py", language="python")
        result.nodes = [
            CodeNode(
                uid="app.py::get_users",
                name="get_users",
                kind=NodeKind.FUNCTION,
                file_path="app.py",
                language="python",
                content_hash="h",
                metadata={"decorators": ["app.get('/users')]"]},
            ),
            CodeNode(
                uid="app.py::helper",
                name="helper",
                kind=NodeKind.FUNCTION,
                file_path="app.py",
                language="python",
                content_hash="h",
                metadata={"decorators": []},
            ),
        ]

        resolved = resolver.resolve(result, {})
        endpoint_nodes = [n for n in resolved.nodes if n.kind == NodeKind.ENDPOINT]
        assert len(endpoint_nodes) == 1
        assert endpoint_nodes[0].name == "get_users"
        assert endpoint_nodes[0].metadata.get("http_method") == "GET"

    def test_depends_resolution(self):
        """Depends() → DEPENDS_ON"""
        resolver = PythonResolver()

        result = ParseResult(file_path="app.py", language="python")
        result.edges = [
            CodeEdge(
                source="app.py::endpoint",
                target="get_db",
                edge_type=EdgeType.CALLS,
                metadata={"bare_name": True},
            ),
        ]

        # 模拟 Depends 调用
        result.edges[0].target = "Depends"
        resolved = resolver.resolve(result, {})
        # Depends 应被标记为 DEPENDS_ON (因为 "depend" in "Depends".lower())
        assert resolved.edges[0].edge_type == EdgeType.DEPENDS_ON

    def test_language_property(self):
        resolver = PythonResolver()
        assert resolver.language == "python"


# ─── Performance Benchmarks ───────────────────────────────────────


class TestBenchmarks:
    def test_query_latency(self, engine):
        """查询延迟 < 100ms"""
        # FTS 搜索
        start = time.time()
        for _ in range(10):
            engine.search("user")
        avg_ms = (time.time() - start) / 10 * 1000
        assert avg_ms < 100, f"Search avg {avg_ms:.1f}ms exceeds 100ms"

    def test_impact_latency(self, engine):
        """影响分析延迟 < 100ms"""
        nodes = engine.find_nodes_by_name("get_user")
        if nodes:
            start = time.time()
            for _ in range(10):
                engine.impact_analysis(nodes[0].uid)
            avg_ms = (time.time() - start) / 10 * 1000
            assert avg_ms < 100, f"Impact avg {avg_ms:.1f}ms exceeds 100ms"

    def test_incremental_speed(self, sample_project):
        """增量更新 (无变更) < 2s"""
        db_path = sample_project / ".saw" / "bench.db"
        eng = CodeGraphEngine(sample_project, db_path=db_path)
        eng.build(full=True, postprocess=False)

        start = time.time()
        result = eng.update()
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 2000, f"Incremental took {elapsed_ms:.0f}ms (> 2s)"
        assert result.files_parsed == 0  # 无变更
        eng.close()

    def test_full_build_speed(self, sample_project):
        """全量构建 (小项目) < 5s"""
        db_path = sample_project / ".saw" / "bench2.db"
        eng = CodeGraphEngine(sample_project, db_path=db_path)

        start = time.time()
        result = eng.build(full=True, postprocess=True)
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 5000, f"Full build took {elapsed_ms:.0f}ms (> 5s)"
        assert result.total_nodes > 0
        eng.close()


# ─── CLI (unit test via direct function calls) ────────────────────


class TestCLI:
    def test_cli_module_imports(self):
        """CLI 模块应可导入"""
        from saw.code_graph.cli import register_code_graph_commands
        assert callable(register_code_graph_commands)

    def test_health_monitor_integration(self, engine):
        """Health monitor 完整流程"""
        monitor = HealthMonitor(engine.store)

        # 记录一些指标
        monitor.record_build(BuildMetrics(
            trigger="full_build", files_parsed=4, duration_ms=150, error_rate=0.0,
        ))

        # 健康检查
        report = monitor.check_health()
        assert report.status in ("healthy", "degraded")

        # 统计
        build_stats = monitor.get_build_stats()
        assert build_stats["count"] == 1

        # 变更日志
        log = monitor.change_log()
        assert len(log) >= 1

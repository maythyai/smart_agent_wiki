"""Sprint 2 测试 — PostProcess / Flows / Communities / MCP Tools"""

import tempfile
from pathlib import Path

import pytest

from saw.code_graph.models import CodeNode, CodeEdge, NodeKind, EdgeType, ConfidenceTier
from saw.code_graph.store import CodeGraphStore
from saw.code_graph.engine import CodeGraphEngine
from saw.code_graph.postprocess import PostProcessor
from saw.code_graph.flows import FlowTracer
from saw.code_graph.communities import CommunityDetector


# ─── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def sample_project(tmp_path):
    """创建一个有调用链的小型项目"""
    src = tmp_path / "src"
    src.mkdir()

    (src / "app.py").write_text('''
from src.auth import authenticate
from src.db import connect


def main():
    """Application entry point."""
    conn = connect()
    user = authenticate("admin", "secret")
    handle_request(user, conn)


def handle_request(user, conn):
    """Process incoming request."""
    validate_permission(user)
    return {"status": "ok"}


def validate_permission(user):
    """Check user permissions."""
    return user is not None
''')

    (src / "auth.py").write_text('''
from src.db import query_user


def authenticate(username: str, password: str):
    """Authenticate a user."""
    user = query_user(username)
    if user and verify_password(user, password):
        return user
    return None


def verify_password(user, password: str) -> bool:
    """Verify password hash."""
    return password == "secret"
''')

    (src / "db.py").write_text('''
def connect():
    """Connect to database."""
    return {"host": "localhost"}


def query_user(username: str):
    """Query user from database."""
    return {"name": username, "role": "admin"}


def close_connection(conn):
    """Close database connection."""
    pass
''')

    (src / "test_auth.py").write_text('''
from src.auth import authenticate


def test_authenticate_success():
    user = authenticate("admin", "secret")
    assert user is not None


def test_authenticate_failure():
    user = authenticate("admin", "wrong")
    assert user is None
''')

    return tmp_path


@pytest.fixture
def engine(sample_project):
    """创建引擎并构建"""
    db_path = sample_project / ".saw" / "test.db"
    eng = CodeGraphEngine(sample_project, db_path=db_path)
    eng.build(full=True, postprocess=True)
    yield eng
    eng.close()


# ─── PostProcess ──────────────────────────────────────────────────


class TestPostProcess:
    def test_bare_name_resolution(self, engine):
        """裸名边应被解析为完整 UID"""
        # authenticate 在 app.py 中被调用，应解析到 auth.py::authenticate
        nodes = engine.find_nodes_by_name("authenticate")
        assert len(nodes) >= 1

        # 检查 CALLS 边是否已解析 (target 包含 "::")
        for node in nodes:
            incoming = engine.get_incoming_edges(node.uid, [EdgeType.CALLS])
            for edge in incoming:
                # 解析后的边 target 应该是完整 UID
                assert "::" in edge.target or "::" in edge.source

    def test_signatures_computed(self, engine):
        """节点应有签名"""
        nodes = engine.find_nodes_by_name("main")
        if nodes:
            assert nodes[0].signature != ""

    def test_postprocess_stats(self, engine):
        """PostProcess 应返回统计"""
        stats = engine.postprocess()
        assert "bare_names_resolved" in stats
        assert "time_ms" in stats
        assert stats["time_ms"] >= 0


# ─── Flows ────────────────────────────────────────────────────────


class TestFlows:
    def test_trace_flows(self, engine):
        """应检测到执行流"""
        flows = engine.trace_flows()
        assert len(flows) >= 1

        # main 应该是一个入口点
        entry_names = [f.entry_name for f in flows]
        assert "main" in entry_names

    def test_flow_has_path(self, engine):
        """执行流应有路径节点"""
        flows = engine.trace_flows()
        main_flows = [f for f in flows if f.entry_name == "main"]
        if main_flows:
            flow = main_flows[0]
            assert flow.length >= 1
            assert len(flow.nodes) >= 1

    def test_flow_criticality(self, engine):
        """涉及 auth 的流应有较高关键度"""
        flows = engine.trace_flows()
        # 至少有一个流有 criticality > 0
        assert any(f.criticality > 0 for f in flows)

    def test_security_detection(self, engine):
        """包含 authenticate/verify_password 的流应标记安全敏感"""
        flows = engine.trace_flows()
        security_flows = [f for f in flows if f.security_sensitive]
        # authenticate 和 verify_password 包含安全关键词
        assert len(security_flows) >= 1

    def test_affected_flows(self, engine):
        """变更检测应返回受影响的流"""
        # 找到 authenticate 的 UID
        nodes = engine.find_nodes_by_name("authenticate")
        if nodes:
            affected = engine.get_affected_flows([nodes[0].uid])
            # authenticate 在 main 的调用链中
            assert isinstance(affected, list)


# ─── Communities ──────────────────────────────────────────────────


class TestCommunities:
    def test_detect_communities(self, engine):
        """应检测到社区"""
        communities = engine.detect_communities()
        assert len(communities) >= 1

        # 每个社区应有成员
        for c in communities:
            assert c.size > 0
            assert len(c.members) > 0

    def test_community_names(self, engine):
        """社区应有生成的名称"""
        communities = engine.detect_communities()
        for c in communities:
            assert c.name != ""

    def test_architecture_overview(self, engine):
        """架构概览应包含完整信息"""
        overview = engine.architecture_overview()
        assert overview.total_nodes > 0
        assert overview.total_edges > 0
        assert len(overview.communities) >= 1

    def test_hub_nodes(self, engine):
        """应识别 hub 节点"""
        overview = engine.architecture_overview()
        # hub_nodes 可能为空（小项目），但不应报错
        assert isinstance(overview.hub_nodes, list)


# ─── MCP Tools ────────────────────────────────────────────────────


class TestMCPTools:
    @pytest.mark.asyncio
    async def test_code_search(self, engine):
        """saw_code_search 应返回结果"""
        from saw.code_graph.mcp_tools import handle_code_search

        result = await handle_code_search("authenticate", engine=engine)
        assert "error" not in result
        assert result["count"] >= 1
        assert any("authenticate" in r["name"] for r in result["results"])

    @pytest.mark.asyncio
    async def test_code_search_with_kind(self, engine):
        """按类型过滤搜索"""
        from saw.code_graph.mcp_tools import handle_code_search

        result = await handle_code_search("connect", kind="function", engine=engine)
        assert "error" not in result
        for r in result["results"]:
            assert r["kind"] == "function"

    @pytest.mark.asyncio
    async def test_code_query_callers(self, engine):
        """saw_code_query callers_of"""
        from saw.code_graph.mcp_tools import handle_code_query

        result = await handle_code_query("authenticate", "callers_of", engine=engine)
        assert "error" not in result
        assert result["pattern"] == "callers_of"

    @pytest.mark.asyncio
    async def test_code_query_callees(self, engine):
        """saw_code_query callees_of"""
        from saw.code_graph.mcp_tools import handle_code_query

        result = await handle_code_query("main", "callees_of", engine=engine)
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_code_query_not_found(self, engine):
        """查询不存在的符号应返回建议"""
        from saw.code_graph.mcp_tools import handle_code_query

        result = await handle_code_query("nonexistent_xyz", "callers_of", engine=engine)
        assert result.get("error") == "node_not_found"
        assert "suggestions" in result

    @pytest.mark.asyncio
    async def test_architecture_tool(self, engine):
        """saw_architecture 应返回概览"""
        from saw.code_graph.mcp_tools import handle_architecture

        result = await handle_architecture(engine=engine)
        assert "error" not in result
        assert result["total_nodes"] > 0
        assert "communities" in result

    @pytest.mark.asyncio
    async def test_flows_tool(self, engine):
        """saw_flows 应返回执行流"""
        from saw.code_graph.mcp_tools import handle_flows

        result = await handle_flows(engine=engine)
        assert "error" not in result
        assert result["count"] >= 1
        assert len(result["flows"]) >= 1

    @pytest.mark.asyncio
    async def test_engine_not_available(self):
        """无引擎时应返回错误"""
        from saw.code_graph.mcp_tools import handle_code_search

        result = await handle_code_search("test", engine=None)
        assert result["error"] == "engine_not_available"


# ─── Integration: Build + PostProcess + Query ─────────────────────


class TestIntegration:
    def test_full_lifecycle(self, sample_project):
        """完整生命周期: build → postprocess → query → flows → communities"""
        db_path = sample_project / ".saw" / "lifecycle.db"
        with CodeGraphEngine(sample_project, db_path=db_path) as eng:
            # Build
            result = eng.build(full=True, postprocess=True)
            assert result.files_parsed >= 4
            assert result.total_nodes > 0

            # Query
            nodes = eng.find_nodes_by_name("authenticate")
            assert len(nodes) >= 1

            # Impact
            if nodes:
                impacts = eng.impact_analysis(nodes[0].uid)
                assert isinstance(impacts, list)

            # Flows
            flows = eng.trace_flows()
            assert len(flows) >= 1

            # Communities
            communities = eng.detect_communities()
            assert len(communities) >= 1

            # Architecture
            overview = eng.architecture_overview()
            assert overview.total_nodes > 0

            # Health
            health = eng.health()
            assert health["node_count"] > 0

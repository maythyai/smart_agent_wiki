"""Sprint 3 测试 — Bridge / Snapshot / Context Tool / Govern"""

import pytest
from pathlib import Path

from saw.code_graph.models import CodeNode, CodeEdge, NodeKind, EdgeType
from saw.code_graph.store import CodeGraphStore
from saw.code_graph.engine import CodeGraphEngine
from saw.code_graph.bridge import BridgeLayer, StaleDoc
from saw.code_graph.snapshot import SnapshotManager
from saw.code_graph.govern import CodeGovernIntegration


# ─── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def sample_project(tmp_path):
    """创建一个小型项目"""
    src = tmp_path / "src"
    src.mkdir()

    (src / "auth.py").write_text('''
class AuthService:
    """Authentication service."""

    def login(self, username: str, password: str):
        """Login a user."""
        user = self.find_user(username)
        if user and self.verify(password):
            return user
        return None

    def find_user(self, username: str):
        return {"name": username}

    def verify(self, password: str) -> bool:
        return password == "secret"


def create_auth_service() -> AuthService:
    return AuthService()
''')

    (src / "api.py").write_text('''
from src.auth import AuthService, create_auth_service


def handle_login(request):
    """Handle login endpoint."""
    service = create_auth_service()
    user = service.login(request["username"], request["password"])
    return {"user": user}
''')

    # Wiki 目录 (带 code_anchors frontmatter)
    wiki = tmp_path / ".saw" / "wiki"
    wiki.mkdir(parents=True)

    (wiki / "authentication-design.md").write_text('''---
title: Authentication Design
code_anchors:
  - "src/auth.py::AuthService"
  - "src/auth.py::AuthService.login"
---

# Authentication Design

This document describes the authentication flow.
''')

    (wiki / "api-guide.md").write_text('''---
title: API Guide
code_anchors:
  - "src/api.py::handle_login"
---

# API Guide

How to use the login API.
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


@pytest.fixture
def bridge(engine, sample_project):
    """创建 Bridge 并扫描 Wiki"""
    wiki_path = sample_project / ".saw" / "wiki"
    b = BridgeLayer(engine.store, wiki_path=wiki_path)
    b.scan_wiki_for_anchors()
    return b


# ─── Bridge ───────────────────────────────────────────────────────


class TestBridge:
    def test_scan_wiki_anchors(self, bridge):
        """Wiki 扫描应发现 code_anchors"""
        stats = bridge.stats()
        assert stats["anchored_pages"] >= 2
        assert stats["linked_symbols"] >= 2

    def test_code_to_docs(self, bridge, engine):
        """代码符号 → 关联文档"""
        nodes = engine.find_nodes_by_name("AuthService")
        if nodes:
            docs = bridge.code_to_docs(nodes[0].uid)
            assert len(docs) >= 1
            assert any("authentication" in d.page_id for d in docs)

    def test_docs_to_code(self, bridge):
        """文档 → 锚定代码"""
        nodes = bridge.docs_to_code("authentication-design")
        assert len(nodes) >= 1
        names = [n.name for n in nodes]
        assert "AuthService" in names

    def test_manual_anchor(self, bridge, engine):
        """手动锚定"""
        bridge.anchor_page("test-page", "Test Page", ["src/auth.py::AuthService.verify"])
        docs = bridge.code_to_docs("src/auth.py::AuthService.verify")
        assert any(d.page_id == "test-page" for d in docs)

    def test_unanchor(self, bridge):
        """移除锚定"""
        bridge.anchor_page("temp", "Temp", ["some::uid"])
        bridge.unanchor_page("temp")
        assert bridge.docs_to_code("temp") == []

    def test_cross_impact(self, bridge):
        """跨图影响: 代码变更 → 文档过期"""
        result = bridge.cross_impact(["src/auth.py"])
        assert result.total_at_risk >= 1
        assert any("authentication" in d.page_id for d in result.stale_docs)

    def test_check_staleness_deleted_code(self, bridge):
        """锚定了不存在代码的文档应标记为过期"""
        bridge.anchor_page("orphan-doc", "Orphan", ["nonexistent.py::ghost_function"])
        stale = bridge.check_staleness()
        assert any(d.page_id == "orphan-doc" for d in stale)
        orphan = next(d for d in stale if d.page_id == "orphan-doc")
        assert orphan.reason == "code_deleted"


# ─── Snapshot ─────────────────────────────────────────────────────


class TestSnapshot:
    def test_create_and_list(self, engine):
        """创建和列出快照"""
        mgr = SnapshotManager(engine.store)
        snap = mgr.create("manual")
        assert snap.snapshot_id != ""
        assert snap.node_count > 0

        snapshots = mgr.list_snapshots()
        assert len(snapshots) >= 1
        assert snapshots[0]["trigger"] == "manual"

    def test_diff(self, engine):
        """快照间 diff"""
        mgr = SnapshotManager(engine.store)
        s1 = mgr.create("test_1")
        s2 = mgr.create("test_2")

        diff = mgr.diff(s1.snapshot_id, s2.snapshot_id)
        assert diff is not None
        assert diff.node_delta == 0  # 无变更

    def test_verify_integrity(self, engine):
        """完整性自检"""
        mgr = SnapshotManager(engine.store)
        result = mgr.verify_integrity()
        assert result["status"] in ("healthy", "degraded")
        assert result["node_count"] > 0


# ─── Context Tool ─────────────────────────────────────────────────


class TestContextTool:
    @pytest.mark.asyncio
    async def test_minimal_context(self, engine):
        """minimal 模式"""
        from saw.code_graph.context_tool import handle_code_context

        result = await handle_code_context("AuthService", detail_level="minimal", engine=engine)
        assert "error" not in result
        assert result["detail_level"] == "minimal"
        assert result["tokens_used"] > 0
        assert result["tokens_used"] <= result["token_budget"]

    @pytest.mark.asyncio
    async def test_standard_context(self, engine):
        """standard 模式包含关系"""
        from saw.code_graph.context_tool import handle_code_context

        result = await handle_code_context("login", detail_level="standard", engine=engine)
        assert "error" not in result
        assert "context" in result
        assert "context_savings" in result
        assert result["context_savings"]["savings_percent"] >= 0

    @pytest.mark.asyncio
    async def test_verbose_context(self, engine):
        """verbose 模式包含源码"""
        from saw.code_graph.context_tool import handle_code_context

        result = await handle_code_context("AuthService", detail_level="verbose", engine=engine)
        assert "error" not in result
        # verbose 应包含更多信息
        assert result["tokens_used"] > 0

    @pytest.mark.asyncio
    async def test_token_budget_respected(self, engine):
        """token 预算应被遵守"""
        from saw.code_graph.context_tool import handle_code_context

        result = await handle_code_context(
            "AuthService", detail_level="verbose", token_budget=100, engine=engine
        )
        assert result["tokens_used"] <= 100

    @pytest.mark.asyncio
    async def test_not_found(self, engine):
        """不存在的符号"""
        from saw.code_graph.context_tool import handle_code_context

        result = await handle_code_context("nonexistent_xyz", engine=engine)
        assert result["error"] == "node_not_found"


# ─── Govern ───────────────────────────────────────────────────────


class TestGovern:
    def test_on_code_change(self, engine, bridge):
        """代码变更 → 治理报告"""
        govern = CodeGovernIntegration(engine, bridge)
        report = govern.on_code_change(["src/auth.py"])

        assert report.timestamp != ""
        assert report.affected_symbols > 0
        assert len(report.stale_docs) >= 1
        assert len(report.recommendations) > 0

    def test_on_no_change(self, engine, bridge):
        """无变更 → 空报告"""
        govern = CodeGovernIntegration(engine, bridge)
        report = govern.on_code_change([])
        assert report.affected_symbols == 0
        assert "No code changes" in report.recommendations[0]

    def test_full_audit(self, engine, bridge):
        """全局审计"""
        # 添加一个锚定到不存在代码的文档
        bridge.anchor_page("broken", "Broken Doc", ["ghost.py::phantom"])

        govern = CodeGovernIntegration(engine, bridge)
        report = govern.full_audit()

        assert report.critical_count >= 1
        assert any("deleted code" in r for r in report.recommendations)


# ─── Integration ──────────────────────────────────────────────────


class TestSprint3Integration:
    def test_full_workflow(self, sample_project):
        """完整工作流: build → anchor → change → detect staleness"""
        db_path = sample_project / ".saw" / "integration.db"
        wiki_path = sample_project / ".saw" / "wiki"

        with CodeGraphEngine(sample_project, db_path=db_path) as eng:
            # Build
            eng.build(full=True, postprocess=True)
            assert eng.stats()["nodes"] > 0

            # Bridge
            bridge = BridgeLayer(eng.store, wiki_path=wiki_path)
            bridge.scan_wiki_for_anchors()
            assert bridge.stats()["anchored_pages"] >= 2

            # Govern: simulate change
            govern = CodeGovernIntegration(eng, bridge)
            report = govern.on_code_change(["src/auth.py"])
            assert report.affected_symbols > 0

            # Snapshot
            mgr = SnapshotManager(eng.store)
            snap = mgr.create("post_govern")
            assert snap.node_count > 0

            # Integrity
            integrity = mgr.verify_integrity()
            assert integrity["node_count"] > 0

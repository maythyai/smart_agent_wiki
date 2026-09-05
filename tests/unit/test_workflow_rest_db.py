"""Workflow REST DB tests (F-O-3, AC-WF-1/2/3).

Verifies that ``GET /api/v1/workflows`` reads from the durable
``workflow_executions`` DB table and merges live in-memory running workflows.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
from saw.adapters.storage.wiki_repository import WikiRepository
from saw.drivers.web.app import create_app
from saw.engines.query.compare import CompareEngine
from saw.engines.query.compiler import ContextCompiler
from saw.engines.query.engine import QueryEngine
from saw.engines.query.graph_traverse import GraphTraverse
from saw.engines.query.search import FTS5Search
from saw.engines.query.tree_mode import TreeModeSearch
from saw.write_queue.queue import SQLiteWriteQueue
from saw.api.routes import collaborate


def _build_client_with_conn(tmp_path: Path) -> tuple[TestClient, sqlite3.Connection]:
    """Build a TestClient with an in-memory DB, exposing ``conn`` on
    ``app.state`` so ``list_workflows`` can read it."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    wq = SQLiteWriteQueue(conn)
    claims_repo = SQLiteClaimsRepository(conn)
    wiki_repo = WikiRepository(tmp_path / "wiki")
    search = FTS5Search(conn)
    compiler = ContextCompiler(claims_repo, wiki_repo, search, conn)
    graph = GraphTraverse(conn)
    compare = CompareEngine(claims_repo, wiki_repo)
    tree = TreeModeSearch(wiki_repo, claims_repo, conn)
    query_engine = QueryEngine(
        search=search,
        compiler=compiler,
        graph=graph,
        compare_engine=compare,
        tree_mode=tree,
        llm=None,
        claims_repo=claims_repo,
        wiki_repo=wiki_repo,
        conn=conn,
    )
    app = create_app(
        query=query_engine,
        collaborate=MagicMock(),
        write_queue=wq,
        auth_mode="local",
    )
    app.state.conn = conn  # expose for list_workflows
    return TestClient(app), conn


def _seed_workflow_executions(conn: sqlite3.Connection, rows: list[tuple]) -> None:
    """Insert workflow_executions rows: (workflow_id, name, status, sc, tot,
    started_at, updated_at, finished_at)."""
    from saw.db.migrations import apply_migrations

    apply_migrations(conn)
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO workflow_executions "
            "(workflow_id, definition_name, status, steps_completed, "
            "steps_total, started_at, updated_at, finished_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            r,
        )
    conn.commit()


# ── AC-WF-1: REST reads DB ───────────────────────────────────────────

class TestWorkflowRestDB:
    def setup_method(self):
        """Clear in-memory _workflows dict before each test."""
        collaborate._workflows.clear()

    def test_ac_wf_1_rest_reads_db(self, tmp_path):
        """GET /api/v1/workflows returns DB-backed history rows."""
        client, conn = _build_client_with_conn(tmp_path)
        _seed_workflow_executions(conn, [
            ("wf-1", "knowledge_review", "completed", 4, 4,
             "2026-09-05T10:00:00", "2026-09-05T10:05:00", "2026-09-05T10:05:00"),
            ("wf-2", "lit_review", "failed", 2, 4,
             "2026-09-05T11:00:00", "2026-09-05T11:03:00", "2026-09-05T11:03:00"),
            ("wf-3", "daily_digest", "completed", 3, 3,
             "2026-09-05T12:00:00", "2026-09-05T12:10:00", "2026-09-05T12:10:00"),
        ])

        r = client.get("/api/v1/workflows")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 3
        workflows = data["workflows"]
        assert len(workflows) >= 3
        # Verify DB field names
        wf_ids = {w["workflow_id"] for w in workflows}
        assert "wf-1" in wf_ids
        assert "wf-2" in wf_ids
        assert "wf-3" in wf_ids
        # Check status field present
        for w in workflows:
            assert "status" in w
            assert "steps_completed" in w
            assert "steps_total" in w

    # ── AC-WF-2: REST merges live in-memory running ──────────────────

    def test_ac_wf_2_rest_merges_live(self, tmp_path):
        """A live running workflow not yet in DB appears in the response."""
        client, conn = _build_client_with_conn(tmp_path)
        _seed_workflow_executions(conn, [
            ("wf-db-1", "knowledge_review", "completed", 4, 4,
             "2026-09-05T10:00:00", "2026-09-05T10:05:00", "2026-09-05T10:05:00"),
        ])

        # Inject a live running workflow not in DB
        collaborate._workflows["wf-live-1"] = {
            "workflow_id": "wf-live-1",
            "workflow": "adhoc_review",
            "status": "running",
            "current_step": 2,
            "steps_total": 4,
            "started_at": "2026-09-05T13:00:00",
        }

        r = client.get("/api/v1/workflows")
        assert r.status_code == 200
        workflows = r.json()["workflows"]
        wf_ids = {w["workflow_id"] for w in workflows}
        assert "wf-live-1" in wf_ids
        # The live workflow should have status="running"
        live = [w for w in workflows if w["workflow_id"] == "wf-live-1"][0]
        assert live["status"] == "running"
        assert live["definition_name"] == "adhoc_review"
        assert live["steps_total"] == 4

    def test_ac_wf_2_live_overrides_stale_db(self, tmp_path):
        """When a workflow is both in DB (stale) and in-memory (running),
        the live status overrides the DB status."""
        client, conn = _build_client_with_conn(tmp_path)
        _seed_workflow_executions(conn, [
            ("wf-stale", "knowledge_review", "failed", 1, 4,
             "2026-09-05T10:00:00", "2026-09-05T10:01:00", "2026-09-05T10:01:00"),
        ])

        # Same workflow ID, now running in-memory
        collaborate._workflows["wf-stale"] = {
            "workflow_id": "wf-stale",
            "workflow": "knowledge_review",
            "status": "running",
            "current_step": 3,
            "steps_total": 4,
            "started_at": "2026-09-05T14:00:00",
        }

        r = client.get("/api/v1/workflows")
        workflows = r.json()["workflows"]
        wf = [w for w in workflows if w["workflow_id"] == "wf-stale"][0]
        assert wf["status"] == "running"  # live overrides stale DB
        assert wf["steps_completed"] == 3

    # ── AC-WF-3: CLI/REST same SQL source ─────────────────────────────

    def test_ac_wf_3_same_sql_as_cli(self, tmp_path):
        """REST list_workflows and CLI list_recent read the same
        workflow_executions table with the same ORDER BY clause."""
        client, conn = _build_client_with_conn(tmp_path)
        _seed_workflow_executions(conn, [
            ("wf-a", "review", "completed", 4, 4,
             "2026-09-05T10:00:00", "2026-09-05T10:05:00", "2026-09-05T10:05:00"),
            ("wf-b", "review", "completed", 3, 3,
             "2026-09-05T09:00:00", "2026-09-05T09:05:00", "2026-09-05T09:05:00"),
        ])

        # REST reads
        r = client.get("/api/v1/workflows")
        rest_ids = [w["workflow_id"] for w in r.json()["workflows"]]

        # Direct DB read with the same SQL as CLI list_recent
        from saw.db.migrations import apply_migrations

        apply_migrations(conn)
        db_rows = conn.execute(
            "SELECT workflow_id FROM workflow_executions "
            "ORDER BY COALESCE(updated_at, started_at) DESC LIMIT 20"
        ).fetchall()
        db_ids = [row[0] for row in db_rows]

        # Both should return the same set of workflow IDs
        assert set(rest_ids) == set(db_ids)
        assert "wf-a" in rest_ids
        assert "wf-b" in rest_ids

    # ── Fallback: no conn → in-memory only ────────────────────────────

    def test_fallback_no_conn_returns_inmemory(self, tmp_path):
        """When app.state has no conn, list_workflows falls back to
        in-memory _workflows only (backward compat)."""
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        wq = SQLiteWriteQueue(conn)
        claims_repo = SQLiteClaimsRepository(conn)
        wiki_repo = WikiRepository(tmp_path / "wiki")
        search = FTS5Search(conn)
        compiler = ContextCompiler(claims_repo, wiki_repo, search, conn)
        graph = GraphTraverse(conn)
        compare = CompareEngine(claims_repo, wiki_repo)
        tree = TreeModeSearch(wiki_repo, claims_repo, conn)
        query_engine = QueryEngine(
            search=search, compiler=compiler, graph=graph,
            compare_engine=compare, tree_mode=tree, llm=None,
            claims_repo=claims_repo, wiki_repo=wiki_repo, conn=conn,
        )
        app = create_app(
            query=query_engine, collaborate=MagicMock(),
            write_queue=wq, auth_mode="local",
        )
        # Do NOT set app.state.conn → should fall back to in-memory
        client = TestClient(app)

        collaborate._workflows["wf-mem"] = {
            "workflow_id": "wf-mem",
            "workflow": "test",
            "status": "running",
            "current_step": 1,
            "steps_total": 4,
            "started_at": "2026-09-05T15:00:00",
        }

        r = client.get("/api/v1/workflows")
        assert r.status_code == 200
        workflows = r.json()["workflows"]
        assert len(workflows) >= 1
        assert workflows[0]["workflow_id"] == "wf-mem"

"""Fresh-DB smoke harness for engine-chain nodes (F-A-2/3/4).

Mirrors the engine construction in ``ingest_cmd.py`` / ``query_cmd.py`` but on
a throwaway temp wiki + SQLite DB, in offline (no-LLM) mode so the smoke chain
is reproducible without network or model dependencies. NL query and online LLM
paths are deferred to F-A-5 (offline fallback).

A single :func:`build_smoke_context` wires every engine the smoke nodes need;
the nodes in :mod:`smoke_cmd` consume it and assert real engine outputs
(claims with provenance, query citations, govern reports).
"""
from __future__ import annotations

import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path

from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
from saw.adapters.storage.vault_repository import VaultRepository
from saw.adapters.storage.wiki_repository import WikiRepository
from saw.engines.govern.governor import Governor
from saw.engines.ingest.pipeline import IngestPipeline
from saw.engines.query.compare import CompareEngine
from saw.engines.query.compiler import ContextCompiler
from saw.engines.query.engine import QueryEngine
from saw.engines.query.graph_traverse import GraphTraverse
from saw.engines.query.search import FTS5Search
from saw.engines.query.tree_mode import TreeModeSearch
from saw.write_queue.dispatcher import Dispatcher
from saw.write_queue.queue import SQLiteWriteQueue
from saw.write_queue.sinks.claims_sink import ClaimsSink
from saw.write_queue.sinks.fts5_sink import FTS5Sink
from saw.write_queue.sinks.graph_sink import GraphSink
from saw.write_queue.sinks.vault_sink import VaultSink
from saw.write_queue.sinks.wiki_sink import WikiSink


@dataclass
class SmokeContext:
    """A fully-wired throwaway knowledge base for smoke nodes."""

    tmp_dir: Path
    conn: sqlite3.Connection
    claims_repo: SQLiteClaimsRepository
    vault_repo: VaultRepository
    wiki_repo: WikiRepository
    write_queue: SQLiteWriteQueue
    dispatcher: Dispatcher
    pipeline: IngestPipeline
    query_engine: QueryEngine
    governor: Governor

    def close(self) -> None:
        self.conn.close()


# A small, self-contained markdown fixture with factual sentences so claim
# extraction has something concrete to anchor (no network, no external docs).
FIXTURE_MD = """# Smoke Fixture Document

The Ed25519 signing algorithm produces a 64-byte signature.
Ed25519 public keys are 32 bytes long.
The write queue dispatches operations to registered sinks.
"""


def build_smoke_context() -> SmokeContext:
    """Build a fresh temp wiki + every engine in offline (no-LLM) mode.

    ``SQLiteClaimsRepository.__init__`` applies migrations, so the claims DB
    (outbox + receipts + FTS5 + graph tables) is ready before any engine
    touches it.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="saw-smoke-"))
    vault_path = tmp_dir / "vault"
    wiki_path = tmp_dir / "wiki"
    db_path = tmp_dir / ".saw" / "db" / "claims.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    vault_path.mkdir(parents=True, exist_ok=True)
    wiki_path.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))

    # Repositories — ClaimsRepository.__init__ runs apply_migrations (v1..v7).
    claims_repo = SQLiteClaimsRepository(conn)
    vault_repo = VaultRepository(vault_path, tmp_dir)
    wiki_repo = WikiRepository(wiki_path)

    # Write queue + dispatcher with every high-risk sink.
    write_queue = SQLiteWriteQueue(conn)
    dispatcher = Dispatcher(write_queue)
    dispatcher.register_sink(VaultSink(vault_repo))
    dispatcher.register_sink(ClaimsSink(claims_repo))
    dispatcher.register_sink(WikiSink(wiki_repo))
    dispatcher.register_sink(FTS5Sink(conn))
    dispatcher.register_sink(GraphSink(conn))

    # Ingest pipeline — offline (llm_router=None): rule/template extraction.
    pipeline = IngestPipeline(
        claims_repo=claims_repo,
        write_queue=write_queue,
        llm_router=None,
        vault_repo=vault_repo,
        wiki_repo=wiki_repo,
    )

    # Query engine — keyword/search mode (offline; NL deferred to F-A-5).
    search = FTS5Search(conn)
    tree_mode = TreeModeSearch(wiki_repo, claims_repo, conn)
    graph = GraphTraverse(conn)
    compare = CompareEngine(claims_repo, wiki_repo)
    compiler = ContextCompiler(claims_repo, wiki_repo, search, conn)
    query_engine = QueryEngine(
        search=search,
        compiler=compiler,
        graph=graph,
        compare_engine=compare,
        tree_mode=tree_mode,
        llm=None,
        claims_repo=claims_repo,
        wiki_repo=wiki_repo,
        conn=conn,
    )

    # Governor — lint + verify (offline).
    governor = Governor(claims_repo, wiki_repo, llm_router=None)

    return SmokeContext(
        tmp_dir=tmp_dir,
        conn=conn,
        claims_repo=claims_repo,
        vault_repo=vault_repo,
        wiki_repo=wiki_repo,
        write_queue=write_queue,
        dispatcher=dispatcher,
        pipeline=pipeline,
        query_engine=query_engine,
        governor=governor,
    )


def _ingest_fixture(ctx: SmokeContext) -> None:
    """Ingest the smoke fixture + dispatch (shared setup for engine nodes)."""
    fixture = ctx.tmp_dir / "fixture.md"
    fixture.write_text(FIXTURE_MD)
    ctx.pipeline.ingest(str(fixture))
    ctx.dispatcher.dispatch_pending()


# ── F-A-2 / F-A-3 / F-A-4 smoke nodes ────────────────────────────────
# Each node builds a fresh isolated context + ingests the fixture, so a
# failure in one node never contaminates another (smoke = independent probes).


def node_ingest_compile() -> bool:
    """F-A-2: ingest markdown fixture → claims with provenance anchor +
    a wiki page compiled (compile incremental)."""
    ctx = build_smoke_context()
    try:
        _ingest_fixture(ctx)
        rows = ctx.conn.execute(
            "SELECT source_uuid FROM claim WHERE deleted_at IS NULL"
        ).fetchall()
        if not rows:
            return False  # no claims extracted
        # AC: every claim traces to a vault source (anchor non-null).
        if not all(r[0] for r in rows):
            return False
        # AC: compile produced at least one wiki page.
        wiki_pages = list(ctx.tmp_dir.joinpath("wiki").rglob("*.md"))
        return len(wiki_pages) > 0
    finally:
        ctx.close()


def node_query_keyword() -> bool:
    """F-A-3: keyword query returns an answer + at least one cited source
    (offline search mode; NL deferred to F-A-5)."""
    ctx = build_smoke_context()
    try:
        _ingest_fixture(ctx)
        result = ctx.query_engine.query(question="Ed25519 signature", mode="search")
        # AC: answer non-empty + sources carry citation.
        return bool(result.answer) and bool(result.sources)
    finally:
        ctx.close()


def node_govern_learn() -> bool:
    """F-A-4: govern lint + verify produce non-empty reports; learn distiller
    plumbing does not error (offline: actual LLM distill deferred to F-A-5)."""
    from saw.engines.learn.distiller import Distiller

    ctx = build_smoke_context()
    try:
        _ingest_fixture(ctx)
        # AC: lint returns a real health report.
        report = ctx.governor.lint()
        if report is None:
            return False
        # AC: verify_claim returns a provenance chain for an ingested claim.
        row = ctx.conn.execute(
            "SELECT uuid FROM claim WHERE deleted_at IS NULL LIMIT 1"
        ).fetchone()
        if row is None:
            return False
        chain = ctx.governor.verify_claim(row[0])
        if chain is None:
            return False
        # AC: learn distiller module loads + offline-safe API does not raise
        # (actual LLM distill is online-only; F-A-5 covers offline fallback).
        distiller = Distiller(llm_router=None, sops_dir=ctx.tmp_dir / ".saw" / "sops")
        sops = distiller.get_sops()  # reads saved SOPs; no LLM, no error
        return isinstance(sops, list)
    finally:
        ctx.close()

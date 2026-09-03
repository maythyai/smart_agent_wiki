"""Smoke chain tests — F-A-2 / F-A-3 / F-A-4 (AC-E2E-1).

Exercises the same fresh-DB engine nodes wired into ``saw smoke`` so the CLI
smoke command and the unit tests share one contract.
"""
from __future__ import annotations

from saw.drivers.cli.commands.smoke_harness import (
    build_smoke_context,
    node_govern_learn,
    node_ingest_compile,
    node_query_keyword,
)


def _ingest(ctx) -> None:
    from saw.drivers.cli.commands.smoke_harness import _ingest_fixture

    _ingest_fixture(ctx)


# ── F-A-2: ingest + compile ──────────────────────────────────────────


def test_smoke_ingest_provenance() -> None:
    """AC-E2E-1: ingested markdown yields claims that trace to a vault source."""
    ctx = build_smoke_context()
    try:
        _ingest(ctx)
        rows = ctx.conn.execute(
            "SELECT source_uuid FROM claim WHERE deleted_at IS NULL"
        ).fetchall()
        assert rows, "no claims extracted from fixture"
        assert all(r[0] for r in rows), "claim missing provenance anchor (source_uuid)"
    finally:
        ctx.close()


def test_smoke_compile_incremental() -> None:
    """AC-E2E-1: compile produces at least one wiki page."""
    ctx = build_smoke_context()
    try:
        _ingest(ctx)
        pages = list(ctx.tmp_dir.joinpath("wiki").rglob("*.md"))
        assert pages, "no wiki page compiled"
    finally:
        ctx.close()


# ── F-A-3: query ─────────────────────────────────────────────────────


def test_smoke_query_keyword_citation() -> None:
    """AC-E2E-1: keyword query returns an answer with cited sources."""
    ctx = build_smoke_context()
    try:
        _ingest(ctx)
        result = ctx.query_engine.query(question="Ed25519 signature", mode="search")
        assert result.answer, "query returned no answer"
        assert result.sources, "query returned no cited sources"
    finally:
        ctx.close()


# ── F-A-4: govern + learn ────────────────────────────────────────────


def test_smoke_govern_lint_verify() -> None:
    """AC-E2E-1: govern lint + verify produce non-empty reports/provenance."""
    ctx = build_smoke_context()
    try:
        _ingest(ctx)
        report = ctx.governor.lint()
        assert report is not None, "lint returned no health report"
        row = ctx.conn.execute(
            "SELECT uuid FROM claim WHERE deleted_at IS NULL LIMIT 1"
        ).fetchone()
        assert row is not None
        chain = ctx.governor.verify_claim(row[0])
        assert chain is not None, "verify_claim returned no provenance chain"
    finally:
        ctx.close()


def test_smoke_learn_distill() -> None:
    """AC-E2E-1: learn distiller plumbing does not error (offline-safe)."""
    from saw.engines.learn.distiller import Distiller

    ctx = build_smoke_context()
    try:
        _ingest(ctx)
        distiller = Distiller(llm_router=None, sops_dir=ctx.tmp_dir / ".saw" / "sops")
        sops = distiller.get_sops()  # offline-safe; no LLM call
        assert isinstance(sops, list)
    finally:
        ctx.close()


# ── node-level smoke (the CLI contract) ──────────────────────────────


def test_node_ingest_compile() -> None:
    assert node_ingest_compile() is True


def test_node_query_keyword() -> None:
    assert node_query_keyword() is True


def test_node_govern_learn() -> None:
    assert node_govern_learn() is True


# ── F-A-5: offline fallback ──────────────────────────────────────────


def test_smoke_offline_fallback() -> None:
    """AC-E2E-2: with no LLM, ingest/govern/learn (no-LLM paths) + auto query
    still PASS via rule fallback."""
    ctx = build_smoke_context()
    try:
        _ingest(ctx)
        # no-LLM paths succeed (ingest already done; govern + learn).
        report = ctx.governor.lint()
        assert report is not None
        # auto query degrades to keyword search instead of crashing.
        result = ctx.query_engine.query(question="Ed25519", mode="auto")
        assert result.answer
    finally:
        ctx.close()


def test_smoke_offline_nl_degraded() -> None:
    """AC-E2E-2: an auto (would-be NL) query is degraded to search offline."""
    ctx = build_smoke_context()
    try:
        _ingest(ctx)
        result = ctx.query_engine.query(question="Ed25519 signature", mode="auto")
        assert result.mode == "search", (
            f"offline auto query should degrade to search, got {result.mode}"
        )
    finally:
        ctx.close()


def test_node_offline_fallback() -> None:
    from saw.drivers.cli.commands.smoke_harness import node_offline_fallback

    assert node_offline_fallback() is True

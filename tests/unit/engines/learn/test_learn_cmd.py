"""Learn engine CLI-path tests — T-F-I-2 (AC-LR-1, AC-LR-2).

distill: Distiller.extract_sop with a mock LLMRouter (CI has no LLM).
gaps:   TrendSenser.detect_gaps over a fresh wiki + empty claims repo.
"""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock


def test_distill_extracts_nonempty_sop_via_mock_llm(tmp_path):
    """AC-LR-1: distill produces a non-empty SOP via the online (LLM) path."""
    from saw.engines.learn.distiller import Distiller

    llm = MagicMock()
    llm.extract_claims.return_value = {
        "name": "Triage incoming sources",
        "trigger": "when a new source is ingested",
        "steps": ["classify", "prioritize", "route"],
        "source_patterns": ["p1", "p2"],
    }
    distiller = Distiller(llm_router=llm, sops_dir=tmp_path / "sops")
    approved = tmp_path / "approved.yaml"
    approved.write_text(
        "- action: triage\n  pattern: classify then route\n"
        "- action: triage\n  pattern: prioritize first\n"
    )
    sops = distiller.run_distillation(approved)
    assert len(sops) == 1
    sop = sops[0]
    assert sop.name == "Triage incoming sources"
    assert len(sop.steps) == 3  # non-empty payload
    # persisted to disk
    saved = list((tmp_path / "sops").glob("*.yaml"))
    assert saved, "SOP should be saved to .saw/sops/"
    llm.extract_claims.assert_called_once()


def test_gaps_detects_uncovered_topics(tmp_path):
    """AC-LR-2: gaps returns a list; an uncovered wiki topic surfaces as a gap."""
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.db.migrations import apply_migrations
    from saw.engines.learn.trends import TrendSenser

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    claims_repo = SQLiteClaimsRepository(conn)
    wiki_dir = tmp_path / "wiki" / "concepts"
    wiki_dir.mkdir(parents=True)
    (wiki_dir / "nonexistent-topic.md").write_text("# Nonexistent Topic\n\nno claims cover this")
    wiki_repo = WikiRepository(tmp_path / "wiki")

    senser = TrendSenser(claims_repo=claims_repo, wiki_repo=wiki_repo)
    gaps = senser.detect_gaps()
    assert isinstance(gaps, list)
    # With an empty claims DB, the wiki page stem has no matching claim → gap.
    topics = [g.topic for g in gaps]
    assert any("nonexistent" in t for t in topics), topics
    conn.close()

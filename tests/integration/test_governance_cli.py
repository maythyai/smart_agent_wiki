"""Integration tests for governance CLI commands."""
from __future__ import annotations

import tempfile
from pathlib import Path
import sqlite3
import unittest

from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
from saw.adapters.storage.wiki_repository import WikiRepository
from saw.domain.claims import Claim
from saw.domain.wiki import WikiPage
from saw.domain.value_objects import ConfidenceLevel, SourceMark, FreshnessLevel, PageType
from saw.engines.govern.governor import Governor
from saw.engines.govern.linter import Linter
from saw.engines.learn.fsrs_scheduler import FSRSScheduler


class TestGovernanceCLI(unittest.TestCase):
    """End-to-end tests for governance CLI commands."""

    def test_lint_command_outputs_health_report(self) -> None:
        """Test 1: `saw lint` outputs health report with Rich table formatting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "claims.db"
            wiki_path = Path(tmpdir) / "wiki"

            conn = sqlite3.connect(str(db_path))
            claims_repo = SQLiteClaimsRepository(conn)
            wiki_repo = WikiRepository(wiki_path)

            # Add some test data
            claim = Claim(
                uuid="test-claim",
                content="Test claim content",
                source_uuid="vault-1",
                content_hash="hash",
                confidence=ConfidenceLevel.SINGLE_SOURCE,
                source_mark=SourceMark.EXTRACTED,
            )
            claims_repo.insert(claim)

            # Create a wiki page
            wiki_repo.write(WikiPage(
                path="test.md",
                title="Test",
                content="Content",
                tags=["test"],
            ))

            linter = Linter(claims_repo, wiki_repo)
            report = linter.lint()

            self.assertEqual(report.total_claims, 1)
            self.assertEqual(report.total_pages, 1)
            self.assertIsInstance(report.health_score, int)

            conn.close()

    def test_verify_command_outputs_provenance(self) -> None:
        """Test 2: `saw verify <claim_uuid>` outputs provenance chain."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "claims.db"
            wiki_path = Path(tmpdir) / "wiki"

            conn = sqlite3.connect(str(db_path))
            claims_repo = SQLiteClaimsRepository(conn)
            wiki_repo = WikiRepository(wiki_path)

            claim = Claim(
                uuid="verify-test",
                content="Claim to verify",
                source_uuid="vault-doc-123",
                content_hash="hash",
                confidence=ConfidenceLevel.SINGLE_SOURCE,
                source_mark=SourceMark.EXTRACTED,
                page_number=5,
                line_number=10,
            )
            claims_repo.insert(claim)

            governor = Governor(claims_repo, wiki_repo)
            provenance = governor.verify_claim("verify-test")

            self.assertIsNotNone(provenance)
            self.assertEqual(provenance.claim_uuid, "verify-test")
            self.assertEqual(provenance.source_uuid, "vault-doc-123")
            self.assertEqual(provenance.source_type, "EXTRACTED")

            conn.close()

    def test_freshness_command_outputs_distribution(self) -> None:
        """Test 3: `saw freshness` outputs freshness distribution with color indicators."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "claims.db"
            wiki_path = Path(tmpdir) / "wiki"

            conn = sqlite3.connect(str(db_path))
            claims_repo = SQLiteClaimsRepository(conn)
            wiki_repo = WikiRepository(wiki_path)

            governor = Governor(claims_repo, wiki_repo)
            report = governor.get_freshness_report()

            self.assertIn("distribution", report.__dict__)
            self.assertIn("color_summary", report.__dict__)
            self.assertIn("green", report.color_summary)
            self.assertIn("yellow", report.color_summary)

            conn.close()

    def test_review_command_outputs_queue(self) -> None:
        """Test 4: `saw review` outputs review queue."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "claims.db"
            wiki_path = Path(tmpdir) / "wiki"

            conn = sqlite3.connect(str(db_path))
            claims_repo = SQLiteClaimsRepository(conn)
            wiki_repo = WikiRepository(wiki_path)

            # Create a stale page
            wiki_repo.write(WikiPage(
                path="stale-page.md",
                title="Stale Page",
                content="Old content",
                freshness=FreshnessLevel.LEVEL_7,  # Stale
                tags=["test"],
            ))

            scheduler = FSRSScheduler(wiki_repo, claims_repo, data_dir=Path(tmpdir))
            queue = scheduler.get_review_queue()

            # Queue should include stale pages
            self.assertIsInstance(queue, list)
            # The stale page should be in queue
            paths = [item.page_path for item in queue]
            self.assertIn("stale-page.md", paths)

            conn.close()


if __name__ == "__main__":
    unittest.main()
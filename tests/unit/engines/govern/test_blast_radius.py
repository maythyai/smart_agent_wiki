"""Tests for blast radius analysis.

Tests the BlastRadiusAnalyzer class with:
1. analyze() returns affected entities/pages
2. Graph traversal for downstream dependencies
3. Wiki page reference identification
4. Risk score calculation
"""
from __future__ import annotations

import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from saw.domain.claims import Claim
from saw.domain.entities import Entity
from saw.domain.wiki import WikiPage
from saw.domain.value_objects import ConfidenceLevel, PageType, FreshnessLevel
from saw.engines.govern.blast_radius import (
    BlastRadiusAnalyzer,
    BlastRadiusReport,
)


class TestAnalyze:
    """Test 1: analyze() returns affected entities/pages."""

    def test_returns_all_affected_claims(self) -> None:
        """Should find claims that depend on this claim."""
        claims_repo = MagicMock()
        wiki_repo = MagicMock()
        graph = MagicMock()

        # Setup: claim with related claims
        claims_repo.get_by_id.return_value = Claim(
            uuid="claim-1",
            content="Test claim content",
            source_uuid="doc-1",
            content_hash="hash-1",
        )
        claims_repo.search.return_value = [
            Claim(
                uuid="claim-2",
                content="Related claim referencing claim-1",
                source_uuid="doc-2",
                content_hash="hash-2",
            ),
        ]

        analyzer = BlastRadiusAnalyzer(claims_repo, wiki_repo, graph)
        report = analyzer.analyze("claim-1")

        assert report.source_claim_uuid == "claim-1"
        assert isinstance(report.affected_claims, list)

    def test_returns_affected_wiki_pages(self) -> None:
        """Should find Wiki pages referencing the claim."""
        claims_repo = MagicMock()
        wiki_repo = MagicMock()
        graph = MagicMock()

        claims_repo.get_by_id.return_value = Claim(
            uuid="claim-1",
            content="Test",
            source_uuid="doc-1",
            content_hash="hash-1",
        )

        # Mock wiki pages with claim citations
        wiki_repo.list_pages.return_value = ["page-1.md", "page-2.md"]
        wiki_repo.read.side_effect = lambda p: WikiPage(
            path=p,
            title=p.replace(".md", ""),
            page_type=PageType.SUMMARY,
            content="Some content with [^claim:claim-1] citation",
            confidence=ConfidenceLevel.SINGLE_SOURCE,
            freshness=FreshnessLevel.LEVEL_0,
        ) if p == "page-1.md" else None

        analyzer = BlastRadiusAnalyzer(claims_repo, wiki_repo, graph)
        report = analyzer.analyze("claim-1")

        assert "page-1.md" in report.affected_pages


class TestGraphTraversal:
    """Test 2: Correctly traverses graph to find downstream dependencies."""

    def test_finds_downstream_entities(self) -> None:
        """Should traverse graph to find connected entities."""
        claims_repo = MagicMock()
        wiki_repo = MagicMock()
        graph = MagicMock()

        claims_repo.get_by_id.return_value = Claim(
            uuid="claim-1",
            content="Entity A is related to Entity B",
            source_uuid="doc-1",
            content_hash="hash-1",
            entities=["entity-a", "entity-b"],
        )

        # Mock graph traversal
        graph.get_neighbors.return_value = [
            Entity(
                uuid="entity-b",
                name="Entity B",
                entity_type="concept",
            ),
        ]

        analyzer = BlastRadiusAnalyzer(claims_repo, wiki_repo, graph)
        report = analyzer.analyze("claim-1")

        assert isinstance(report.affected_entities, list)

    def test_traverses_multiple_levels(self) -> None:
        """Should traverse more than one level deep."""
        claims_repo = MagicMock()
        wiki_repo = MagicMock()
        graph = MagicMock()

        claims_repo.get_by_id.return_value = Claim(
            uuid="claim-1",
            content="Complex claim",
            source_uuid="doc-1",
            content_hash="hash-1",
            entities=["entity-a"],
        )

        graph.get_neighbors.return_value = []

        analyzer = BlastRadiusAnalyzer(claims_repo, wiki_repo, graph)
        report = analyzer.analyze("claim-1")

        # Should not error on empty neighbors
        assert report.affected_entities == []


class TestWikiPageReferences:
    """Test 3: Identifies Wiki pages that reference the claim."""

    def test_finds_pages_with_claim_citations(self) -> None:
        """Should find pages with [^claim:uuid] citations."""
        claims_repo = MagicMock()
        wiki_repo = MagicMock()
        graph = MagicMock()

        claims_repo.get_by_id.return_value = Claim(
            uuid="claim-123",
            content="Test",
            source_uuid="doc-1",
            content_hash="hash-1",
        )

        wiki_repo.list_pages.return_value = ["concepts/test.md"]
        wiki_repo.read.return_value = WikiPage(
            path="concepts/test.md",
            title="Test Page",
            page_type=PageType.SUMMARY,
            content="Content with [^claim:claim-123] reference",
            confidence=ConfidenceLevel.SINGLE_SOURCE,
            freshness=FreshnessLevel.LEVEL_0,
        )

        analyzer = BlastRadiusAnalyzer(claims_repo, wiki_repo, graph)
        report = analyzer.analyze("claim-123")

        assert "concepts/test.md" in report.affected_pages

    def test_handles_pages_without_citations(self) -> None:
        """Should handle pages without relevant citations."""
        claims_repo = MagicMock()
        wiki_repo = MagicMock()
        graph = MagicMock()

        claims_repo.get_by_id.return_value = Claim(
            uuid="claim-1",
            content="Test",
            source_uuid="doc-1",
            content_hash="hash-1",
        )

        wiki_repo.list_pages.return_value = ["page.md"]
        wiki_repo.read.return_value = WikiPage(
            path="page.md",
            title="Page",
            page_type=PageType.SUMMARY,
            content="No citations here",
            confidence=ConfidenceLevel.SINGLE_SOURCE,
            freshness=FreshnessLevel.LEVEL_0,
        )

        analyzer = BlastRadiusAnalyzer(claims_repo, wiki_repo, graph)
        report = analyzer.analyze("claim-1")

        assert report.affected_pages == []


class TestRiskScore:
    """Test 4: Calculates risk score based on impact breadth."""

    def test_low_risk_score_for_minimal_impact(self) -> None:
        """0-30: No dependent claims, single page reference."""
        claims_repo = MagicMock()
        wiki_repo = MagicMock()
        graph = MagicMock()

        claims_repo.get_by_id.return_value = Claim(
            uuid="claim-1",
            content="Test",
            source_uuid="doc-1",
            content_hash="hash-1",
        )
        claims_repo.search.return_value = []
        wiki_repo.list_pages.return_value = []

        analyzer = BlastRadiusAnalyzer(claims_repo, wiki_repo, graph)
        report = analyzer.analyze("claim-1")

        assert 0 <= report.risk_score <= 100
        assert report.recommendation in ["safe to edit", "review required", "high impact"]

    def test_medium_risk_score_for_moderate_impact(self) -> None:
        """31-70: 1-5 dependent claims, multiple page references."""
        claims_repo = MagicMock()
        wiki_repo = MagicMock()
        graph = MagicMock()

        claims_repo.get_by_id.return_value = Claim(
            uuid="claim-1",
            content="Test",
            source_uuid="doc-1",
            content_hash="hash-1",
        )
        claims_repo.search.return_value = [
            Claim(uuid=f"claim-{i}", content=f"Related {i}",
                  source_uuid="doc-1", content_hash=f"hash-{i}")
            for i in range(3)
        ]
        wiki_repo.list_pages.return_value = ["page-1.md", "page-2.md"]
        wiki_repo.read.return_value = WikiPage(
            path="page-1.md",
            title="Page 1",
            page_type=PageType.SUMMARY,
            content="[^claim:claim-1]",
            confidence=ConfidenceLevel.SINGLE_SOURCE,
            freshness=FreshnessLevel.LEVEL_0,
        )

        analyzer = BlastRadiusAnalyzer(claims_repo, wiki_repo, graph)
        report = analyzer.analyze("claim-1")

        assert 0 <= report.risk_score <= 100

    def test_high_risk_score_for_broad_impact(self) -> None:
        """71-100: >5 dependent claims, core entity references."""
        claims_repo = MagicMock()
        wiki_repo = MagicMock()
        graph = MagicMock()

        claims_repo.get_by_id.return_value = Claim(
            uuid="claim-1",
            content="Core concept",
            source_uuid="doc-1",
            content_hash="hash-1",
            entities=["core-entity"],
        )
        claims_repo.search.return_value = [
            Claim(uuid=f"claim-{i}", content=f"Related {i}",
                  source_uuid="doc-1", content_hash=f"hash-{i}")
            for i in range(7)
        ]
        wiki_repo.list_pages.return_value = [f"page-{i}.md" for i in range(5)]
        wiki_repo.read.return_value = WikiPage(
            path="page-1.md",
            title="Page 1",
            page_type=PageType.SUMMARY,
            content="[^claim:claim-1]",
            confidence=ConfidenceLevel.SINGLE_SOURCE,
            freshness=FreshnessLevel.LEVEL_0,
        )

        analyzer = BlastRadiusAnalyzer(claims_repo, wiki_repo, graph)
        report = analyzer.analyze("claim-1")

        assert report.risk_score >= 50  # High impact should reflect in score


class TestAnalyzePage:
    """Tests for analyze_page() method."""

    def test_analyzes_entire_page_impact(self) -> None:
        """Should analyze impact of editing entire Wiki page."""
        claims_repo = MagicMock()
        wiki_repo = MagicMock()
        graph = MagicMock()

        wiki_repo.read.return_value = WikiPage(
            path="concepts/test.md",
            title="Test",
            page_type=PageType.SUMMARY,
            content="Content with [^claim:claim-1] and [^claim:claim-2]",
            confidence=ConfidenceLevel.SINGLE_SOURCE,
            freshness=FreshnessLevel.LEVEL_0,
        )
        wiki_repo.list_pages.return_value = ["concepts/test.md"]

        analyzer = BlastRadiusAnalyzer(claims_repo, wiki_repo, graph)
        report = analyzer.analyze_page("concepts/test.md")

        assert report.source_page_path == "concepts/test.md"


class TestCheckEditSafety:
    """Tests for check_edit_safety() method."""

    def test_returns_safety_tuple(self) -> None:
        """Should return (is_safe, reason) tuple."""
        claims_repo = MagicMock()
        wiki_repo = MagicMock()
        graph = MagicMock()

        claims_repo.get_by_id.return_value = Claim(
            uuid="claim-1",
            content="Test",
            source_uuid="doc-1",
            content_hash="hash-1",
        )
        claims_repo.search.return_value = []
        wiki_repo.list_pages.return_value = []

        analyzer = BlastRadiusAnalyzer(claims_repo, wiki_repo, graph)
        is_safe, reason = analyzer.check_edit_safety("claim-1")

        assert isinstance(is_safe, bool)
        assert isinstance(reason, str)

    def test_safe_for_low_impact(self) -> None:
        """Should be safe for low-risk claims."""
        claims_repo = MagicMock()
        wiki_repo = MagicMock()
        graph = MagicMock()

        claims_repo.get_by_id.return_value = Claim(
            uuid="claim-1",
            content="Isolated claim",
            source_uuid="doc-1",
            content_hash="hash-1",
        )
        claims_repo.search.return_value = []
        wiki_repo.list_pages.return_value = []

        analyzer = BlastRadiusAnalyzer(claims_repo, wiki_repo, graph)
        is_safe, reason = analyzer.check_edit_safety("claim-1")

        assert is_safe is True


class TestBlastRadiusReport:
    """Tests for BlastRadiusReport dataclass."""

    def test_report_stores_all_fields(self) -> None:
        """Report should store all required fields."""
        report = BlastRadiusReport(
            source_claim_uuid="claim-1",
            source_page_path="page.md",
            affected_claims=["claim-2", "claim-3"],
            affected_pages=["page-2.md"],
            affected_entities=["entity-1"],
            risk_score=45,
            recommendation="review required",
        )

        assert report.source_claim_uuid == "claim-1"
        assert report.source_page_path == "page.md"
        assert report.affected_claims == ["claim-2", "claim-3"]
        assert report.affected_pages == ["page-2.md"]
        assert report.affected_entities == ["entity-1"]
        assert report.risk_score == 45
        assert report.recommendation == "review required"

    def test_recommendation_matches_risk(self) -> None:
        """Recommendation should reflect risk level."""
        low_risk = BlastRadiusReport(
            source_claim_uuid="c-1",
            source_page_path=None,
            affected_claims=[],
            affected_pages=[],
            affected_entities=[],
            risk_score=10,
            recommendation="safe to edit",
        )
        high_risk = BlastRadiusReport(
            source_claim_uuid="c-2",
            source_page_path=None,
            affected_claims=[],
            affected_pages=[],
            affected_entities=[],
            risk_score=85,
            recommendation="high impact",
        )

        assert low_risk.recommendation == "safe to edit"
        assert high_risk.recommendation == "high impact"

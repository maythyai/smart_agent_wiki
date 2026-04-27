"""Tests for Research-on-Miss Handler.

Per 02-03 Task 5: Research-on-Miss automatic knowledge gap filling.
Per XCUT-08 and FEATURES.md (llm-wiki1 pattern).
"""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio


class TestResearchOnMissTrigger:
    """Tests for gap coverage detection."""

    def test_should_trigger_returns_true_when_coverage_below_threshold(self):
        """Test 1: ResearchOnMissHandler.should_trigger() returns True when coverage < threshold."""
        from saw.drivers.mcp.research_on_miss import ResearchOnMissHandler

        mock_pipeline = MagicMock()
        mock_config = MagicMock()
        mock_config.coverage_threshold = 0.5
        mock_llm = MagicMock()

        handler = ResearchOnMissHandler(mock_pipeline, mock_config, mock_llm)

        assert handler.should_trigger(0.3) == True

    def test_should_trigger_returns_false_when_coverage_above_threshold(self):
        """should_trigger() returns False when coverage >= threshold."""
        from saw.drivers.mcp.research_on_miss import ResearchOnMissHandler

        mock_pipeline = MagicMock()
        mock_config = MagicMock()
        mock_config.coverage_threshold = 0.5
        mock_llm = MagicMock()

        handler = ResearchOnMissHandler(mock_pipeline, mock_config, mock_llm)

        assert handler.should_trigger(0.7) == False


class TestResearchExecution:
    """Tests for parallel research execution."""

    @pytest.mark.asyncio
    async def test_trigger_research_starts_parallel_searches(self):
        """Test 2: Handler.trigger_research() starts parallel searches (web/academic/code)."""
        from saw.drivers.mcp.research_on_miss import ResearchOnMissHandler

        mock_pipeline = MagicMock()
        mock_config = MagicMock()
        mock_config.coverage_threshold = 0.5
        mock_llm = MagicMock()

        handler = ResearchOnMissHandler(mock_pipeline, mock_config, mock_llm)

        # Mock the search methods
        with patch.object(handler, "_web_search", return_value=[{"url": "http://test.com"}]) as mock_web:
            with patch.object(handler, "_academic_search", return_value=[]) as mock_academic:
                with patch.object(handler, "_code_search", return_value=[]) as mock_code:
                    with patch.object(handler, "_generate_search_queries", return_value={"web": "test", "academic": "test", "code": "test"}):
                        result = await handler.trigger_research("test query")

                        # Should have called all three search types
                        mock_web.assert_called_once()
                        mock_academic.assert_called_once()
                        mock_code.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_research_queues_results_for_ingestion(self):
        """Test 3: Handler queues results for ingestion."""
        from saw.drivers.mcp.research_on_miss import ResearchOnMissHandler

        mock_pipeline = MagicMock()
        mock_pipeline.ingest = MagicMock(return_value=MagicMock(claim_count=5, pages_created=[]))

        mock_config = MagicMock()
        mock_config.coverage_threshold = 0.5
        mock_llm = MagicMock()

        handler = ResearchOnMissHandler(mock_pipeline, mock_config, mock_llm)

        with patch.object(handler, "_web_search", return_value=[{"url": "http://test.com", "title": "Test"}]):
            with patch.object(handler, "_academic_search", return_value=[]):
                with patch.object(handler, "_code_search", return_value=[]):
                    with patch.object(handler, "_generate_search_queries", return_value={"web": "test", "academic": "test", "code": "test"}):
                        with patch.object(handler, "_dedupe_sources", return_value=[{"url": "http://test.com"}]):
                            result = await handler.trigger_research("test query")

                            assert result is not None
                            assert result.query == "test query"


class TestRateLimiting:
    """Tests for rate limiting."""

    def test_handler_respects_rate_limits(self):
        """Test 4: Handler respects rate limits for external APIs."""
        from saw.drivers.mcp.research_on_miss import ResearchOnMissHandler, RateLimiter

        mock_pipeline = MagicMock()
        mock_config = MagicMock()
        mock_config.coverage_threshold = 0.5
        mock_llm = MagicMock()

        handler = ResearchOnMissHandler(mock_pipeline, mock_config, mock_llm)

        # Check that rate limiter exists
        assert handler._rate_limiter is not None

        # Check rate limiter allows calls
        assert handler._rate_limiter.allow() == True


class TestResearchResult:
    """Tests for ResearchResult dataclass."""

    def test_research_result_has_required_fields(self):
        """ResearchResult has query, sources, coverage_before, coverage_after, pages_added."""
        from saw.drivers.mcp.research_on_miss import ResearchResult

        result = ResearchResult(
            query="test query",
            sources=[{"url": "http://test.com"}],
            coverage_before=0.3,
            coverage_after=0.5,
            pages_added=["page1.md"],
            duration_ms=500,
        )

        assert result.query == "test query"
        assert result.sources == [{"url": "http://test.com"}]
        assert result.coverage_before == 0.3
        assert result.coverage_after == 0.5
        assert result.pages_added == ["page1.md"]
        assert result.duration_ms == 500


class TestGapDetection:
    """Tests for knowledge gap detection."""

    @pytest.mark.asyncio
    async def test_handler_detects_gap_and_triggers(self):
        """Integration test: low coverage triggers research."""
        from saw.drivers.mcp.research_on_miss import ResearchOnMissHandler

        mock_pipeline = MagicMock()
        mock_config = MagicMock()
        mock_config.coverage_threshold = 0.5
        mock_llm = MagicMock()

        handler = ResearchOnMissHandler(mock_pipeline, mock_config, mock_llm)

        # Low coverage should trigger
        coverage = 0.2
        assert handler.should_trigger(coverage) == True

        # High coverage should not trigger
        coverage = 0.8
        assert handler.should_trigger(coverage) == False

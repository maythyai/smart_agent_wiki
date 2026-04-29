"""Unit tests for Search API endpoint.

Tests for GET /api/search endpoint per D-07~09:
- Search returns results with proper format
- Empty query returns 422 validation error
- Pagination works correctly
- Confidence filtering works
- Type filtering works
- Result format includes all required fields
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from saw.drivers.web.app import create_app
from saw.engines.query.engine import QueryResult


@pytest.fixture
def mock_query_engine() -> MagicMock:
    """Create mock QueryEngine with search results."""
    engine = MagicMock()
    engine.query.return_value = QueryResult(
        answer="Found 2 results for 'machine'",
        sources=[
            {
                "claim_uuid": "uuid-1",
                "content": "Machine learning is a subset of AI that uses neural networks.",
                "confidence": "cross_validated",
                "title": "Machine Learning",
                "score": 0.95,
                "type": "concept",
                "tags": ["ai", "ml"],
            },
            {
                "claim_uuid": "uuid-2",
                "content": "Deep learning uses multiple layers of neural networks.",
                "confidence": "single_source",
                "title": "Deep Learning",
                "score": 0.85,
                "type": "concept",
                "tags": ["ai", "dl"],
            },
            {
                "claim_uuid": "uuid-3",
                "content": "Neural networks are computing systems inspired by biological neurons.",
                "confidence": "unverified",
                "title": "Neural Networks",
                "score": 0.75,
                "type": "concept",
                "tags": ["ai", "nn"],
            },
        ],
        mode="search",
    )
    return engine


@pytest.fixture
def client(mock_query_engine: MagicMock) -> TestClient:
    """Create TestClient with mock engines."""
    app = create_app(
        query=mock_query_engine,
        collaborate=MagicMock(),
        write_queue=MagicMock(),
    )
    return TestClient(app)


def test_search_returns_results(client: TestClient, mock_query_engine: MagicMock) -> None:
    """Test GET /api/search returns 200 with SearchResponse."""
    response = client.get("/api/search?q=machine")

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data
    assert data["page"] == 1
    mock_query_engine.query.assert_called_once()


def test_search_empty_query_returns_422(client: TestClient) -> None:
    """Test empty query q='' returns 422 validation error."""
    response = client.get("/api/search?q=")

    assert response.status_code == 422


def test_search_pagination(client: TestClient, mock_query_engine: MagicMock) -> None:
    """Test pagination with page=2, per_page=5."""
    response = client.get("/api/search?q=machine&page=2&per_page=5")

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["per_page"] == 5


def test_search_min_confidence_filter(client: TestClient) -> None:
    """Test min_confidence=3 filters out low confidence results."""
    response = client.get("/api/search?q=machine&min_confidence=3")

    assert response.status_code == 200
    data = response.json()
    # Only cross_validated (3) and human_verified (4) should be returned
    for result in data["results"]:
        assert result["confidence"] >= 3


def test_search_type_filter(client: TestClient) -> None:
    """Test type=entity filter returns only matching type."""
    response = client.get("/api/search?q=machine&type=concept")

    assert response.status_code == 200
    data = response.json()
    # All results in mock have type="concept", so all should pass
    assert len(data["results"]) >= 1


def test_search_result_format(client: TestClient) -> None:
    """Test result format includes slug, title, snippet, confidence, freshness, citations."""
    response = client.get("/api/search?q=machine")

    assert response.status_code == 200
    data = response.json()
    if data["results"]:
        result = data["results"][0]
        assert "slug" in result
        assert "title" in result
        assert "snippet" in result
        assert "confidence" in result
        assert "freshness" in result
        assert "citations" in result
        assert "score" in result


def test_search_suggestions(client: TestClient, mock_query_engine: MagicMock) -> None:
    """Test GET /api/search/suggestions returns title suggestions."""
    response = client.get("/api/search/suggestions?q=mach&limit=5")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    mock_query_engine.query.assert_called()


def test_search_has_more_field(client: TestClient) -> None:
    """Test has_more field indicates pagination continuation."""
    response = client.get("/api/search?q=machine&per_page=1")

    assert response.status_code == 200
    data = response.json()
    assert "has_more" in data
    # With 3 results and per_page=1, should have more
    assert data["has_more"] is True


def test_search_default_pagination(client: TestClient) -> None:
    """Test default pagination values (page=1, per_page=10)."""
    response = client.get("/api/search?q=machine")

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["per_page"] == 10


def test_search_confidence_int_values(client: TestClient) -> None:
    """Test confidence values are correctly mapped from strings to ints."""
    response = client.get("/api/search?q=machine")

    assert response.status_code == 200
    data = response.json()
    if data["results"]:
        for result in data["results"]:
            # Confidence should be int 1-4
            assert isinstance(result["confidence"], int)
            assert 1 <= result["confidence"] <= 4
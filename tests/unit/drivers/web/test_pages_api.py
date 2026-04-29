"""Unit tests for Page API endpoints.

Tests for GET/PUT/DELETE /api/pages endpoints per D-13~16:
- List pages returns slug list
- Get page returns content and frontmatter
- Get non-existent page returns 404
- PUT and DELETE use Write Queue
- Result format includes all required fields
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from saw.drivers.web.app import create_app
from saw.domain.wiki import WikiPage
from saw.domain.value_objects import ConfidenceLevel, FreshnessLevel


@pytest.fixture
def mock_wiki_repo() -> MagicMock:
    """Create mock WikiRepository."""
    repo = MagicMock()
    repo.list_pages.return_value = ["machine-learning", "neural-networks", "transformers"]
    repo.read.return_value = WikiPage(
        path="machine-learning",
        title="Machine Learning",
        content="# Machine Learning\n\nContent here...",
        frontmatter={"type": "summary", "tags": ["ai", "ml"]},
    )
    return repo


@pytest.fixture
def mock_write_queue() -> MagicMock:
    """Create mock SQLiteWriteQueue."""
    queue = MagicMock()
    queue.enqueue_atomic = MagicMock()
    return queue


@pytest.fixture
def mock_query_engine(mock_wiki_repo: MagicMock) -> MagicMock:
    """Create mock QueryEngine with wiki repo."""
    engine = MagicMock()
    engine._wiki_repo = mock_wiki_repo
    return engine


@pytest.fixture
def client(
    mock_query_engine: MagicMock, mock_write_queue: MagicMock
) -> TestClient:
    """Create TestClient with mock engines."""
    app = create_app(
        query=mock_query_engine,
        collaborate=MagicMock(),
        write_queue=mock_write_queue,
    )
    return TestClient(app)


class TestListPages:
    """Tests for GET /api/pages endpoint."""

    def test_list_pages_returns_slug_list(self, client: TestClient) -> None:
        """Test GET /api/pages returns 200 with page list."""
        response = client.get("/api/pages")

        assert response.status_code == 200
        data = response.json()
        assert "slugs" in data
        assert "total" in data
        assert data["total"] == 3

    def test_list_pages_format(self, client: TestClient) -> None:
        """Test list response format."""
        response = client.get("/api/pages")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["slugs"], list)
        assert all(isinstance(s, str) for s in data["slugs"])


class TestGetPage:
    """Tests for GET /api/pages/{slug} endpoint."""

    def test_get_page_returns_content(
        self, client: TestClient, mock_wiki_repo: MagicMock
    ) -> None:
        """Test GET /api/pages/{slug} returns page content."""
        response = client.get("/api/pages/machine-learning")

        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "machine-learning"
        assert data["title"] == "Machine Learning"
        assert "content" in data
        assert "frontmatter" in data
        mock_wiki_repo.read.assert_called_once_with("machine-learning")

    def test_get_page_not_found(
        self, client: TestClient, mock_wiki_repo: MagicMock
    ) -> None:
        """Test non-existent page returns 404."""
        mock_wiki_repo.read.return_value = None

        response = client.get("/api/pages/nonexistent")

        assert response.status_code == 404

    def test_page_response_format(self, client: TestClient) -> None:
        """Test PageResponse includes all required fields."""
        response = client.get("/api/pages/machine-learning")

        assert response.status_code == 200
        data = response.json()
        assert "slug" in data
        assert "title" in data
        assert "content" in data
        assert "frontmatter" in data
        assert "confidence" in data
        assert "freshness" in data


class TestUpdatePage:
    """Tests for PUT /api/pages/{slug} endpoint."""

    def test_update_page_calls_write_queue(
        self, client: TestClient, mock_write_queue: MagicMock
    ) -> None:
        """Test PUT calls WriteQueue.enqueue_atomic."""
        response = client.put(
            "/api/pages/machine-learning",
            json={"content": "Updated content", "message": "Fix typo"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["slug"] == "machine-learning"
        mock_write_queue.enqueue_atomic.assert_called_once()

    def test_update_page_returns_op_id(
        self, client: TestClient, mock_write_queue: MagicMock
    ) -> None:
        """Test update returns operation ID."""
        response = client.put(
            "/api/pages/machine-learning",
            json={"content": "Updated content"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "op_id" in data
        assert data["op_id"] is not None

    def test_update_page_optional_message(
        self, client: TestClient, mock_write_queue: MagicMock
    ) -> None:
        """Test update works without message."""
        response = client.put(
            "/api/pages/machine-learning",
            json={"content": "Updated content"},
        )

        assert response.status_code == 200


class TestDeletePage:
    """Tests for DELETE /api/pages/{slug} endpoint."""

    def test_delete_page_calls_write_queue(
        self, client: TestClient, mock_write_queue: MagicMock
    ) -> None:
        """Test DELETE calls WriteQueue.enqueue_atomic."""
        # DELETE with body requires request object
        import json
        response = client.request(
            "DELETE",
            "/api/pages/machine-learning",
            content=json.dumps({"message": "Outdated content"}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        mock_write_queue.enqueue_atomic.assert_called_once()

    def test_delete_page_optional_message(
        self, client: TestClient, mock_write_queue: MagicMock
    ) -> None:
        """Test delete works without message."""
        response = client.delete("/api/pages/machine-learning")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"


class TestCreatePage:
    """Tests for POST /api/pages endpoint."""

    def test_create_page_calls_write_queue(
        self, client: TestClient, mock_write_queue: MagicMock
    ) -> None:
        """Test POST calls WriteQueue.enqueue_atomic."""
        response = client.post(
            "/api/pages",
            json={
                "slug": "new-page",
                "title": "New Page",
                "content": "# New Page\n\nNew content...",
                "tags": ["new"],
                "type": "summary",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["slug"] == "new-page"
        mock_write_queue.enqueue_atomic.assert_called_once()

    def test_create_page_returns_op_id(
        self, client: TestClient, mock_write_queue: MagicMock
    ) -> None:
        """Test create returns operation ID."""
        response = client.post(
            "/api/pages",
            json={
                "slug": "another-page",
                "title": "Another Page",
                "content": "Content",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "op_id" in data


class TestPageStatusFormat:
    """Tests for PageStatus response format."""

    def test_status_response_format(
        self, client: TestClient, mock_write_queue: MagicMock
    ) -> None:
        """Test PageStatus has required fields."""
        response = client.put(
            "/api/pages/test",
            json={"content": "Test"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "slug" in data
        assert "op_id" in data

"""Unit tests for Graph API endpoints.

Tests for GET /api/graph and GET /api/graph/{entity} per D-10~12:
- Graph endpoint returns nodes and edges
- Entity subgraph traversal works
- BFS/DFS traversal modes work correctly
- Depth parameter is passed to traverser
- Result format is valid for Cytoscape.js
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from saw.drivers.web.app import create_app
from saw.domain.entities import Entity, EntityRelation
from saw.engines.query.graph_traverse import GraphResult


@pytest.fixture
def mock_graph_traverse() -> MagicMock:
    """Create mock GraphTraverse with entities and relations."""
    graph = MagicMock()
    graph._entity_cache = {
        "uuid-1": Entity(
            uuid="uuid-1",
            name="Machine Learning",
            aliases=["ML"],
            entity_type="concept",
            description="Machine learning is a subset of AI",
        ),
        "uuid-2": Entity(
            uuid="uuid-2",
            name="Neural Networks",
            aliases=["NN"],
            entity_type="concept",
            description="Neural networks are computing systems inspired by neurons",
        ),
        "uuid-3": Entity(
            uuid="uuid-3",
            name="Deep Learning",
            aliases=["DL"],
            entity_type="concept",
            description="Deep learning uses multiple layers of neural networks",
        ),
    }
    # Mock NetworkX graph with edges
    mock_nx_graph = MagicMock()
    mock_nx_graph.edges.return_value = [
        ("uuid-1", "uuid-2", {"relation_type": "uses", "weight": 1.0}),
        ("uuid-2", "uuid-3", {"relation_type": "enables", "weight": 0.8}),
    ]
    graph._graph = mock_nx_graph

    # Mock traverse method
    graph.traverse.return_value = GraphResult(
        nodes=[
            Entity(
                uuid="uuid-1",
                name="Machine Learning",
                aliases=[],
                entity_type="concept",
                description="ML",
            ),
            Entity(
                uuid="uuid-2",
                name="Neural Networks",
                aliases=[],
                entity_type="concept",
                description="NN",
            ),
        ],
        edges=[
            EntityRelation(
                source_uuid="uuid-1",
                target_uuid="uuid-2",
                relation_type="uses",
                weight=1.0,
            ),
        ],
        paths=[["uuid-1", "uuid-2"]],
    )
    return graph


@pytest.fixture
def mock_query_engine(mock_graph_traverse: MagicMock) -> MagicMock:
    """Create mock QueryEngine with graph."""
    engine = MagicMock()
    engine._graph = mock_graph_traverse
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


class TestGetGraph:
    """Tests for GET /api/graph endpoint."""

    def test_get_graph_returns_nodes_and_edges(self, client: TestClient) -> None:
        """Test GET /api/graph returns 200 with GraphResponse."""
        response = client.get("/api/graph")

        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert "total_nodes" in data
        assert "total_edges" in data

    def test_get_graph_with_depth(self, client: TestClient) -> None:
        """Test depth parameter is accepted."""
        response = client.get("/api/graph?depth=3")

        assert response.status_code == 200

    def test_get_graph_with_max_nodes(self, client: TestClient) -> None:
        """Test max_nodes parameter limits results."""
        response = client.get("/api/graph?max_nodes=10")

        assert response.status_code == 200
        data = response.json()
        assert data["total_nodes"] <= 10

    def test_get_graph_type_filter(self, client: TestClient) -> None:
        """Test type filter parameter."""
        response = client.get("/api/graph?type=concept")

        assert response.status_code == 200

    def test_graph_node_format(self, client: TestClient) -> None:
        """Test GraphNode format includes id, label, type, confidence."""
        response = client.get("/api/graph")

        assert response.status_code == 200
        data = response.json()
        if data["nodes"]:
            node = data["nodes"][0]
            assert "id" in node
            assert "label" in node
            assert "type" in node
            assert "confidence" in node

    def test_graph_edge_format(self, client: TestClient) -> None:
        """Test GraphEdge format includes id, source, target, type, weight."""
        response = client.get("/api/graph")

        assert response.status_code == 200
        data = response.json()
        if data["edges"]:
            edge = data["edges"][0]
            assert "id" in edge
            assert "source" in edge
            assert "target" in edge
            assert "type" in edge
            assert "weight" in edge


class TestGetEntitySubgraph:
    """Tests for GET /api/graph/{entity} endpoint."""

    def test_get_entity_subgraph_returns_subgraph(
        self, client: TestClient, mock_graph_traverse: MagicMock
    ) -> None:
        """Test GET /api/graph/{entity} returns entity subgraph."""
        response = client.get("/api/graph/Machine Learning")

        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) > 0
        mock_graph_traverse.traverse.assert_called_once()

    def test_get_entity_subgraph_not_found(
        self, client: TestClient, mock_graph_traverse: MagicMock
    ) -> None:
        """Test non-existent entity returns 404."""
        mock_graph_traverse.traverse.return_value = GraphResult(
            nodes=[], edges=[], paths=[]
        )

        response = client.get("/api/graph/NonExistent")

        assert response.status_code == 404

    def test_entity_subgraph_depth_parameter(
        self, client: TestClient, mock_graph_traverse: MagicMock
    ) -> None:
        """Test depth parameter is passed to traverse."""
        response = client.get("/api/graph/Machine Learning?depth=3")

        assert response.status_code == 200
        call_kwargs = mock_graph_traverse.traverse.call_args[1]
        assert call_kwargs["max_depth"] == 3


class TestTraversalModes:
    """Tests for BFS/DFS traversal modes."""

    def test_traversal_mode_bfs(
        self, client: TestClient, mock_graph_traverse: MagicMock
    ) -> None:
        """Test BFS traversal mode is passed to traverse."""
        response = client.get("/api/graph/Machine Learning?mode=bfs")

        assert response.status_code == 200
        mock_graph_traverse.traverse.assert_called_once()
        call_kwargs = mock_graph_traverse.traverse.call_args[1]
        assert call_kwargs["mode"] == "bfs"

    def test_traversal_mode_dfs(
        self, client: TestClient, mock_graph_traverse: MagicMock
    ) -> None:
        """Test DFS traversal mode is passed to traverse."""
        response = client.get("/api/graph/Machine Learning?mode=dfs")

        assert response.status_code == 200
        mock_graph_traverse.traverse.assert_called_once()
        call_kwargs = mock_graph_traverse.traverse.call_args[1]
        assert call_kwargs["mode"] == "dfs"

    def test_default_traversal_mode_is_bfs(
        self, client: TestClient, mock_graph_traverse: MagicMock
    ) -> None:
        """Test default traversal mode is BFS."""
        response = client.get("/api/graph/Machine Learning")

        assert response.status_code == 200
        call_kwargs = mock_graph_traverse.traverse.call_args[1]
        assert call_kwargs["mode"] == "bfs"


class TestGraphResponseFormat:
    """Tests for GraphResponse format for Cytoscape.js compatibility."""

    def test_response_has_required_fields(self, client: TestClient) -> None:
        """Test GraphResponse has all required fields."""
        response = client.get("/api/graph")

        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert "total_nodes" in data
        assert "total_edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

    def test_node_has_description_optional(
        self, client: TestClient, mock_graph_traverse: MagicMock
    ) -> None:
        """Test GraphNode may have optional description."""
        response = client.get("/api/graph/Machine Learning")

        assert response.status_code == 200
        data = response.json()
        # Description is optional but should be string or null if present
        if data["nodes"]:
            node = data["nodes"][0]
            if "description" in node and node["description"] is not None:
                assert isinstance(node["description"], str)

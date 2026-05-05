"""Unit tests for impact analysis."""
import pytest
from saw.analysis import analyze_impact, NodeNotFoundError
from saw.analysis.types import ImpactNode, ImpactResult


class MockGraph:
    """Mock knowledge graph for testing."""

    def __init__(self):
        self.nodes = {}
        self.edges = []

    def add_node(self, uid: str, name: str, kind: str = 'function',
                 file_path: str = '/src/main.py', start_line: int = 1):
        self.nodes[uid] = {
            'uid': uid,
            'name': name,
            'kind': kind,
            'filePath': file_path,
            'startLine': start_line
        }

    def add_edge(self, source: str, target: str, edge_type: str,
                 confidence: float = 0.9):
        self.edges.append({
            'source': source,
            'target': target,
            'type': edge_type,
            'confidence': confidence
        })

    def get_node(self, uid: str):
        return self.nodes.get(uid)

    def find_nodes_by_name(self, name: str) -> list:
        return [n for n in self.nodes.values() if n['name'] == name]

    def get_incoming_edges(self, uid: str, types: list = None) -> list:
        types = types or ['CALLS', 'IMPORTS', 'EXTENDS', 'IMPLEMENTS']
        return [e for e in self.edges
                if e['target'] == uid and e['type'] in types]

    def get_outgoing_edges(self, uid: str, types: list = None) -> list:
        types = types or ['CALLS', 'IMPORTS', 'EXTENDS', 'IMPLEMENTS']
        return [e for e in self.edges
                if e['source'] == uid and e['type'] in types]


class TestImpactAnalysis:
    """Tests for impact analysis."""

    def test_simple_upstream(self):
        """Test upstream analysis finds dependents."""
        graph = MockGraph()
        graph.add_node('svc', 'UserService', 'class')
        graph.add_node('login', 'handleLogin', 'function')
        graph.add_node('register', 'handleRegister', 'function')

        # login and register depend on UserService
        graph.add_edge('login', 'svc', 'IMPORTS', 0.9)
        graph.add_edge('register', 'svc', 'IMPORTS', 0.9)

        result = analyze_impact(graph, 'UserService', direction='upstream')

        assert result['target'] == 'UserService'
        assert result['direction'] == 'upstream'
        assert len(result['impacts']) == 2

        # Check depth 1 are WILL_BREAK
        depth_1 = [i for i in result['impacts'] if i['depth'] == 1]
        assert len(depth_1) == 2
        for i in depth_1:
            assert i['risk_level'] == 'WILL_BREAK'

    def test_simple_downstream(self):
        """Test downstream analysis finds dependencies."""
        graph = MockGraph()
        graph.add_node('svc', 'UserService', 'class')
        graph.add_node('db', 'Database', 'class')
        graph.add_node('auth', 'AuthService', 'class')

        # UserService depends on Database and AuthService
        graph.add_edge('svc', 'db', 'IMPORTS', 0.9)
        graph.add_edge('svc', 'auth', 'IMPORTS', 0.85)

        result = analyze_impact(graph, 'UserService', direction='downstream')

        assert result['direction'] == 'downstream'
        assert len(result['impacts']) == 2

        names = [i['name'] for i in result['impacts']]
        assert 'Database' in names
        assert 'AuthService' in names

    def test_max_depth_limit(self):
        """Test max_depth limits traversal."""
        graph = MockGraph()
        graph.add_node('a', 'A', 'class')
        graph.add_node('b', 'B', 'class')
        graph.add_node('c', 'C', 'class')
        graph.add_node('d', 'D', 'class')

        # Chain: d -> c -> b -> a
        graph.add_edge('b', 'a', 'IMPORTS', 0.9)
        graph.add_edge('c', 'b', 'IMPORTS', 0.9)
        graph.add_edge('d', 'c', 'IMPORTS', 0.9)

        result = analyze_impact(graph, 'A', direction='upstream', max_depth=2)

        max_depth = max([i['depth'] for i in result['impacts']], default=0)
        assert max_depth <= 2

    def test_confidence_filter(self):
        """Test min_confidence filters low confidence edges."""
        graph = MockGraph()
        graph.add_node('svc', 'UserService', 'class')
        graph.add_node('high', 'HighConf', 'function')
        graph.add_node('low', 'LowConf', 'function')

        graph.add_edge('high', 'svc', 'IMPORTS', 0.9)
        graph.add_edge('low', 'svc', 'IMPORTS', 0.3)  # Low confidence

        result = analyze_impact(graph, 'UserService', min_confidence=0.8)

        names = [i['name'] for i in result['impacts']]
        assert 'HighConf' in names
        assert 'LowConf' not in names

    def test_node_not_found(self):
        """Test NodeNotFoundError on missing node."""
        graph = MockGraph()
        graph.add_node('exists', 'Exists', 'class')

        with pytest.raises(NodeNotFoundError) as exc_info:
            analyze_impact(graph, 'NonExistent')

        assert 'NonExistent' in str(exc_info.value)

    def test_relation_type_filter(self):
        """Test relation_types filter."""
        graph = MockGraph()
        graph.add_node('svc', 'UserService', 'class')
        graph.add_node('caller', 'handleLogin', 'function')
        graph.add_node('extender', 'AdminService', 'class')

        graph.add_edge('caller', 'svc', 'CALLS', 0.9)
        graph.add_edge('extender', 'svc', 'EXTENDS', 0.9)

        result = analyze_impact(graph, 'UserService',
                                 relation_types=['CALLS'])

        names = [i['name'] for i in result['impacts']]
        assert 'handleLogin' in names
        assert 'AdminService' not in names

    def test_summary_statistics(self):
        """Test summary includes correct counts."""
        graph = MockGraph()
        graph.add_node('target', 'Target', 'class')

        # Add nodes at different depths
        for i in range(3):
            graph.add_node(f'depth1_{i}', f'Depth1_{i}', 'function')
            graph.add_edge(f'depth1_{i}', 'target', 'IMPORTS', 0.9)

        for i in range(2):
            graph.add_node(f'depth2_{i}', f'Depth2_{i}', 'function')
            graph.add_edge(f'depth2_{i}', 'depth1_0', 'IMPORTS', 0.9)

        result = analyze_impact(graph, 'Target', max_depth=3)

        summary = result['summary']
        assert summary['depth_1_count'] == 3
        assert summary['depth_2_count'] == 2
        assert summary['high_risk_count'] == 3  # depth 1
        assert summary['total_affected'] == 5

    def test_test_filtering(self):
        """Test test file filtering."""
        graph = MockGraph()
        graph.add_node('svc', 'UserService', 'class')
        graph.add_node('test', 'TestUserService', 'function',
                       file_path='/tests/test_user.py')
        graph.add_node('real', 'RealCaller', 'function')

        graph.add_edge('test', 'svc', 'IMPORTS', 0.9)
        graph.add_edge('real', 'svc', 'IMPORTS', 0.9)

        # Without tests
        result = analyze_impact(graph, 'svc', include_tests=False)
        names = [i['name'] for i in result['impacts']]
        assert 'RealCaller' in names
        assert 'TestUserService' not in names

        # With tests
        result = analyze_impact(graph, 'svc', include_tests=True)
        names = [i['name'] for i in result['impacts']]
        assert 'TestUserService' in names

    def test_execution_time_measured(self):
        """Test execution time is measured."""
        graph = MockGraph()
        graph.add_node('svc', 'UserService', 'class')

        result = analyze_impact(graph, 'UserService')

        assert 'execution_time_ms' in result
        assert result['execution_time_ms'] >= 0
"""Query engine package initialization."""
from __future__ import annotations

from saw.engines.query.search import FTS5Search, SearchResult
from saw.engines.query.tree_mode import SectionPath, TreeModeSearch
from saw.engines.query.graph_traverse import GraphTraverse, GraphResult
from saw.engines.query.compare import CompareEngine, ComparisonResult
from saw.engines.query.compiler import ContextCompiler, CompiledContext
from saw.engines.query.engine import QueryEngine, QueryResult

__all__ = [
    "FTS5Search",
    "SearchResult",
    "TreeModeSearch",
    "SectionPath",
    "GraphTraverse",
    "GraphResult",
    "CompareEngine",
    "ComparisonResult",
    "ContextCompiler",
    "CompiledContext",
    "QueryEngine",
    "QueryResult",
]
"""MCP tools package.

Provides tool registration for MCP server.

Per 02-03 Task 2: 23 tools covering all operations.
"""

# Import all tool modules to register tools with FastMCP
# Tools are registered via @mcp.tool decorators in each module
from saw.drivers.mcp.tools import ingest, query, govern, learn, collaborate

__all__ = [
    "register_all_tools",
    "init_all_tools",
    "ingest",
    "query",
    "govern",
    "learn",
    "collaborate",
]


def register_all_tools() -> None:
    """Ensure all tool modules are imported (tools auto-register via decorators).

    Tools are registered when their modules are imported due to @mcp.tool decorators.
    """
    # Import ensures registration
    pass


def init_all_tools(
    pipeline=None,
    query_engine=None,
    search=None,
    compiler=None,
    graph=None,
    tree_mode=None,
    governor=None,
    detector=None,
    blast_radius=None,
    audit=None,
    learn_engine=None,
) -> None:
    """Initialize all tool modules with their engine references.

    Args:
        pipeline: IngestPipeline for ingest tools.
        query_engine: QueryEngine for query tools.
        search: FTS5Search for search tools.
        compiler: ContextCompiler for compile tools.
        graph: GraphTraverse for graph tools.
        tree_mode: TreeModeSearch for tree search tools.
        governor: Governor for govern tools.
        detector: ContradictionDetector for conflicts tools.
        blast_radius: BlastRadiusAnalyzer for blast radius tools.
        audit: AuditTrail for audit tools.
        learn_engine: LearnEngine for learn/collaborate tools.
    """
    from saw.drivers.mcp.tools.ingest import init_ingest_tools
    from saw.drivers.mcp.tools.query import init_query_tools
    from saw.drivers.mcp.tools.govern import init_govern_tools
    from saw.drivers.mcp.tools.learn import init_learn_tools
    from saw.drivers.mcp.tools.collaborate import init_collaborate_tools

    init_ingest_tools(pipeline)
    init_query_tools(query_engine, search, compiler, graph, tree_mode)
    init_govern_tools(governor, detector, blast_radius, audit)
    init_learn_tools(learn_engine)
    init_collaborate_tools(learn_engine)
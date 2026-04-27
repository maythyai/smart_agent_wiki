"""MCP tools for query operations.

Per 02-03 Task 2: Query tools (7 tools: saw_query, saw_search, saw_tree_search,
saw_graph, saw_compare, saw_compile, saw_coverage).
"""
from __future__ import annotations

from typing import Any

from saw.drivers.mcp.server import mcp

# Global engine references (set during initialization)
_query_engine = None
_search = None
_compiler = None
_graph = None
_tree_mode = None


def init_query_tools(
    query_engine,
    search,
    compiler,
    graph,
    tree_mode,
) -> None:
    """Initialize query tools with engine references.

    Args:
        query_engine: QueryEngine instance.
        search: FTS5Search instance.
        compiler: ContextCompiler instance.
        graph: GraphTraverse instance.
        tree_mode: TreeModeSearch instance.
    """
    global _query_engine, _search, _compiler, _graph, _tree_mode
    _query_engine = query_engine
    _search = search
    _compiler = compiler
    _graph = graph
    _tree_mode = tree_mode


@mcp.tool
async def saw_query(
    question: str,
    mode: str = "auto",
    depth: int = 3,
) -> dict[str, Any]:
    """Query the knowledge base in natural language.

    Per PITFALLS.md: Backward-compatible parameter handling (new params have defaults).

    Args:
        question: Natural language question to answer.
        mode: Query mode: "auto", "search", "graph", "compare", "tree".
        depth: Answer depth (1=title, 2=summary, 3=conclusions, 4=full).

    Returns:
        Query result with answer, sources, coverage, and meta.
    """
    result = {
        "question": question,
        "answer": "",
        "mode": mode,
        "sources": [],
        "coverage": 0.0,
        "depth": depth,
        "version": "1.0.0",
    }

    if _query_engine is None:
        result["answer"] = "Query engine not initialized"
        return result

    try:
        query_result = _query_engine.query(question, depth=depth, mode=mode)
        result["answer"] = query_result.answer
        result["sources"] = query_result.sources
        result["coverage"] = query_result.coverage
        result["mode"] = query_result.mode
        result["meta"] = query_result.meta
    except Exception as e:
        result["answer"] = f"Query error: {e}"

    return result


@mcp.tool
async def saw_search(keywords: str, limit: int = 10) -> list[dict]:
    """Full-text search using FTS5/BM25.

    Args:
        keywords: Keywords to search for.
        limit: Maximum number of results.

    Returns:
        List of search results with claim_uuid, content, score.
    """
    results = []

    if _search is None:
        return [{"error": "Search not initialized"}]

    try:
        search_result = _search.search(keywords, limit=limit)
        for uuid, content, score in zip(
            search_result.claim_uuids,
            search_result.contents,
            search_result.scores,
        ):
            results.append({
                "claim_uuid": uuid,
                "content": content[:200] + "..." if len(content) > 200 else content,
                "score": score,
                "version": "1.0.0",
            })
    except Exception as e:
        results = [{"error": str(e)}]

    return results


@mcp.tool
async def saw_tree_search(anchor: str, depth: int = 3) -> list[dict]:
    """Structure-aware tree mode search.

    Args:
        anchor: Anchor point for tree traversal.
        depth: Depth of tree traversal.

    Returns:
        List of section paths with claims.
    """
    results = []

    if _tree_mode is None:
        return [{"error": "Tree mode not initialized"}]

    try:
        section_paths = _tree_mode.search(anchor, limit=depth * 5)
        for path in section_paths:
            results.append({
                "path": " > ".join(path.path) if path.path else "root",
                "claims_count": len(path.claims),
                "claims": [c.uuid for c in path.claims[:5]],
                "version": "1.0.0",
            })
    except Exception as e:
        results = [{"error": str(e)}]

    return results


@mcp.tool
async def saw_graph(entity: str, depth: int = 2) -> dict:
    """Query knowledge graph for entity relationships.

    Args:
        entity: Entity name to start graph traversal.
        depth: Traversal depth.

    Returns:
        Graph data with nodes and edges.
    """
    result = {
        "entity": entity,
        "nodes": [],
        "edges": [],
        "version": "1.0.0",
    }

    if _graph is None:
        result["error"] = "Graph not initialized"
        return result

    try:
        graph_result = _graph.traverse(entity, mode="bfs", max_depth=depth)
        result["nodes"] = [
            {"uuid": n.uuid, "name": n.name, "type": n.entity_type}
            for n in graph_result.nodes
        ]
        result["edges"] = [
            {
                "source": e.source_uuid,
                "target": e.target_uuid,
                "relation": e.relation_type,
            }
            for e in graph_result.edges
        ]
    except Exception as e:
        result["error"] = str(e)

    return result


@mcp.tool
async def saw_compare(page_a: str, page_b: str) -> dict:
    """Compare two wiki pages for similarities and differences.

    Args:
        page_a: First page name.
        page_b: Second page name.

    Returns:
        Comparison result with similarity score and unique claims.
    """
    result = {
        "page_a": page_a,
        "page_b": page_b,
        "similarity": 0.0,
        "shared_claims": [],
        "unique_claims_a": [],
        "unique_claims_b": [],
        "version": "1.0.0",
    }

    if _query_engine is None:
        result["error"] = "Query engine not initialized"
        return result

    try:
        # Use compare mode through query engine
        comp_result = _query_engine._compare.compare([page_a, page_b])
        result["similarity"] = comp_result.similarity
        result["shared_claims"] = [
            {"uuid": c.uuid, "content": c.content[:100]}
            for c in comp_result.shared_claims[:10]
        ]
        result["unique_claims_a"] = [
            {"uuid": c.uuid, "content": c.content[:100]}
            for c in comp_result.unique_claims.get(page_a, [])[:5]
        ]
        result["unique_claims_b"] = [
            {"uuid": c.uuid, "content": c.content[:100]}
            for c in comp_result.unique_claims.get(page_b, [])[:5]
        ]
    except Exception as e:
        result["error"] = str(e)

    return result


@mcp.tool
async def saw_compile(query: str, budget: int = 8000) -> dict:
    """Compile context for a query within token budget.

    Args:
        query: Query to compile context for.
        budget: Token budget for context.

    Returns:
        Compiled context with token count and sources.
    """
    result = {
        "query": query,
        "content": "",
        "token_count": 0,
        "sources": [],
        "coverage": 0.0,
        "version": "1.0.0",
    }

    if _compiler is None:
        result["error"] = "Compiler not initialized"
        return result

    try:
        compiled = _compiler.compile(query, token_budget=budget)
        result["content"] = compiled.content
        result["token_count"] = compiled.token_count
        result["sources"] = compiled.sources
        result["coverage"] = compiled.coverage
    except Exception as e:
        result["error"] = str(e)

    return result


@mcp.tool
async def saw_coverage(query: str) -> float:
    """Calculate knowledge base coverage for a query.

    Args:
        query: Query to calculate coverage for.

    Returns:
        Coverage percentage (0.0 to 100.0).
    """
    if _compiler is None:
        return 0.0

    try:
        compiled = _compiler.compile(query, token_budget=4000)
        return compiled.coverage
    except Exception:
        return 0.0
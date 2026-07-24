"""MCP tools for Wiki compile layer, concept graph, feedback, and code wiki.

Exposes the compile engine capabilities as MCP tools for AI agent consumption.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from saw.drivers.mcp.server import mcp

# Module-level engine references (set by init_compile_tools)
_compile_engine = None
_archiver = None
_linter = None
_concept_graph = None
_feedback_engine = None
_code_wiki_engine = None


def init_compile_tools(
    compile_engine,
    archiver,
    linter,
    concept_graph,
    feedback_engine,
    code_wiki_engine,
) -> None:
    """Initialize compile tool engine references."""
    global _compile_engine, _archiver, _linter, _concept_graph, _feedback_engine, _code_wiki_engine
    _compile_engine = compile_engine
    _archiver = archiver
    _linter = linter
    _concept_graph = concept_graph
    _feedback_engine = feedback_engine
    _code_wiki_engine = code_wiki_engine


# ─── Compile tools ─────────────────────────────────────────────────────


@mcp.tool
async def saw_wiki_compile(mode: str = "incremental", sources: Optional[list[str]] = None) -> dict:
    """Compile raw documents into structured Wiki layer.

    Args:
        mode: "full" for complete recompilation, "incremental" for changes only
        sources: Optional list of specific source paths to compile
    """
    if not _compile_engine:
        return {"error": "Compile engine not initialized", "version": "1.0.0"}

    if mode == "full":
        result = await _compile_engine.compile_full()
    else:
        result = await _compile_engine.compile_incremental(sources or [])

    return {
        "pages_created": result.pages_created,
        "pages_updated": result.pages_updated,
        "pages_unchanged": result.pages_unchanged,
        "contradictions": result.contradictions_found,
        "duration_seconds": result.duration_seconds,
        "version": "1.0.0",
    }


@mcp.tool
async def saw_wiki_index() -> dict:
    """Read the Wiki compile layer index (index.md structure)."""
    if not _compile_engine:
        return {"error": "Compile engine not initialized", "version": "1.0.0"}

    index = await _compile_engine.get_index()
    return {
        "total_pages": index.total_pages,
        "topics": {
            topic: [
                {"filename": e.filename, "title": e.title, "summary": e.summary, "archived": e.is_archived}
                for e in entries
            ]
            for topic, entries in index.topics.items()
        },
        "version": "1.0.0",
    }


@mcp.tool
async def saw_wiki_page(filename: str) -> dict:
    """Read a specific Wiki compile layer page.

    Args:
        filename: Page path relative to _wiki/ (e.g. "concepts/event-sourcing.md")
    """
    if not _compile_engine:
        return {"error": "Compile engine not initialized", "version": "1.0.0"}

    page = _compile_engine.read_page(filename)
    if not page:
        return {"error": f"Page not found: {filename}", "version": "1.0.0"}

    return {
        "filename": page.filename,
        "title": page.title,
        "content": page.content,
        "type": page.metadata.type.value,
        "confidence": page.metadata.confidence.value,
        "sources": [
            {"pageId": s.page_id, "title": s.title, "sections": list(s.sections)}
            for s in page.metadata.sources
        ],
        "see_also": page.metadata.see_also,
        "version": "1.0.0",
    }


@mcp.tool
async def saw_wiki_log(limit: int = 10) -> dict:
    """Read recent compile log entries.

    Args:
        limit: Maximum number of entries to return
    """
    if not _compile_engine:
        return {"error": "Compile engine not initialized", "version": "1.0.0"}

    entries = _compile_engine.get_log(limit)
    return {
        "entries": [
            {
                "timestamp": e.timestamp.isoformat(),
                "action": e.action,
                "summary": e.summary,
                "pages_affected": e.pages_affected,
            }
            for e in entries
        ],
        "version": "1.0.0",
    }


# ─── Archive tools ─────────────────────────────────────────────────────


@mcp.tool
async def saw_archive(query: str, answer: str, referenced_pages: list[str]) -> dict:
    """Archive a query result as a Wiki page (type=archive).

    Args:
        query: The original query question
        answer: The generated answer (Markdown)
        referenced_pages: List of wiki page paths that were referenced
    """
    if not _archiver:
        return {"error": "Archiver not initialized", "version": "1.0.0"}

    page = await _archiver.archive(query, answer, referenced_pages)
    return {
        "filename": page.filename,
        "title": page.title,
        "sources_count": len(page.metadata.sources),
        "version": "1.0.0",
    }


@mcp.tool
async def saw_archive_suggest(query: str, answer: str, referenced_pages: list[str]) -> dict:
    """Check if a query result is worth archiving.

    Args:
        query: The query question
        answer: The answer content
        referenced_pages: Referenced wiki pages
    """
    if not _archiver:
        return {"error": "Archiver not initialized", "version": "1.0.0"}

    should_archive = await _archiver.suggest_archive(query, answer, referenced_pages)
    return {"should_archive": should_archive, "version": "1.0.0"}


# ─── Lint tools ────────────────────────────────────────────────────────


@mcp.tool
async def saw_wiki_lint(auto_fix: bool = True, category: Optional[str] = None) -> dict:
    """Wiki health check with tiered governance.

    Args:
        auto_fix: Whether to automatically fix fixable issues
        category: Optional specific category to check
    """
    if not _linter:
        return {"error": "Linter not initialized", "version": "1.0.0"}

    report = await _linter.lint(auto_fix=auto_fix)
    return report.to_dict() | {"version": "1.0.0"}


# ─── Concept graph tools ──────────────────────────────────────────────


@mcp.tool
async def saw_concept_list() -> dict:
    """List all concepts in the knowledge graph."""
    if not _concept_graph:
        return {"error": "Concept graph not initialized", "version": "1.0.0"}

    concepts = _concept_graph.list_concepts()
    return {
        "concepts": [
            {
                "name": c.name,
                "stability": c.stability.value,
                "definition": c.definition,
                "wiki_page": c.wiki_page,
            }
            for c in concepts
        ],
        "total": len(concepts),
        "version": "1.0.0",
    }


@mcp.tool
async def saw_concept_view(name: str) -> dict:
    """View concept details with typed relations.

    Args:
        name: Concept name to look up
    """
    if not _concept_graph:
        return {"error": "Concept graph not initialized", "version": "1.0.0"}

    node = _concept_graph.get_concept(name)
    if not node:
        return {"error": f"Concept not found: {name}", "version": "1.0.0"}

    return {
        "name": node.name,
        "definition": node.definition,
        "stability": node.stability.value,
        "wiki_page": node.wiki_page,
        "code_entities": node.code_entities,
        "relations_out": [
            {"target": r.target, "type": r.relation_type.value, "confidence": r.confidence}
            for r in node.relations_out
        ],
        "relations_in": [
            {"source": r.source, "type": r.relation_type.value, "confidence": r.confidence}
            for r in node.relations_in
        ],
        "version": "1.0.0",
    }


@mcp.tool
async def saw_concept_relate(source: str, target: str, relation: str, action: str = "add") -> dict:
    """Add or remove a typed relation between concepts.

    Args:
        source: Source concept name
        target: Target concept name
        relation: Relation type (depends_on, implements, is_part_of, related_to, etc.)
        action: "add" or "remove"
    """
    if not _concept_graph:
        return {"error": "Concept graph not initialized", "version": "1.0.0"}

    from saw.domain.concept import ConceptRelation, ConceptRelationType

    try:
        rel_type = ConceptRelationType(relation)
    except ValueError:
        valid = [t.value for t in ConceptRelationType]
        return {"error": f"Invalid relation type. Valid: {valid}", "version": "1.0.0"}

    if action == "remove":
        ok = _concept_graph.remove_relation(source, target, rel_type)
        return {"removed": ok, "version": "1.0.0"}
    else:
        rel = ConceptRelation(source=source, target=target, relation_type=rel_type)
        ok = _concept_graph.add_relation(rel)
        return {"added": ok, "version": "1.0.0"}


@mcp.tool
async def saw_graph_overview() -> dict:
    """Get knowledge graph global topology overview."""
    if not _concept_graph:
        return {"error": "Concept graph not initialized", "version": "1.0.0"}

    overview = _concept_graph.get_overview()
    return {
        "total_concepts": overview.total_concepts,
        "total_relations": overview.total_relations,
        "topics": overview.topics,
        "relation_types": overview.relation_type_distribution,
        "stability": overview.stability_distribution,
        "densest_concepts": overview.densest_concepts,
        "version": "1.0.0",
    }


@mcp.tool
async def saw_navigate(start: str, relations: Optional[list[str]] = None, depth: int = 2) -> dict:
    """Navigate the concept graph from a starting node.

    Args:
        start: Starting concept name
        relations: Optional list of relation types to follow
        depth: Maximum navigation depth
    """
    if not _concept_graph:
        return {"error": "Concept graph not initialized", "version": "1.0.0"}

    from saw.domain.concept import ConceptRelationType

    rel_types = None
    if relations:
        rel_types = []
        for r in relations:
            try:
                rel_types.append(ConceptRelationType(r))
            except ValueError:
                pass

    result = _concept_graph.navigate(start, rel_types, depth)
    return {
        "start": result.start,
        "nodes_visited": [n.name for n in result.nodes_visited],
        "relations_traversed": [
            {"source": r.source, "target": r.target, "type": r.relation_type.value}
            for r in result.relations_traversed
        ],
        "depth_reached": result.depth_reached,
        "version": "1.0.0",
    }


# ─── Feedback tools ────────────────────────────────────────────────────


@mcp.tool
async def saw_issue_create(
    type: str, title: str, description: str, affected_pages: list[str]
) -> dict:
    """Create a knowledge issue (challenge, request, or suggestion).

    Args:
        type: Issue type - "challenge", "request", or "suggestion"
        title: Issue title
        description: Detailed description
        affected_pages: List of affected wiki page paths
    """
    if not _feedback_engine:
        return {"error": "Feedback engine not initialized", "version": "1.0.0"}

    from saw.domain.feedback import IssueType

    try:
        issue_type = IssueType(type)
    except ValueError:
        return {"error": "Invalid type. Valid: challenge, request, suggestion", "version": "1.0.0"}

    issue = _feedback_engine.create_issue(issue_type, title, description, affected_pages, "mcp-agent")
    return {"id": issue.id, "type": issue.type.value, "title": issue.title, "version": "1.0.0"}


@mcp.tool
async def saw_issue_list(status: Optional[str] = None, type: Optional[str] = None) -> dict:
    """List knowledge issues.

    Args:
        status: Optional filter by status (open, discussing, resolved, wontfix)
        type: Optional filter by type (challenge, request, suggestion)
    """
    if not _feedback_engine:
        return {"error": "Feedback engine not initialized", "version": "1.0.0"}

    from saw.domain.feedback import IssueStatus, IssueType

    filter_status = IssueStatus(status) if status else None
    filter_type = IssueType(type) if type else None
    issues = _feedback_engine.list_issues(status=filter_status, issue_type=filter_type)

    return {
        "issues": [
            {
                "id": i.id,
                "type": i.type.value,
                "title": i.title,
                "status": i.status.value,
                "affected_pages": i.affected_pages,
                "reporter": i.reporter,
            }
            for i in issues
        ],
        "total": len(issues),
        "version": "1.0.0",
    }


@mcp.tool
async def saw_cr_create(
    title: str, target_page: str, proposed_content: str, linked_issue: Optional[str] = None
) -> dict:
    """Create a knowledge change request.

    Args:
        title: CR title
        target_page: Target wiki page path
        proposed_content: Proposed new content
        linked_issue: Optional linked issue ID
    """
    if not _feedback_engine:
        return {"error": "Feedback engine not initialized", "version": "1.0.0"}

    cr = _feedback_engine.create_cr(
        title=title,
        target_page=target_page,
        proposed_content=proposed_content,
        creator="mcp-agent",
        linked_issue=linked_issue,
    )
    return {"id": cr.id, "title": cr.title, "target_page": cr.target_page, "version": "1.0.0"}


@mcp.tool
async def saw_cr_review(cr_id: str, approved: bool, comment: str = "") -> dict:
    """Review a change request (approve or reject).

    Args:
        cr_id: Change request ID
        approved: True to approve, False to reject
        comment: Review comment
    """
    if not _feedback_engine:
        return {"error": "Feedback engine not initialized", "version": "1.0.0"}

    cr = _feedback_engine.review_cr(cr_id, reviewer="mcp-reviewer", approved=approved, comment=comment)
    if not cr:
        return {"error": f"CR not found: {cr_id}", "version": "1.0.0"}

    return {"id": cr.id, "status": cr.status.value, "reviewer": cr.reviewer, "version": "1.0.0"}


# ─── Code Wiki tools ──────────────────────────────────────────────────


@mcp.tool
async def saw_code_wiki_generate(
    repo_path: str, skip_if_exists: bool = False, branch: str = "main"
) -> dict:
    """Generate or update Code Wiki for a repository.

    Args:
        repo_path: Path to the code repository
        skip_if_exists: Skip modules that already have documentation
        branch: Git branch to analyze
    """
    if not _code_wiki_engine:
        return {"error": "Code Wiki engine not initialized", "version": "1.0.0"}

    from saw.domain.code_wiki import CodeWikiConfig

    config = CodeWikiConfig(repo_path=Path(repo_path), skip_if_exists=skip_if_exists, branch=branch)
    result = await _code_wiki_engine.generate(config)

    return {
        "pages_generated": result.pages_generated,
        "pages_updated": result.pages_updated,
        "pages_skipped": result.pages_skipped,
        "total_source_files": result.total_source_files,
        "duration_seconds": result.duration_seconds,
        "version": "1.0.0",
    }


@mcp.tool
async def saw_code_wiki_status(repo_path: str) -> dict:
    """Check Code Wiki status for a repository.

    Args:
        repo_path: Path to the code repository
    """
    if not _code_wiki_engine:
        return {"error": "Code Wiki engine not initialized", "version": "1.0.0"}

    from saw.domain.code_wiki import CodeWikiConfig

    config = CodeWikiConfig(repo_path=Path(repo_path))
    status = await _code_wiki_engine.status(config)

    return {
        "exists": status.exists,
        "pages_count": status.pages_count,
        "is_stale": status.is_stale,
        "last_commit": status.last_commit,
        "current_commit": status.current_commit,
        "version": "1.0.0",
    }

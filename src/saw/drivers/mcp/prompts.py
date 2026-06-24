"""MCP prompt templates for common knowledge operations.

Per MCP spec: Prompts are reusable prompt templates that AI clients can invoke.
"""
from __future__ import annotations

from typing import Any

from saw.drivers.mcp.server import mcp

# Global references (set during initialization)
_wiki_repo = None


def init_prompts(wiki_repo) -> None:
    """Initialize prompts with engine references.

    Args:
        wiki_repo: WikiRepository instance.
    """
    global _wiki_repo
    _wiki_repo = wiki_repo


@mcp.prompt
async def summarize_kb(topic: str = "") -> list[dict[str, Any]]:
    """Summarize the knowledge base or a specific topic.

    Args:
        topic: Optional topic to focus on. If empty, summarize entire KB.

    Returns:
        List of messages for the AI to process.
    """
    if not _wiki_repo:
        return [{"role": "user", "content": "Knowledge base is empty."}]

    pages = []
    for path in _wiki_repo.list_pages()[:50]:  # Limit to 50 pages
        page = _wiki_repo.read(path)
        if page:
            if not topic or topic.lower() in page.title.lower() or topic.lower() in page.content.lower():
                pages.append(f"## {page.title}\n{page.content[:300]}")

    context = "\n\n".join(pages) if pages else "No matching pages found."

    prompt_text = f"""You are analyzing a knowledge base. Based on the following pages, provide a concise summary{' of the topic: ' + topic if topic else ' of the entire knowledge base'}.

Pages:
{context}

Summary:"""

    return [{"role": "user", "content": prompt_text}]


@mcp.prompt
async def research_topic(topic: str) -> list[dict[str, Any]]:
    """Research a topic using the knowledge base.

    Args:
        topic: Topic to research.

    Returns:
        List of messages for the AI to process.
    """
    if not _wiki_repo:
        return [{"role": "user", "content": f"Research topic: {topic}. Knowledge base is empty."}]

    relevant = []
    topic_lower = topic.lower()

    for path in _wiki_repo.list_pages():
        page = _wiki_repo.read(path)
        if page and (topic_lower in page.title.lower() or topic_lower in page.content.lower()):
            relevant.append(f"### {page.title}\n{page.content[:400]}")

    context = "\n\n".join(relevant[:20]) if relevant else "No directly relevant pages found."

    prompt_text = f"""You are a research assistant. Based on the following knowledge base content about "{topic}", synthesize key insights and identify gaps.

Content:
{context}

Provide:
1. Key findings
2. Connections between concepts
3. Knowledge gaps
4. Suggested next steps"""

    return [{"role": "user", "content": prompt_text}]


@mcp.prompt
async def compare_entities(entity_a: str, entity_b: str) -> list[dict[str, Any]]:
    """Compare two entities from the knowledge base.

    Args:
        entity_a: First entity name or slug.
        entity_b: Second entity name or slug.

    Returns:
        List of messages for the AI to process.
    """
    if not _wiki_repo:
        return [{"role": "user", "content": "Knowledge base is empty."}]

    page_a = _wiki_repo.read(entity_a)
    page_b = _wiki_repo.read(entity_b)

    if not page_a or not page_b:
        return [{"role": "user", "content": f"Could not find both entities: {entity_a}, {entity_b}"}]

    prompt_text = f"""Compare these two entities:

## {page_a.title}
{page_a.content[:500]}

## {page_b.title}
{page_b.content[:500]}

Provide:
1. Similarities
2. Differences
3. Relationships
4. When to use each"""

    return [{"role": "user", "content": prompt_text}]


@mcp.prompt
async def find_gaps(topic: str) -> list[dict[str, Any]]:
    """Identify knowledge gaps in a topic area.

    Args:
        topic: Topic area to analyze.

    Returns:
        List of messages for the AI to process.
    """
    if not _wiki_repo:
        return [{"role": "user", "content": "Knowledge base is empty."}]

    pages = []
    topic_lower = topic.lower()

    for path in _wiki_repo.list_pages():
        page = _wiki_repo.read(path)
        if page and (topic_lower in page.title.lower() or topic_lower in page.content.lower()):
            pages.append(f"- {page.title}: {page.content[:150]}")

    context = "\n".join(pages) if pages else "No pages found for this topic."

    prompt_text = f"""Analyze the knowledge base for topic "{topic}" and identify gaps.

Existing pages:
{context}

Identify:
1. Missing subtopics
2. Incomplete coverage
3. Outdated information
4. Suggested new pages to create"""

    return [{"role": "user", "content": prompt_text}]


@mcp.prompt
async def daily_review() -> list[dict[str, Any]]:
    """Generate a daily review prompt using recent pages.

    Returns:
        List of messages for the AI to process.
    """
    if not _wiki_repo:
        return [{"role": "user", "content": "No pages to review."}]

    # Get last 10 pages (simplified - in production would use mtime)
    pages = []
    for path in _wiki_repo.list_pages()[-10:]:
        page = _wiki_repo.read(path)
        if page:
            pages.append(f"- **{page.title}** ({page.entity_type}): {page.content[:100]}")

    context = "\n".join(pages) if pages else "No recent pages."

    prompt_text = f"""Daily knowledge base review:

Recent pages:
{context}

Provide:
1. Summary of today's additions
2. Connections to existing knowledge
3. Action items or follow-ups
4. Suggested improvements"""

    return [{"role": "user", "content": prompt_text}]


@mcp.prompt
async def generate_report(topic: str, depth: str = "summary") -> list[dict[str, Any]]:
    """Generate a structured report on a topic.

    Args:
        topic: Topic for the report.
        depth: Report depth: "summary", "detailed", or "comprehensive".

    Returns:
        List of messages for the AI to process.
    """
    if not _wiki_repo:
        return [{"role": "user", "content": "Knowledge base is empty."}]

    relevant = []
    topic_lower = topic.lower()
    limit = {"summary": 10, "detailed": 20, "comprehensive": 50}.get(depth, 20)

    for path in _wiki_repo.list_pages():
        page = _wiki_repo.read(path)
        if page and (topic_lower in page.title.lower() or topic_lower in page.content.lower()):
            content_limit = {"summary": 200, "detailed": 400, "comprehensive": 800}.get(depth, 400)
            relevant.append(f"### {page.title}\n{page.content[:content_limit]}")

    context = "\n\n".join(relevant[:limit]) if relevant else "No relevant content found."

    prompt_text = f"""Generate a {depth} report on "{topic}".

Source material:
{context}

Report structure:
1. Executive Summary
2. Key Concepts
3. Detailed Analysis
4. Connections & Relationships
5. Conclusions
6. References (list source pages)"""

    return [{"role": "user", "content": prompt_text}]

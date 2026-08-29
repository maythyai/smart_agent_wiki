"""Query Engine orchestrator for search, NL query, graph, and compare modes.

Per D-15: Natural language query via LLM with layered answers.
Per D-13: BM25 + FTS5 search.
Per D-16: Graph traversal.
Per D-07 QUER-07: Comparison analysis.
"""
from __future__ import annotations

import logging
import re
import sqlite3
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from saw.adapters.llm.router import LLMRouter
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.engines.query.compare import CompareEngine
    from saw.engines.query.compiler import ContextCompiler
    from saw.engines.query.graph_traverse import GraphTraverse
    from saw.engines.query.search import FTS5Search
    from saw.engines.query.tree_mode import TreeModeSearch


@dataclass
class QueryResult:
    """Result from query engine."""
    answer: str
    layered_answer: dict[str, str] = field(default_factory=dict)
    sources: list[dict[str, Any]] = field(default_factory=list)
    related_pages: list[str] = field(default_factory=list)
    coverage: float = 0.0
    mode: str = "search"
    meta: dict[str, Any] = field(default_factory=dict)


class QueryEngine:
    """Orchestrator for all query modes.

    Per D-15: NL query with layered answer (L1-L4) and inline citations.
    """

    def __init__(
        self,
        search: FTS5Search,
        compiler: ContextCompiler,
        graph: GraphTraverse,
        compare_engine: CompareEngine,
        tree_mode: TreeModeSearch,
        llm: LLMRouter | None,
        claims_repo: SQLiteClaimsRepository,
        wiki_repo: WikiRepository,
        conn: sqlite3.Connection,
    ) -> None:
        """Initialize query engine.

        Args:
            search: FTS5 search service.
            compiler: Context compiler.
            graph: Graph traversal service.
            compare_engine: Comparison engine.
            tree_mode: Tree mode search.
            llm: LLM router (optional, None for offline mode).
            claims_repo: Claims repository.
            wiki_repo: Wiki repository.
            conn: SQLite connection.
        """
        self._search = search
        self._compiler = compiler
        self._graph = graph
        self._compare = compare_engine
        self._tree_mode = tree_mode
        self._llm = llm
        self._claims_repo = claims_repo
        self._wiki_repo = wiki_repo
        self._conn = conn

    def query(
        self,
        question: str,
        depth: int = 3,
        mode: str = "auto",
        token_budget: int = 4000,
        limit: int = 20,
        offset: int = 0,
    ) -> QueryResult:
        """Execute query in specified mode.

        Args:
            question: User question or query.
            depth: Answer depth (1=title, 2=summary, 3=conclusions, 4=full).
            mode: Query mode: "auto", "search", "graph", "compare", "tree".
            token_budget: Token budget for context compilation.

        Returns:
            QueryResult with answer and sources.
        """
        if not question or not question.strip():
            return QueryResult(answer="No question provided.", mode=mode)

        # Determine query path based on mode
        if mode == "auto":
            if self._llm is None:
                # No LLM available -> keyword search
                return self._keyword_search(question)
            else:
                # LLM available -> NL query
                return self._nl_query(question, depth, token_budget)
        elif mode == "search":
            return self._keyword_search(question, limit=limit, offset=offset)
        elif mode == "graph":
            return self._graph_query(question)
        elif mode == "compare":
            return self._compare_query(question)
        elif mode == "tree":
            return self._tree_query(question)
        else:
            return QueryResult(answer=f"Unknown mode: {mode}", mode=mode)

    def _nl_query(
        self, question: str, depth: int, token_budget: int
    ) -> QueryResult:
        """Natural language query via LLM.

        Per D-15: Compile context -> LLM generates layered answer
        with inline citations [^claim:uuid].

        Args:
            question: User question.
            depth: Answer depth.
            token_budget: Token budget.

        Returns:
            QueryResult with layered answer.
        """
        # Step 1: Compile context
        compiled = self._compiler.compile(question, token_budget)

        if not compiled.content.strip():
            return QueryResult(
                answer="No relevant context found for the question.",
                mode="nl_query",
                coverage=0.0,
            )

        # Step 2: Load system prompt
        system_prompt = self._get_query_prompt()

        # Step 3: Call LLM
        # F-QS-03: degrade gracefully — if the LLM call fails (rate limit,
        # network, provider error) fall back to keyword search instead of
        # surfacing a 500 to the user.
        try:
            raw_answer = self._llm.answer_query(compiled.content, question, system_prompt)
        except Exception as llm_exc:
            logger.warning(
                "NL query LLM call failed, falling back to keyword search: %s",
                llm_exc,
            )
            kw_result = self._keyword_search(question)
            kw_result.mode = "nl_query_fallback"
            kw_result.meta = {
                **(kw_result.meta or {}),
                "nl_fallback": True,
                "nl_error": str(llm_exc),
            }
            return kw_result

        # Step 4: Parse into layered answer
        layered = self._parse_layered_answer(raw_answer, depth)

        # Step 5: Extract citations
        citations = self._extract_citations(raw_answer)

        # Step 6: Resolve citations to sources
        sources = self._resolve_citations(citations, compiled.sources)

        return QueryResult(
            answer=raw_answer,
            layered_answer=layered,
            sources=sources,
            coverage=compiled.coverage,
            mode="nl_query",
            meta={
                "token_count": compiled.token_count,
                "model": self._llm._query_model if self._llm else None,
            },
        )

    def _keyword_search(self, question: str, limit: int = 20, offset: int = 0) -> QueryResult:
        """Keyword search via FTS5.

        Args:
            question: Search query.
            limit: Maximum number of results (FTS5 LIMIT).
            offset: Offset for pagination (FTS5 OFFSET).

        Returns:
            QueryResult with search results.
        """
        # F-QS-07: serve from the query cache before hitting FTS5.
        from saw.engines.query.cache import get_cache

        _cache = get_cache()
        _cached = _cache.get(question, {"limit": limit, "offset": offset, "mode": "search"})
        if _cached is not None:
            return _cached

        result = self._search.search(question, limit=limit, offset=offset)

        # Format results as answer
        answer_lines: list[str] = []
        answer_lines.append(f"Found {result.total} results for '{question}':\n")

        sources: list[dict] = []

        for i, (doc_id, content, score) in enumerate(
            zip(result.claim_uuids, result.contents, result.scores), 1
        ):
            claim = self._claims_repo.get_by_id(doc_id)
            if claim:
                answer_lines.append(f"{i}. {claim.content[:100]}...")
                sources.append({
                    "claim_uuid": doc_id,
                    "content": claim.content,
                    "confidence": claim.confidence.name.lower(),
                    "source_uuid": claim.source_uuid,
                    "page_number": claim.page_number,
                    "line_number": claim.line_number,
                    "score": score,
                    # F-QS-02: populate type/tags so the search route's
                    # type/tag filters can actually match.
                    "type": "claim",
                    "tags": list(claim.tags or []),
                })
                continue
            # doc_id is a wiki slug (FTS rows written by WikiIndexer), not a
            # claim UUID — surface the actual page so wiki-only content is
            # searchable instead of being silently dropped.
            page = self._wiki_repo.read(doc_id) if self._wiki_repo else None
            if page is not None:
                answer_lines.append(f"{i}. [[{doc_id}]] {page.title}")
                sources.append({
                    "page_slug": doc_id,
                    "title": page.title,
                    "content": page.content,
                    "score": score,
                    # F-QS-02: populate type/tags from the page so filters match.
                    "type": page.entity_type,
                    "tags": list(getattr(page, "tags", []) or []),
                })
            else:
                answer_lines.append(f"{i}. {(content or '')[:100]}...")
                sources.append({
                    "doc_id": doc_id,
                    "content": (content or "")[:200],
                    "score": score,
                    "type": "unknown",
                    "tags": [],
                })

        _qr = QueryResult(
            answer="\n".join(answer_lines),
            sources=sources,
            coverage=100.0,  # All search results included
            mode="search",
            meta={"total": result.total, "limit": limit, "offset": offset},
        )
        # F-QS-07: cache the result (TTL-bounded; cleared on content writes).
        _cache.set(question, {"limit": limit, "offset": offset, "mode": "search"}, _qr)
        return _qr

    def _graph_query(self, question: str) -> QueryResult:
        """Graph traversal query.

        Args:
            question: Entity names to traverse.

        Returns:
            QueryResult with graph data.
        """
        # Extract entity names from question
        # Simple approach: split and look up each word
        words = question.split()
        entity_name = None

        for word in words:
            # Try to find entity
            result = self._graph.traverse(word, mode="bfs", max_depth=2)
            if result.nodes:
                entity_name = word
                break

        if entity_name is None:
            return QueryResult(
                answer=f"No entities found for '{question}'",
                mode="graph",
            )

        # Traverse from found entity
        graph_result = self._graph.traverse(entity_name, mode="bfs", max_depth=3)

        # Format as answer
        answer_lines: list[str] = []
        answer_lines.append(f"Graph traversal from '{entity_name}':")
        answer_lines.append(f"Found {len(graph_result.nodes)} entities:")
        for node in graph_result.nodes:
            answer_lines.append(f"  - {node.name} ({node.entity_type})")
        answer_lines.append(f"Found {len(graph_result.edges)} relations:")
        for edge in graph_result.edges:
            answer_lines.append(
                f"  - {edge.source_uuid} -> {edge.relation_type} -> {edge.target_uuid}"
            )

        sources: list[dict] = []
        for node in graph_result.nodes:
            sources.append({
                "entity_uuid": node.uuid,
                "entity_name": node.name,
                "entity_type": node.entity_type,
            })

        return QueryResult(
            answer="\n".join(answer_lines),
            sources=sources,
            mode="graph",
        )

    def _compare_query(self, question: str) -> QueryResult:
        """Comparison analysis query.

        Args:
            question: Page names to compare (comma-separated or natural language).

        Returns:
            QueryResult with comparison.
        """
        # Parse page names from question
        # Simple approach: comma-separated or quoted strings
        page_names: list[str] = []

        # Try comma-separated
        if "," in question:
            page_names = [p.strip() for p in question.split(",")]
        else:
            # Try to extract quoted strings
            quotes = re.findall(r'"([^"]+)"', question)
            if quotes:
                page_names = quotes
            else:
                # Use entire question as single page name
                page_names = [question.strip()]

        if len(page_names) < 2:
            return QueryResult(
                answer=f"Need at least 2 pages to compare. Found: {page_names}",
                mode="compare",
            )

        # Execute comparison
        comparison = self._compare.compare(page_names)

        # Format as answer
        answer_lines: list[str] = []
        answer_lines.append(f"Comparison of {comparison.pages}:")
        answer_lines.append(f"Similarity: {comparison.similarity:.1%}")
        answer_lines.append(f"Shared claims: {len(comparison.shared_claims)}")
        answer_lines.append("")

        for page, claims in comparison.unique_claims.items():
            answer_lines.append(f"Unique to {page}: {len(claims)} claims")

        sources: list[dict] = []
        for claim in comparison.shared_claims:
            sources.append({
                "claim_uuid": claim.uuid,
                "content": claim.content[:100],
                "shared": True,
            })

        return QueryResult(
            answer="\n".join(answer_lines),
            sources=sources,
            coverage=comparison.similarity,
            mode="compare",
        )

    def _tree_query(self, question: str) -> QueryResult:
        """Tree mode search for hierarchical documents.

        Args:
            question: Search query.

        Returns:
            QueryResult with section paths.
        """
        section_paths = self._tree_mode.search(question, limit=10)

        if not section_paths:
            return QueryResult(
                answer=f"No hierarchical structure found for '{question}'",
                mode="tree",
            )

        # Format as answer
        answer_lines: list[str] = []
        answer_lines.append(f"Tree mode search for '{question}':")
        answer_lines.append(f"Found {len(section_paths)} section paths:")

        sources: list[dict] = []

        for i, path in enumerate(section_paths, 1):
            path_str = " > ".join(path.path) if path.path else "root"
            answer_lines.append(f"{i}. {path_str} ({len(path.claims)} claims)")
            for claim in path.claims:
                sources.append({
                    "claim_uuid": claim.uuid,
                    "content": claim.content[:100],
                    "section_path": path_str,
                })

        return QueryResult(
            answer="\n".join(answer_lines),
            sources=sources,
            mode="tree",
        )

    def _get_query_prompt(self) -> str:
        """Load query system prompt from YAML.

        Returns:
            System prompt string.
        """
        import yaml
        from pathlib import Path

        prompt_path = Path(__file__).parent.parent.parent / "adapters" / "llm" / "prompts" / "query_default.yaml"

        if prompt_path.exists():
            with open(prompt_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data.get("system_prompt", self._default_prompt())

        return self._default_prompt()

    def _default_prompt(self) -> str:
        """Default query prompt.

        Returns:
            Default system prompt string.
        """
        return """You are a knowledgeable research assistant with access to a curated knowledge base.
Answer the user's question based on the provided context only.

Rules:
1. Every factual statement must reference a claim using [^claim:UUID] format
2. If the context does not contain enough information, say so explicitly
3. Structure your answer in layers:
   - First line: concise title/answer (L1)
   - First paragraph: summary in 2-3 sentences (L2)
   - Key conclusions as bullet points (L3)
   - Full detailed answer with all evidence (L4)
4. Preserve the original language of the source material
5. Never fabricate claims or citations that are not in the context"""

    def _parse_layered_answer(
        self, raw_answer: str, depth: int
    ) -> dict[str, str]:
        """Parse raw LLM answer into layered structure.

        Args:
            raw_answer: Raw LLM response.
            depth: Depth level (1-4).

        Returns:
            Dict with L1, L2, L3, L4 layers.
        """
        layers: dict[str, str] = {}

        lines = raw_answer.split("\n")

        # L1: First line or heading
        if lines:
            first_line = lines[0].strip()
            # Remove markdown heading markers
            if first_line.startswith("#"):
                first_line = first_line.lstrip("#").strip()
            layers["L1"] = first_line

        # L2: First paragraph (summary)
        paragraphs: list[str] = []
        current_para: list[str] = []

        for line in lines[1:]:
            if line.strip() == "":
                if current_para:
                    paragraphs.append(" ".join(current_para))
                    current_para = []
            else:
                current_para.append(line.strip())

        if current_para:
            paragraphs.append(" ".join(current_para))

        if paragraphs:
            layers["L2"] = paragraphs[0]

        # L3: Key conclusions (bullet points)
        bullets: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("-") or stripped.startswith("*"):
                bullets.append(stripped)

        if bullets:
            layers["L3"] = "\n".join(bullets[:5])  # Top 5 bullets

        # L4: Full text
        if depth >= 4:
            layers["L4"] = raw_answer

        return layers

    def _extract_citations(self, answer: str) -> list[str]:
        """Extract [^claim:uuid] citations from answer.

        Args:
            answer: Answer text.

        Returns:
            List of claim UUIDs cited.
        """
        # Match both UUID format and simpler IDs (alphanumeric, hyphens, underscores)
        pattern = r'\[\^claim:([a-zA-Z0-9_-]+)\]'
        matches = re.findall(pattern, answer, re.IGNORECASE)
        return list(set(matches))

    def _resolve_citations(
        self, citations: list[str], compiled_sources: list[dict]
    ) -> list[dict]:
        """Resolve citations to source details.

        Args:
            citations: List of claim UUIDs.
            compiled_sources: Sources from compiled context.

        Returns:
            List of source dicts with full details.
        """
        sources: list[dict] = []

        # First check compiled sources
        for uuid in citations:
            # Check if in compiled sources
            for src in compiled_sources:
                if src.get("claim_uuid") == uuid:
                    sources.append(src)
                    break

            # If not found, look up directly
            if not any(s.get("claim_uuid") == uuid for s in sources):
                claim = self._claims_repo.get_by_id(uuid)
                if claim:
                    sources.append({
                        "claim_uuid": uuid,
                        "content": claim.content,
                        "confidence": claim.confidence.name.lower(),
                        "source_uuid": claim.source_uuid,
                        "page_number": claim.page_number,
                        "line_number": claim.line_number,
                    })

        return sources
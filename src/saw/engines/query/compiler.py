"""Context compiler for assembling relevant Wiki pages within token budget.

Per D-14: L0 always-loaded index, L1 summary, L2 full content on demand.
Token budget enforcement ensures context fits within LLM limits.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.engines.query.search import FTS5Search


@dataclass
class CompiledContext:
    """Compiled context for LLM query."""
    content: str
    token_count: int
    sources: list[dict] = field(default_factory=list)
    coverage: float = 0.0


class ContextCompiler:
    """Compile relevant wiki pages and claims into context for LLM.

    Per D-14: Context compilation with token budget.
    L0: Always-loaded index (~85 lines)
    L1: Summary topics
    L2: Full content on demand
    """

    # Rough character-to-token ratio (English text)
    CHARS_PER_TOKEN = 4
    L0_BUDGET = 500  # ~125 tokens for index
    L1_BUDGET = 1000  # ~250 tokens per claim

    def __init__(
        self,
        claims_repo: SQLiteClaimsRepository,
        wiki_repo: WikiRepository,
        search_service: FTS5Search,
        conn: sqlite3.Connection,
        workspace_id: str = "default",
    ) -> None:
        """Initialize context compiler.

        Args:
            claims_repo: Claims repository for claim lookup.
            wiki_repo: Wiki repository for page access.
            search_service: FTS5 search for finding relevant claims.
            conn: SQLite connection.
        """
        self._claims_repo = claims_repo
        self._wiki_repo = wiki_repo
        self._search = search_service
        self._conn = conn
        self._workspace_id = workspace_id

    def set_workspace_id(self, workspace_id: str) -> None:
        """Set the workspace scope (T-F-K-2: public, replaces private setattr)."""
        self._workspace_id = workspace_id

    def compile(
        self,
        question: str,
        token_budget: int = 4000,
    ) -> CompiledContext:
        """Compile context from question within token budget.

        Args:
            question: User question.
            token_budget: Maximum tokens for context.

        Returns:
            CompiledContext with assembled content and metadata.
        """
        if not question or not question.strip():
            return CompiledContext(content="", token_count=0)

        # Step 1: L0 always-loaded index
        l0_content = self._build_l0_index()
        current_tokens = len(l0_content) // self.CHARS_PER_TOKEN

        # Step 2: Search for relevant claims
        search_result = self._search.search(question, limit=50)

        # Step 3: Load candidate claims
        candidate_claims = []
        for uuid in search_result.claim_uuids:
            claim = self._claims_repo.get_by_id(uuid, workspace_id=self._workspace_id)
            if claim:
                candidate_claims.append(claim)

        # Step 4: Prioritize claims (confidence desc, relevance desc)
        # Sort by confidence (higher first) and then by search score
        confidence_order = [
            "HUMAN_VERIFIED",
            "CROSS_VALIDATED",
            "SINGLE_SOURCE",
            "UNVERIFIED",
        ]
        candidate_claims.sort(
            key=lambda c: confidence_order.index(c.confidence.name)
            if c.confidence.name in confidence_order else 999
        )

        # Step 5: Add claims within budget
        included_claims: list = []
        claim_contents: list[str] = []

        for claim in candidate_claims:
            claim_text = self._format_claim(claim)
            claim_tokens = len(claim_text) // self.CHARS_PER_TOKEN

            if current_tokens + claim_tokens <= token_budget:
                included_claims.append(claim)
                claim_contents.append(claim_text)
                current_tokens += claim_tokens

        # Step 6: Build final context
        context_parts: list[str] = []
        context_parts.append("== Wiki Index (L0) ==")
        context_parts.append(l0_content)
        context_parts.append("")
        context_parts.append("== Relevant Claims ==")
        context_parts.extend(claim_contents)

        # Build sources metadata
        sources: list[dict] = []
        for claim in included_claims:
            sources.append({
                "claim_uuid": claim.uuid,
                "content": claim.content[:200] + "..." if len(claim.content) > 200 else claim.content,
                "confidence": claim.confidence.name.lower(),
                "source_uuid": claim.source_uuid,
                "page_number": claim.page_number,
                "line_number": claim.line_number,
            })

        # Calculate coverage
        coverage = (
            len(included_claims) / len(candidate_claims) * 100
            if candidate_claims else 0.0
        )

        return CompiledContext(
            content="\n".join(context_parts),
            token_count=current_tokens,
            sources=sources,
            coverage=coverage,
        )

    def _build_l0_index(self) -> str:
        """Build L0 index of wiki pages.

        Returns:
            Formatted index string.
        """
        pages = self._wiki_repo.list_pages()
        if not pages:
            return ""

        # Simple index: list page titles
        index_lines: list[str] = []
        for page_path in pages[:20]:  # Limit to 20 pages
            page = self._wiki_repo.read(page_path)
            if page:
                index_lines.append(f"- {page.title} ({page.page_type.name.lower()})")

        return "\n".join(index_lines)

    def _format_claim(self, claim) -> str:
        """Format a claim for context inclusion.

        Args:
            claim: Claim object.

        Returns:
            Formatted claim string.
        """
        lines: list[str] = []
        lines.append(f"[Claim UUID: {claim.uuid}]")
        lines.append(f"[Source: {claim.source_uuid}]")
        if claim.page_number:
            lines.append(f"[Page: {claim.page_number}]")
        if claim.line_number:
            lines.append(f"[Line: {claim.line_number}]")
        lines.append(f"[Confidence: {claim.confidence.name.lower()}]")
        if claim.tags:
            lines.append(f"[Tags: {', '.join(claim.tags)}]")
        lines.append(f"Content: {claim.content}")
        lines.append("")

        return "\n".join(lines)

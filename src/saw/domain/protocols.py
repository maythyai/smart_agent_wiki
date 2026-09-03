"""Domain protocols - interface definitions for all engine adapters.

All protocols use typing.Protocol for structural subtyping.
Implementations are in adapters/ directory.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from saw.domain.claims import Claim
from saw.domain.wiki import WikiPage


class ClaimsRepository(Protocol):
    """Port for Claims DB operations."""

    def get_by_id(self, uuid: str, workspace_id: str | None = None) -> Claim | None:
        """Retrieve a claim by its UUID.

        workspace_id (T-F-Z-7): when set, restrict to that workspace.
        """
        ...

    def insert(self, claim: Claim) -> str:
        """Insert a new claim. Returns the claim UUID.

        Must be idempotent: INSERT OR IGNORE on duplicate UUID.
        """
        ...

    def search(
        self, query: str, limit: int = 10, workspace_id: str | None = None
    ) -> list[Claim]:
        """Full-text search via FTS5 MATCH with bm25 ranking.

        workspace_id (T-F-Z-7): when set, restrict matches to that workspace.
        """
        ...

    def get_by_source(self, source_uuid: str) -> list[Claim]:
        """Get all claims originating from a specific source."""
        ...

    def count(self) -> int:
        """Count total non-deleted claims."""
        ...


class VaultRepository(Protocol):
    """Port for Vault immutable storage operations."""

    def store(self, source_path: Path, uuid: str, metadata: dict) -> Path:
        """Store a document in the vault under a UUID directory.

        Creates vault/{uuid}/ with original file, transcript.md, and meta.yaml.
        Idempotent: if vault/{uuid}/ exists, skip.
        """
        ...

    def get(self, uuid: str) -> Path | None:
        """Return the vault directory path for a given UUID, or None."""
        ...

    def exists(self, uuid: str) -> bool:
        """Check if a vault entry exists for the given UUID."""
        ...


class WikiRepository(Protocol):
    """Port for Wiki page read/write operations."""

    def write(self, page: WikiPage) -> Path:
        """Write a wiki page as Markdown with YAML frontmatter.

        Overwrite is safe (Markdown files).
        """
        ...

    def read(self, path: str) -> WikiPage | None:
        """Parse a wiki page from file. Returns None if not found."""
        ...

    def list_pages(self) -> list[str]:
        """List all wiki page paths."""
        ...

    def count(self) -> int:
        """Count total wiki pages."""
        ...


class WriteQueue(Protocol):
    """Port for Write Queue (Outbox) operations."""

    def enqueue(self, ops: list) -> None:
        """Atomically enqueue all operations. All-or-nothing."""
        ...

    def enqueue_atomic(self, ops: list) -> None:
        """Enqueue then immediately dispatch to sinks."""
        ...

    def get_pending(self) -> list:
        """Get pending and retryable operations."""
        ...


class Sink(Protocol):
    """Port for a Write Queue sink."""

    @property
    def name(self) -> str:
        """Sink identifier (e.g. 'vault', 'claims', 'wiki', 'fts5', 'graph')."""
        ...

    def write(self, op) -> None:
        """Process a write operation. Must be idempotent."""
        ...

    def can_handle(self, sink_name: str) -> bool:
        """Check if this sink handles the given sink name."""
        ...


class AgentProtocol(Protocol):
    """Protocol for specialized agents.

    Per D-01: 6 specialized agents with role-specific behavior.
    Per D-02: Agents have name, model_tier, system_prompt, tools_allowed, constraints.
    """

    @property
    def name(self) -> str:
        """Agent role name (e.g., 'Librarian', 'Writer', 'Scholar')."""
        ...

    @property
    def model_tier(self) -> str:
        """Model tier: 'haiku' | 'sonnet' | 'opus' | 'rule'."""
        ...

    async def execute(
        self,
        task: "AgentTask",
        context: "AgentContext",
        tools: list,
    ) -> "AgentResult":
        """Execute a task and return the result.

        Args:
            task: The task to execute.
            context: Execution context with wiki state and claims.
            tools: List of available tools for this agent.

        Returns:
            AgentResult with success, payload, confidence, and metadata.
        """
        ...

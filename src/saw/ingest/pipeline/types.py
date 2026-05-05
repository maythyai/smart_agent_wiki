"""Pipeline phase types and interfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class PhaseResult(Generic[T]):
    """Result of a single phase execution."""

    name: str
    output: T
    duration_ms: float
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PhaseResults:
    """Collection of phase results with type-safe access."""

    _results: dict[str, PhaseResult] = field(default_factory=dict)

    def add(self, result: PhaseResult) -> None:
        self._results[result.name] = result

    def get(self, name: str) -> PhaseResult:
        from .errors import PhaseNotFoundError

        if name not in self._results:
            raise PhaseNotFoundError(f"Phase '{name}' not found in results")
        return self._results[name]

    def get_output[T](self, name: str) -> T:
        """Type-safe output access."""
        return self.get(name).output

    def has(self, name: str) -> bool:
        return name in self._results

    def names(self) -> list[str]:
        return list(self._results.keys())


@dataclass
class PipelineContext:
    """Shared context for pipeline execution."""

    graph: Any  # KnowledgeGraph
    repo_path: str
    options: dict[str, Any] = field(default_factory=dict)
    progress_callback: Optional[Callable[[str, float], None]] = None

    def report_progress(self, phase: str, progress: float) -> None:
        if self.progress_callback:
            self.progress_callback(phase, progress)


# Type alias for phase executor
PhaseExecutor = Callable[[PipelineContext, PhaseResults], Awaitable[Any]]


@dataclass
class PipelinePhase:
    """Definition of a pipeline phase."""

    name: str
    deps: list[str]
    execute: PhaseExecutor
    description: str = ""

    def __post_init__(self):
        if not self.name:
            raise ValueError("Phase name is required")
        if not isinstance(self.deps, list):
            raise ValueError("Deps must be a list")


@dataclass
class PhaseList:
    """Collection of phases with validation."""

    phases: list[PipelinePhase]

    def get(self, name: str) -> PipelinePhase:
        from .errors import PhaseNotFoundError

        for phase in self.phases:
            if phase.name == name:
                return phase
        raise PhaseNotFoundError(f"Phase '{name}' not defined")

    def names(self) -> list[str]:
        return [p.name for p in self.phases]
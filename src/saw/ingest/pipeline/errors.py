"""Pipeline-specific exceptions."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import PhaseResults
    from .validator import ValidationResult


class PipelineError(Exception):
    """Base exception for pipeline errors."""

    pass


@dataclass
class PhaseNotFoundError(PipelineError):
    """Phase not found in results or definitions."""

    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class MissingDependencyError(PipelineError):
    """Phase depends on undefined phase."""

    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class CycleDetectedError(PipelineError):
    """Cycle detected in phase dependencies."""

    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class PipelineValidationError(PipelineError):
    """DAG validation failed."""

    validation_result: "ValidationResult"

    def __str__(self) -> str:
        r = self.validation_result
        if r.cycle_path:
            cycle = " → ".join(r.cycle_path)
            return f"Pipeline validation failed: cycle detected: {cycle}"
        if r.missing_deps:
            phase, dep = r.missing_deps[0]
            return f"Pipeline validation failed: phase '{phase}' depends on undefined '{dep}'"
        return "Pipeline validation failed"


@dataclass
class PhaseExecutionError(PipelineError):
    """Phase execution failed."""

    phase_name: str
    error_message: str
    completed_results: "PhaseResults"

    def __str__(self) -> str:
        completed = self.completed_results.names()
        return (
            f"Phase '{self.phase_name}' failed: {self.error_message}. "
            f"Completed phases: {completed}"
        )
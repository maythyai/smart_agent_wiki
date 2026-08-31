"""Generic DAG pipeline runner framework (NOT the production ingest pipeline).

This package provides reusable pipeline-execution primitives —
``PipelineRunner``, ``validate_dag`` (Kahn topological sort + cycle
detection), ``PipelinePhase``/``PipelineContext``/``PhaseResults`` — for
features that need topologically-ordered, multi-stage execution.

It is **not** the production ingestion path. Production ingestion lives in
``saw.engines.ingest.pipeline.IngestPipeline`` (classify -> extract -> fuse
-> validate -> enqueue via the Write Queue). The phase implementations in
``phases/`` are framework examples and are not wired into real ingestion.

See ``docs/ingest-pipeline-unification-plan.md`` for the design decision.
"""
from .types import (
    PhaseResult,
    PhaseResults,
    PipelineContext,
    PipelinePhase,
    PhaseList,
    PhaseExecutor,
)
from .validator import validate_dag, validate_phase_list, ValidationResult
from .runner import PipelineRunner
from .errors import (
    PipelineError,
    PhaseNotFoundError,
    MissingDependencyError,
    CycleDetectedError,
    PipelineValidationError,
    PhaseExecutionError,
)

__all__ = [
    'PhaseResult',
    'PhaseResults',
    'PipelineContext',
    'PipelinePhase',
    'PhaseList',
    'PhaseExecutor',
    'validate_dag',
    'validate_phase_list',
    'ValidationResult',
    'PipelineRunner',
    'PipelineError',
    'PhaseNotFoundError',
    'MissingDependencyError',
    'CycleDetectedError',
    'PipelineValidationError',
    'PhaseExecutionError',
]
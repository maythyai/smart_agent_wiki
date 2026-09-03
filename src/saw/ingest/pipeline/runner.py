"""Pipeline execution with DAG validation."""
from __future__ import annotations
import time

from .types import PipelinePhase, PipelineContext, PhaseResults, PhaseResult
from .validator import validate_dag
from .errors import PipelineValidationError, PhaseExecutionError


class PipelineRunner:
    """
    Executes pipeline phases in dependency order.

    Features:
    - DAG validation on initialization
    - Sequential execution in topological order
    - Type-safe phase output access
    - Progress reporting
    - Error handling with phase context
    """

    def __init__(self, phases: list[PipelinePhase]):
        self.phases = phases
        self._validation_result = validate_dag(phases)

        if not self._validation_result.valid:
            raise PipelineValidationError(
                self._validation_result
            )

        # Build sorted phases list
        phase_by_name = {p.name: p for p in phases}
        self._sorted_phases = [
            phase_by_name[name]
            for name in self._validation_result.sorted_order
        ]

    @property
    def _phase_names(self) -> list[str]:
        return [p.name for p in self.phases]

    async def run(self, ctx: PipelineContext) -> PhaseResults:
        """
        Execute all phases in dependency order.

        Args:
            ctx: Shared pipeline context

        Returns:
            PhaseResults with all phase outputs
        """
        results = PhaseResults()

        for phase in self._sorted_phases:
            try:
                # Filter deps to declared only
                phase_deps = PhaseResults()
                for dep_name in phase.deps:
                    phase_deps.add(results.get(dep_name))

                # Execute phase
                start = time.time()
                ctx.report_progress(phase.name, 0.0)

                output = await phase.execute(ctx, phase_deps)

                duration = (time.time() - start) * 1000
                ctx.report_progress(phase.name, 1.0)

                results.add(PhaseResult(
                    name=phase.name,
                    output=output,
                    duration_ms=duration
                ))

            except Exception as e:
                raise PhaseExecutionError(
                    phase.name,
                    str(e),
                    results
                ) from e

        return results

    def get_execution_order(self) -> list[str]:
        """Return phase names in execution order."""
        return [p.name for p in self._sorted_phases]
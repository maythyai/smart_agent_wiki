"""DAG validation for pipeline phases."""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from .types import PipelinePhase, PhaseList
from .errors import CycleDetectedError, MissingDependencyError


@dataclass
class ValidationResult:
    """Result of DAG validation."""
    valid: bool
    cycle_path: Optional[list[str]] = None
    missing_deps: list[tuple[str, str]] = field(default_factory=list)
    sorted_order: Optional[list[str]] = None
    blocked_count: int = 0


def validate_dag(phases: list[PipelinePhase]) -> ValidationResult:
    """
    Validate pipeline phases as a DAG.

    Uses Kahn's algorithm for topological sort.
    Detects cycles and missing dependencies.

    Args:
        phases: List of PipelinePhase definitions

    Returns:
        ValidationResult with validation status and details
    """
    phase_names = {p.name for p in phases}
    missing_deps = []

    # Check for missing dependencies
    for phase in phases:
        for dep in phase.deps:
            if dep not in phase_names:
                missing_deps.append((phase.name, dep))

    if missing_deps:
        return ValidationResult(
            valid=False,
            missing_deps=missing_deps
        )

    # Build adjacency list and in-degree count
    adj: dict[str, list[str]] = {p.name: [] for p in phases}
    in_degree: dict[str, int] = {p.name: 0 for p in phases}

    for phase in phases:
        for dep in phase.deps:
            adj[dep].append(phase.name)
            in_degree[phase.name] += 1

    # Kahn's algorithm
    queue = deque([name for name, deg in in_degree.items() if deg == 0])
    sorted_order = []
    blocked = set()

    while queue:
        node = queue.popleft()
        sorted_order.append(node)

        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
            else:
                blocked.add(neighbor)

    # If not all nodes processed, there's a cycle
    if len(sorted_order) != len(phases):
        cycle_path = _find_cycle(phases, adj)
        return ValidationResult(
            valid=False,
            cycle_path=cycle_path,
            blocked_count=len(blocked)
        )

    return ValidationResult(
        valid=True,
        sorted_order=sorted_order
    )


def _find_cycle(
    phases: list[PipelinePhase],
    adj: dict[str, list[str]]
) -> list[str]:
    """
    Find and return an actual cycle path using DFS.

    Returns the first cycle found as a list of phase names.
    """
    visited = set()
    rec_stack = set()
    path = []

    def dfs(node: str) -> Optional[list[str]]:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in adj[node]:
            if neighbor not in visited:
                result = dfs(neighbor)
                if result:
                    return result
            elif neighbor in rec_stack:
                # Found cycle - return the cycle portion
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]

        path.pop()
        rec_stack.remove(node)
        return None

    for phase in phases:
        if phase.name not in visited:
            cycle = dfs(phase.name)
            if cycle:
                return cycle

    return []  # No cycle found (shouldn't reach here if validation failed)


def validate_phase_list(phase_list: PhaseList) -> None:
    """
    Validate a PhaseList and raise exceptions on errors.

    Raises:
        MissingDependencyError: If dependencies are not defined
        CycleDetectedError: If the graph has cycles
    """
    result = validate_dag(phase_list.phases)

    if result.missing_deps:
        phase, dep = result.missing_deps[0]
        raise MissingDependencyError(
            f"Phase '{phase}' depends on undefined phase '{dep}'"
        )

    if result.cycle_path:
        cycle_str = " → ".join(result.cycle_path)
        raise CycleDetectedError(
            f"Cycle detected in pipeline: {cycle_str}"
        )
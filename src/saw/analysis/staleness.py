"""Staleness detection module."""
from __future__ import annotations
import time
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Literal, TYPE_CHECKING
from dataclasses import dataclass, field
from pathlib import Path

if TYPE_CHECKING:
    from saw.graph import KnowledgeGraph


StalenessSeverity = Literal['fresh', 'stale', 'outdated', 'critical']


@dataclass
class StaleNode:
    """Stale node information."""
    uid: str
    name: str
    kind: str
    file_path: str
    days_old: int
    commits_behind: int
    severity: StalenessSeverity
    last_indexed_commit: Optional[str] = None
    last_indexed_date: Optional[str] = None


@dataclass
class StalenessResult:
    """Staleness detection result."""
    total_nodes: int
    total_stale: int
    nodes: list[StaleNode]
    summary: dict
    recommendation: str
    execution_time_ms: float
    analyzed_at: str


def detect_staleness(
    graph: 'KnowledgeGraph',
    threshold_days: int = 7,
    min_commits_behind: int = 1,
    repo_path: str = None
) -> StalenessResult:
    """
    Detect stale nodes in knowledge graph.

    Algorithm:
    1. Get HEAD commit
    2. For each indexed node:
       - Get last_indexed_commit
       - Calculate commits_behind
       - Check if exceeds threshold
    3. Group stale nodes by severity
    4. Return structured result

    Args:
        graph: Knowledge graph instance
        threshold_days: Days threshold for staleness (default: 7)
        min_commits_behind: Minimum commits behind to be stale (default: 1)
        repo_path: Git repository path (default: current directory)

    Returns:
        StalenessResult with stale nodes and recommendations
    """
    start = time.time()

    # Get HEAD commit
    head_commit = _get_head_commit(repo_path)
    head_date = datetime.utcnow()

    stale_nodes = []
    all_nodes = []

    if hasattr(graph, 'get_all_nodes'):
        all_nodes = graph.get_all_nodes()
    elif hasattr(graph, 'nodes'):
        all_nodes = list(graph.nodes.values())

    for node in all_nodes:
        indexed_commit = node.get('last_indexed_commit')
        indexed_date_str = node.get('last_indexed_date')

        days_old = 0
        commits_behind = 0

        if indexed_date_str:
            try:
                indexed_date = datetime.fromisoformat(indexed_date_str.replace('Z', '+00:00'))
                days_old = (head_date - indexed_date.replace(tzinfo=None)).days
            except (ValueError, TypeError):
                days_old = 0

        if indexed_commit and head_commit and indexed_commit != head_commit:
            commits_behind = _count_commits_between(indexed_commit, head_commit, repo_path)

        severity = _get_staleness_severity(days_old, commits_behind, threshold_days, min_commits_behind)

        if severity != 'fresh':
            stale_nodes.append(StaleNode(
                uid=node.get('uid', ''),
                name=node.get('name', 'unknown'),
                kind=node.get('kind', 'unknown'),
                file_path=node.get('filePath', ''),
                days_old=days_old,
                commits_behind=commits_behind,
                severity=severity,
                last_indexed_commit=indexed_commit,
                last_indexed_date=indexed_date_str
            ))

    # Sort by severity (critical first) then days_old
    severity_order = {'critical': 0, 'outdated': 1, 'stale': 2, 'fresh': 3}
    stale_nodes.sort(key=lambda n: (severity_order[n.severity], -n.days_old))

    execution_time_ms = (time.time() - start) * 1000

    summary = {
        'total_nodes': len(all_nodes),
        'total_stale': len(stale_nodes),
        'critical_count': sum(1 for n in stale_nodes if n.severity == 'critical'),
        'outdated_count': sum(1 for n in stale_nodes if n.severity == 'outdated'),
        'stale_count': sum(1 for n in stale_nodes if n.severity == 'stale'),
        'fresh_count': len(all_nodes) - len(stale_nodes)
    }

    return StalenessResult(
        total_nodes=len(all_nodes),
        total_stale=len(stale_nodes),
        nodes=stale_nodes,
        summary=summary,
        recommendation=_generate_recommendation(stale_nodes, summary),
        execution_time_ms=execution_time_ms,
        analyzed_at=datetime.utcnow().isoformat()
    )


def _get_head_commit(repo_path: str = None) -> Optional[str]:
    """Get current HEAD commit hash."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_path or '.',
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _count_commits_between(old_commit: str, new_commit: str, repo_path: str = None) -> int:
    """Count commits between two commits."""
    try:
        result = subprocess.run(
            ['git', 'rev-list', '--count', f'{old_commit}..{new_commit}'],
            cwd=repo_path or '.',
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return int(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    return 0


def _get_staleness_severity(
    days_old: int,
    commits_behind: int,
    threshold_days: int,
    min_commits: int
) -> StalenessSeverity:
    """Determine staleness severity."""
    if days_old < threshold_days and commits_behind < min_commits:
        return 'fresh'
    elif days_old >= threshold_days * 3 or commits_behind >= 20:
        return 'critical'
    elif days_old >= threshold_days * 2 or commits_behind >= 10:
        return 'outdated'
    else:
        return 'stale'


def _generate_recommendation(stale_nodes: list[StaleNode], summary: dict) -> str:
    """Generate update recommendation."""
    if not stale_nodes:
        return "All nodes are fresh. No update needed."

    critical = summary['critical_count']
    outdated = summary['outdated_count']
    stale = summary['stale_count']

    parts = []

    if critical > 0:
        parts.append(f"{critical} critical nodes need immediate update")
    if outdated > 0:
        parts.append(f"{outdated} outdated nodes should be updated soon")
    if stale > 0:
        parts.append(f"{stale} stale nodes may need refresh")

    return "Recommendation: Run ingest to update " + ", ".join(parts) + "."


__all__ = [
    'detect_staleness',
    'StaleNode',
    'StalenessResult',
    'StalenessSeverity'
]
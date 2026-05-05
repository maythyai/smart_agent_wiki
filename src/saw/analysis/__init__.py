"""Analysis module for Smart Agent Wiki."""
from .impact import analyze_impact, NodeNotFoundError
from .types import ImpactNode, ImpactResult, RiskLevel, Direction
from .process import detect_process, EntryNotFoundError, ProcessNode, ProcessResult, flatten_tree
from .staleness import detect_staleness, StaleNode, StalenessResult, StalenessSeverity

__all__ = [
    # Impact Analysis
    'analyze_impact',
    'NodeNotFoundError',
    'ImpactNode',
    'ImpactResult',
    'RiskLevel',
    'Direction',
    # Process Detection
    'detect_process',
    'EntryNotFoundError',
    'ProcessNode',
    'ProcessResult',
    'flatten_tree',
    # Staleness Detection
    'detect_staleness',
    'StaleNode',
    'StalenessResult',
    'StalenessSeverity',
]
"""Impact analysis types."""
from typing import TypedDict, Literal

RiskLevel = Literal['WILL_BREAK', 'LIKELY_AFFECTED', 'MAY_NEED_TESTING']
Direction = Literal['upstream', 'downstream']


class ImpactNode(TypedDict):
    """Single affected node."""
    uid: str
    name: str
    kind: str
    file_path: str
    start_line: int
    depth: int
    risk_level: RiskLevel
    relation_type: str
    confidence: float


class ImpactResult(TypedDict):
    """Impact analysis result."""
    target: str
    target_node: dict
    direction: Direction
    impacts: list[ImpactNode]
    summary: dict
    execution_time_ms: float
    analyzed_at: str
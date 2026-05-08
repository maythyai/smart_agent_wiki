"""
Reconcile Engine - 自动矛盾解决引擎

基于 Obsidian Second Brain 的 /obsidian-reconcile 设计模式实现：
- 检测 Claims 层的矛盾主张
- 选择最优解决策略
- 记录完整审计过程
- 支持 Bi-Temporal Facts 追踪
"""

from .detector import ContradictionDetector, Contradiction
from .strategies import ResolutionStrategy, ResolutionStrategist
from .audit import AuditLogger, AuditEntry
from .models import (
    BiTemporalFact,
    ContradictionType,
    ResolutionStrategyType,
    FactStatus,
)
from .engine import ReconcileEngine

__all__ = [
    "ContradictionDetector",
    "Contradiction",
    "ResolutionStrategy",
    "ResolutionStrategist",
    "AuditLogger",
    "AuditEntry",
    "BiTemporalFact",
    "ContradictionType",
    "ResolutionStrategyType",
    "FactStatus",
    "ReconcileEngine",
]
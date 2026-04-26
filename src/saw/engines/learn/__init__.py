"""Learning Engine - self-improvement and adaptation.

The Learning Engine provides:
- Training period adaptation (30-day preference learning)
- FSRS spaced repetition for page reviews
- Cognitive distillation for SOP extraction
- Knowledge expiry classification (tactical vs strategic)
- Trend sensing for gap detection

Per D-14 to D-21 implementation decisions.
"""
from saw.engines.learn.adaptive import TrainingPeriod, UserPreference
from saw.engines.learn.fsrs_scheduler import FSRSScheduler, ReviewItem
from saw.engines.learn.distiller import Distiller, SOP
from saw.engines.learn.trends import TrendSenser, KnowledgeGap
from saw.engines.learn.expiry import KnowledgeExpiry, ExpiryCandidate
from saw.engines.learn.engine import LearnEngine, LearningReport

__all__ = [
    "TrainingPeriod",
    "UserPreference",
    "FSRSScheduler",
    "ReviewItem",
    "Distiller",
    "SOP",
    "TrendSenser",
    "KnowledgeGap",
    "KnowledgeExpiry",
    "ExpiryCandidate",
    "LearnEngine",
    "LearningReport",
]

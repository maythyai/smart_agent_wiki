"""
Purpose Module - Wiki意图和目标定义系统

基于 llm_wiki 的 purpose.md 设计模式实现
"""

from .manager import PurposeManager
from .models import Purpose, Goal, ResearchScope
from .analyzer import PurposeAnalyzer

__all__ = [
    "PurposeManager",
    "Purpose",
    "Goal",
    "ResearchScope",
    "PurposeAnalyzer",
]
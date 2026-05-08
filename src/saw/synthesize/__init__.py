"""
Synthesize Engine - 模式发现与综合页面生成引擎

基于 Obsidian Second Brain 的 /obsidian-synthesize 设计模式实现：
- 自动发现跨来源的模式
- 生成综合页面
- 支持定时任务
"""

from .miner import PatternMiner, Pattern
from .cluster import ClusterBuilder, Cluster
from .generator import PageGenerator, SynthesisPage
from .scheduler import SynthesizeScheduler
from .engine import SynthesizeEngine

__all__ = [
    "PatternMiner",
    "Pattern",
    "ClusterBuilder",
    "Cluster",
    "PageGenerator",
    "SynthesisPage",
    "SynthesizeScheduler",
    "SynthesizeEngine",
]
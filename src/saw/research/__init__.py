"""
Deep Research Module - 深度研究工具

基于 llm_wiki 的 Deep Research 设计模式实现
"""

from .research_engine import DeepResearchEngine
from .web_search import WebSearchClient
from .auto_ingest import AutoIngestProcessor

__all__ = [
    "DeepResearchEngine",
    "WebSearchClient",
    "AutoIngestProcessor",
]
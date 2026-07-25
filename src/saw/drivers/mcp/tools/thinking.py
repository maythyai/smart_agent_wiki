"""
Thinking Tools MCP - 批判性思维工具集

基于 Obsidian Second Brain 的 Thinking Tools 设计模式
"""

from .challenge import challenge_tool
from .emerge import emerge_tool
from .connect import connect_tool
from .graduate import graduate_tool
from .context import context_tool

__all__ = [
    "challenge_tool",
    "emerge_tool",
    "connect_tool",
    "graduate_tool",
    "context_tool",
]
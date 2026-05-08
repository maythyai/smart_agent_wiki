"""
saw_context - Context Loader Tool

渐进式上下文加载
"""

from typing import Optional
from pathlib import Path

from saw.context.loader import ContextLoader, ContextLevel
from saw.context.loader import ContextBundle


def context_tool(
    level: str = "l1",
    wiki_path: Optional[Path] = None,
    state_path: Optional[Path] = None,
) -> ContextBundle:
    """
    渐进式加载上下文

    按级别加载上下文，控制 token 消耗：
    - L0: 仅 CRITICAL_FACTS (~120 tokens)
    - L1: + 当前项目状态 (~500 tokens)
    - L2: + 相关历史决策 (~1500 tokens)
    - L3: + 完整上下文 (~5000 tokens)

    Args:
        level: 上下文级别 (l0, l1, l2, l3)
        wiki_path: Wiki 目录路径
        state_path: 状态文件路径

    Returns:
        上下文包
    """
    # 解析级别
    level_map = {
        "l0": ContextLevel.L0,
        "l1": ContextLevel.L1,
        "l2": ContextLevel.L2,
        "l3": ContextLevel.L3,
    }

    context_level = level_map.get(level.lower(), ContextLevel.L1)

    # 创建加载器
    loader = ContextLoader(
        wiki_path=wiki_path,
        state_path=state_path,
    )

    # 加载上下文
    bundle = loader.load(context_level)

    return bundle


def format_context_bundle(bundle: ContextBundle) -> str:
    """格式化上下文包为可读文本"""
    return bundle.to_markdown()


def get_context_stats(loader: ContextLoader) -> dict:
    """获取上下文统计信息"""
    return loader.get_stats()

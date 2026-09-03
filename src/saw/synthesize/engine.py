"""
Synthesize Engine - 综合引擎

整合模式挖掘、聚合和页面生成的完整引擎
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .miner import PatternMiner, MiningResult
from .cluster import ClusterBuilder, ClusterResult
from .generator import PageGenerator, GenerationResult, SynthesisPage
from .scheduler import SynthesizeScheduler


@dataclass
class SynthesizeResult:
    """综合引擎结果"""
    mining: MiningResult
    clustering: ClusterResult
    generation: GenerationResult
    pages: list[SynthesisPage] = field(default_factory=list)
    total_time: float = 0.0


class SynthesizeEngine:
    """
    综合引擎

    整合模式挖掘、聚合构建和页面生成：
    1. 从 Claims/Wiki 中挖掘模式
    2. 聚合相关主张为簇
    3. 生成 AI-first 综合页面
    4. 支持定时任务调度
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        schedule_config: Optional[Path] = None,
        min_occurrences: int = 3,
    ):
        """
        初始化综合引擎

        Args:
            output_dir: 输出目录
            schedule_config: 调度配置路径
            min_occurrences: 最小出现次数
        """
        self.miner = PatternMiner(min_occurrences=min_occurrences)
        self.cluster_builder = ClusterBuilder()
        self.generator = PageGenerator(output_dir=output_dir)
        self.scheduler = SynthesizeScheduler(config_path=schedule_config)

    def synthesize(
        self,
        items: list[dict],
        time_window: Optional[timedelta] = None,
        save_pages: bool = True,
    ) -> SynthesizeResult:
        """
        执行综合流程

        Args:
            items: 内容项列表
            time_window: 时间窗口
            save_pages: 是否保存页面

        Returns:
            综合结果
        """
        start_time = datetime.now()

        # 1. 挖掘模式
        mining = self.miner.mine(items, time_window)

        if not mining.patterns:
            return SynthesizeResult(
                mining=mining,
                clustering=ClusterResult(),
                generation=GenerationResult(),
                total_time=(datetime.now() - start_time).total_seconds(),
            )

        # 2. 构建聚合簇
        # 将 items 转换为 claims 格式
        claims = [
            {
                "id": item.get("id", f"claim-{i}"),
                "content": item.get("content", ""),
                "topic": item.get("topic", "general"),
                "confidence": item.get("confidence", 1),
                "source": item.get("source", ""),
            }
            for i, item in enumerate(items)
        ]

        clustering = self.cluster_builder.build(claims)

        # 3. 生成页面
        generation = self.generator.generate(
            [p.to_dict() for p in mining.patterns],
            [c.to_dict() for c in clustering.clusters],
        )

        # 4. 保存页面
        pages = generation.pages
        if save_pages and pages:
            self.generator.save_all(pages)

        total_time = (datetime.now() - start_time).total_seconds()

        return SynthesizeResult(
            mining=mining,
            clustering=clustering,
            generation=generation,
            pages=pages,
            total_time=total_time,
        )

    def run_scheduled_task(
        self,
        task_id: str,
        items: list[dict],
    ) -> SynthesizeResult:
        """
        执行定时任务

        Args:
            task_id: 任务 ID
            items: 内容项列表

        Returns:
            综合结果
        """
        task = self.scheduler.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        # 根据任务配置设置参数
        config = task.config
        time_window = None

        if config.get("time_window_hours"):
            time_window = timedelta(hours=config["time_window_hours"])
        elif config.get("time_window_days"):
            time_window = timedelta(days=config["time_window_days"])

        # 临时调整 miner 参数
        original_min = self.miner.min_occurrences
        self.miner.min_occurrences = config.get("min_occurrences", original_min)

        # 执行综合
        result = self.synthesize(items, time_window)

        # 恢复原始参数
        self.miner.min_occurrences = original_min

        # 标记任务完成
        self.scheduler.mark_task_run(
            task_id=task_id,
            success=True,
            pages_generated=len(result.pages),
            patterns_found=len(result.mining.patterns),
            clusters_created=len(result.clustering.clusters),
        )

        return result

    def get_pending_tasks(self) -> list:
        """获取待执行任务"""
        return self.scheduler.get_pending_tasks()

    def get_stats(self) -> dict:
        """获取引擎统计"""
        return {
            "scheduler": {
                "total_tasks": len(self.scheduler.tasks),
                "enabled_tasks": sum(1 for t in self.scheduler.tasks.values() if t.enabled),
                "pending_tasks": len(self.get_pending_tasks()),
                "recent_results": len(self.scheduler.get_recent_results()),
            },
            "miner": {
                "min_occurrences": self.miner.min_occurrences,
                "min_confidence": self.miner.min_confidence,
            },
        }

    def enable_nightly(self) -> None:
        """启用夜间任务"""
        self.scheduler.enable_task("nightly-pattern")

    def enable_weekly(self) -> None:
        """启用周度任务"""
        self.scheduler.enable_task("weekly-synthesis")

    def enable_monthly(self) -> None:
        """启用月度任务"""
        self.scheduler.enable_task("monthly-analysis")
"""
Synthesize Scheduler - 定时任务调度器

实现定时综合任务
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from enum import Enum


class ScheduleType(Enum):
    """调度类型"""
    NIGHTLY = "nightly"      # 每晚运行
    WEEKLY = "weekly"        # 每周运行
    MONTHLY = "monthly"      # 每月运行
    MANUAL = "manual"        # 手动触发


@dataclass
class ScheduleTask:
    """调度任务"""
    task_id: str
    schedule_type: ScheduleType
    scope: Optional[str] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    enabled: bool = True
    config: dict = field(default_factory=dict)


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    executed_at: datetime
    success: bool
    pages_generated: int = 0
    patterns_found: int = 0
    clusters_created: int = 0
    error_message: str = ""


class SynthesizeScheduler:
    """
    综合调度器

    管理定时综合任务：
    - nightly: 每晚 10 PM 运行模式发现
    - weekly: 每周五 6 PM 运行周度综合
    - monthly: 每月 1 日运行月度分析
    """

    def __init__(
        self,
        config_path: Optional[Path] = None,
    ):
        """
        初始化调度器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or Path(".saw/synthesize_schedule.json")
        self.tasks: dict[str, ScheduleTask] = {}
        self.results: list[TaskResult] = []

        self._init_default_tasks()
        self.load()

    def _init_default_tasks(self) -> None:
        """初始化默认任务"""
        default_tasks = [
            ScheduleTask(
                task_id="nightly-pattern",
                schedule_type=ScheduleType.NIGHTLY,
                next_run=self._calculate_next_nightly(),
                config={"min_occurrences": 3, "time_window_hours": 24},
            ),
            ScheduleTask(
                task_id="weekly-synthesis",
                schedule_type=ScheduleType.WEEKLY,
                next_run=self._calculate_next_weekly(),
                config={"min_occurrences": 5, "time_window_days": 7},
            ),
            ScheduleTask(
                task_id="monthly-analysis",
                schedule_type=ScheduleType.MONTHLY,
                next_run=self._calculate_next_monthly(),
                config={"min_occurrences": 10, "time_window_days": 30},
            ),
        ]

        for task in default_tasks:
            self.tasks[task.task_id] = task

    def _calculate_next_nightly(self) -> datetime:
        """计算下一次夜间运行时间"""
        now = datetime.now()
        # 设为今晚 10 PM
        next_run = now.replace(hour=22, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        return next_run

    def _calculate_next_weekly(self) -> datetime:
        """计算下一次周度运行时间"""
        now = datetime.now()
        # 设为下周五 6 PM
        days_until_friday = (4 - now.weekday()) % 7
        if days_until_friday == 0 and now.hour >= 18:
            days_until_friday = 7
        next_run = now + timedelta(days=days_until_friday)
        next_run = next_run.replace(hour=18, minute=0, second=0, microsecond=0)
        return next_run

    def _calculate_next_monthly(self) -> datetime:
        """计算下一次月度运行时间"""
        now = datetime.now()
        # 设为下月 1 日 9 AM
        if now.month == 12:
            next_run = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_run = now.replace(month=now.month + 1, day=1)
        next_run = next_run.replace(hour=9, minute=0, second=0, microsecond=0)
        return next_run

    def get_pending_tasks(self) -> list[ScheduleTask]:
        """获取待执行任务"""
        pending = []
        now = datetime.now()

        for task in self.tasks.values():
            if not task.enabled:
                continue
            if task.next_run and task.next_run <= now:
                pending.append(task)

        return pending

    def mark_task_run(
        self,
        task_id: str,
        success: bool,
        pages_generated: int = 0,
        patterns_found: int = 0,
        clusters_created: int = 0,
        error_message: str = "",
    ) -> None:
        """标记任务已执行"""
        task = self.tasks.get(task_id)
        if not task:
            return

        now = datetime.now()
        task.last_run = now

        # 更新下一次运行时间
        if task.schedule_type == ScheduleType.NIGHTLY:
            task.next_run = now + timedelta(days=1)
        elif task.schedule_type == ScheduleType.WEEKLY:
            task.next_run = now + timedelta(weeks=1)
        elif task.schedule_type == ScheduleType.MONTHLY:
            # 下月 1 日
            if now.month == 12:
                task.next_run = now.replace(year=now.year + 1, month=1, day=1)
            else:
                task.next_run = now.replace(month=now.month + 1, day=1)
        else:
            task.next_run = None

        # 记录结果
        result = TaskResult(
            task_id=task_id,
            executed_at=now,
            success=success,
            pages_generated=pages_generated,
            patterns_found=patterns_found,
            clusters_created=clusters_created,
            error_message=error_message,
        )
        self.results.append(result)

        self.save()

    def enable_task(self, task_id: str) -> None:
        """启用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self.save()

    def disable_task(self, task_id: str) -> None:
        """禁用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            self.save()

    def add_custom_task(
        self,
        task_id: str,
        schedule_type: ScheduleType,
        scope: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> ScheduleTask:
        """添加自定义任务"""
        task = ScheduleTask(
            task_id=task_id,
            schedule_type=schedule_type,
            scope=scope,
            config=config or {},
        )

        # 设置下一次运行时间
        if schedule_type == ScheduleType.NIGHTLY:
            task.next_run = self._calculate_next_nightly()
        elif schedule_type == ScheduleType.WEEKLY:
            task.next_run = self._calculate_next_weekly()
        elif schedule_type == ScheduleType.MONTHLY:
            task.next_run = self._calculate_next_monthly()

        self.tasks[task_id] = task
        self.save()

        return task

    def remove_task(self, task_id: str) -> None:
        """移除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save()

    def get_task(self, task_id: str) -> Optional[ScheduleTask]:
        """获取任务"""
        return self.tasks.get(task_id)

    def list_tasks(self) -> list[ScheduleTask]:
        """列出所有任务"""
        return list(self.tasks.values())

    def get_recent_results(self, limit: int = 10) -> list[TaskResult]:
        """获取最近执行结果"""
        return self.results[-limit:]

    def save(self) -> None:
        """保存配置"""
        if self.config_path:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "schedule_type": t.schedule_type.value,
                        "scope": t.scope,
                        "last_run": t.last_run.isoformat() if t.last_run else None,
                        "next_run": t.next_run.isoformat() if t.next_run else None,
                        "enabled": t.enabled,
                        "config": t.config,
                    }
                    for t in self.tasks.values()
                ],
                "results": [
                    {
                        "task_id": r.task_id,
                        "executed_at": r.executed_at.isoformat(),
                        "success": r.success,
                        "pages_generated": r.pages_generated,
                        "patterns_found": r.patterns_found,
                        "clusters_created": r.clusters_created,
                        "error_message": r.error_message,
                    }
                    for r in self.results[-100:]  # 只保留最近 100 个结果
                ],
            }

            self.config_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

    def load(self) -> None:
        """加载配置"""
        if not self.config_path or not self.config_path.exists():
            return

        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))

            for t_data in data.get("tasks", []):
                task = ScheduleTask(
                    task_id=t_data["task_id"],
                    schedule_type=ScheduleType(t_data["schedule_type"]),
                    scope=t_data.get("scope"),
                    last_run=datetime.fromisoformat(t_data["last_run"]) if t_data.get("last_run") else None,
                    next_run=datetime.fromisoformat(t_data["next_run"]) if t_data.get("next_run") else None,
                    enabled=t_data.get("enabled", True),
                    config=t_data.get("config", {}),
                )
                self.tasks[task.task_id] = task

            for r_data in data.get("results", []):
                result = TaskResult(
                    task_id=r_data["task_id"],
                    executed_at=datetime.fromisoformat(r_data["executed_at"]),
                    success=r_data["success"],
                    pages_generated=r_data.get("pages_generated", 0),
                    patterns_found=r_data.get("patterns_found", 0),
                    clusters_created=r_data.get("clusters_created", 0),
                    error_message=r_data.get("error_message", ""),
                )
                self.results.append(result)

        except (json.JSONDecodeError, KeyError, ValueError):
            # 配置损坏时使用默认配置
            pass
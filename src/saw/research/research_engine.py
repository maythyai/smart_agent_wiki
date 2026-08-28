"""
Deep Research Engine - 深度研究引擎

整合网页搜索和自动摄入
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ResearchTask:
    """研究任务"""
    task_id: str
    topic: str
    search_queries: list[str]
    status: str = "pending"  # pending, running, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class ResearchResult:
    """研究结果"""
    task: ResearchTask
    sources_found: int = 0
    pages_created: int = 0
    synthesis_page: Optional[str] = None
    total_time: float = 0.0


class DeepResearchEngine:
    """
    深度研究引擎

    执行完整的研究流程：
    1. LLM 优化研究主题
    2. 多查询并行搜索
    3. 结果自动摄入
    4. LLM 综合生成 Wiki 页面
    5. 提取实体和概念
    """

    def __init__(
        self,
        wiki_path: Optional[Path] = None,
        api_key: Optional[str] = None,
        max_concurrent_tasks: int = 3,
    ):
        """
        初始化研究引擎

        Args:
            wiki_path: Wiki 目录路径
            api_key: Tavily API 密钥
            max_concurrent_tasks: 最大并发任务数
        """
        self.wiki_path = wiki_path or Path(".saw/wiki")
        self.api_key = api_key
        self.max_concurrent_tasks = max_concurrent_tasks

        # 延迟导入避免循环依赖
        self._web_search = None
        self._auto_ingest = None

    def _get_web_search(self):
        """获取网页搜索客户端"""
        if self._web_search is None:
            from .web_search import WebSearchClient
            self._web_search = WebSearchClient(api_key=self.api_key)
        return self._web_search

    def _get_auto_ingest(self):
        """获取自动摄入处理器"""
        if self._auto_ingest is None:
            from .auto_ingest import AutoIngestProcessor
            self._auto_ingest = AutoIngestProcessor(wiki_path=self.wiki_path)
        return self._auto_ingest

    def generate_search_queries(
        self,
        topic: str,
        context: Optional[str] = None,
        num_queries: int = 3,
    ) -> list[str]:
        """
        生成搜索查询

        基于主题和上下文生成优化的搜索查询

        Args:
            topic: 研究主题
            context: 额外上下文（如 overview.md, purpose.md）
            num_queries: 查询数量

        Returns:
            搜索查询列表
        """
        # 简化实现：基于主题生成查询
        # 实际应该使用 LLM 生成

        base_queries = [
            f"{topic} overview",
            f"{topic} latest research",
            f"{topic} key concepts",
        ]

        # 如果有上下文，添加更具体的查询
        if context:
            base_queries.append(f"{topic} {context[:50]}")

        return base_queries[:num_queries]

    def execute_research(
        self,
        topic: str,
        purpose_summary: Optional[str] = None,
        overview_summary: Optional[str] = None,
        num_queries: int = 3,
        max_results_per_query: int = 3,
        auto_synthesize: bool = True,
    ) -> ResearchResult:
        """
        执行深度研究

        Args:
            topic: 研究主题
            purpose_summary: Purpose 摘要（用于上下文）
            overview_summary: Overview 摘要（用于上下文）
            num_queries: 搜索查询数
            max_results_per_query: 每个查询的最大结果数
            auto_synthesize: 是否自动综合

        Returns:
            研究结果
        """
        from time import time
        start_time = time()

        # 创建任务
        task = ResearchTask(
            task_id=f"research-{hash(topic) % 10000:04d}",
            topic=topic,
            search_queries=[],
            status="running",
        )

        # 1. 生成搜索查询
        context = purpose_summary or overview_summary

        # F-RS-07: surface failures — mark the task failed on exception
        # instead of always "completed". (No API key / empty results still
        # complete normally; only an actual error is "failed".)
        unique_results = []
        ingest_result = None
        synthesis_page = None
        try:
            task.search_queries = self.generate_search_queries(
                topic, context, num_queries
            )

            # 2. 执行搜索
            web_search = self._get_web_search()
            responses = web_search.multi_search(
                task.search_queries,
                max_results_per_query,
            )

            # 3. 去重
            unique_results = web_search.deduplicate(responses)

            # 4. 自动摄入
            auto_ingest = self._get_auto_ingest()
            ingest_result = auto_ingest.process_search_results(
                [r.__dict__ for r in unique_results],
                topic,
            )

            # 5. 综合 — F-RS-06: pass the actual ingested items so the
            # synthesis page lists real sources (was [] -> 0 sources,
            # breaking the source traceability chain).
            if auto_synthesize and ingest_result.items_successful > 0:
                synthesis_page = auto_ingest.synthesize_research(
                    ingest_result.items,
                    topic,
                )

            task.status = "completed"
        except Exception:
            task.status = "failed"
        task.completed_at = datetime.now()

        return ResearchResult(
            task=task,
            sources_found=len(unique_results),
            pages_created=ingest_result.items_successful if ingest_result else 0,
            synthesis_page=synthesis_page,
            total_time=time() - start_time,
        )

    def research_knowledge_gap(
        self,
        gap_description: str,
        overview_path: Optional[Path] = None,
        purpose_path: Optional[Path] = None,
    ) -> ResearchResult:
        """
        研究知识缺口

        针对图洞察发现的知识缺口进行研究

        Args:
            gap_description: 缺口描述
            overview_path: Overview 文件路径
            purpose_path: Purpose 文件路径

        Returns:
            研究结果
        """
        # 读取上下文
        purpose_summary = None
        overview_summary = None

        if purpose_path and purpose_path.exists():
            purpose_summary = purpose_path.read_text(encoding="utf-8")[:500]

        if overview_path and overview_path.exists():
            overview_summary = overview_path.read_text(encoding="utf-8")[:500]

        # 执行研究
        return self.execute_research(
            topic=gap_description,
            purpose_summary=purpose_summary,
            overview_summary=overview_summary,
        )

    def get_stats(self) -> dict:
        """获取统计"""
        return {
            "wiki_path": str(self.wiki_path),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "web_search_enabled": self.api_key is not None,
        }
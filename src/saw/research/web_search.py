"""
Web Search Client - 网页搜索客户端

集成 Tavily API 进行网页搜索
"""

from dataclasses import dataclass, field
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果"""
    url: str
    title: str
    content: str
    score: float = 0.0
    raw_content: str = ""  # 完整内容（不截断）


@dataclass
class SearchResponse:
    """搜索响应"""
    query: str
    results: list[SearchResult] = field(default_factory=list)
    search_time: float = 0.0
    total_results: int = 0


class WebSearchClient:
    """
    网页搜索客户端

    使用 Tavily API 进行搜索：
    1. 多查询并行搜索
    2. 完整内容提取（不截断）
    3. 结果去重和排序
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.tavily.com",
    ):
        """
        初始化搜索客户端

        Args:
            api_key: Tavily API 密钥
            base_url: API 基础 URL
        """
        self.api_key = api_key
        self.base_url = base_url

    def search(
        self,
        query: str,
        max_results: int = 5,
        include_raw_content: bool = True,
    ) -> SearchResponse:
        """
        执行搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数
            include_raw_content: 是否包含完整内容

        Returns:
            搜索响应
        """
        from time import time
        start_time = time()

        # 简化实现：如果没有 API 密钥，返回空结果
        if not self.api_key:
            return SearchResponse(
                query=query,
                results=[],
                search_time=time() - start_time,
                total_results=0,
            )

        # 实际 API 调用（需要安装 requests 或使用 httpx）
        try:
            import urllib.request
            import urllib.parse

            data = json.dumps({
                "query": query,
                "max_results": max_results,
                "include_raw_content": include_raw_content,
            }).encode("utf-8")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            url = f"{self.base_url}/search"
            req = urllib.request.Request(url, data=data, headers=headers)

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))

            results = []
            for r in result.get("results", []):
                results.append(SearchResult(
                    url=r.get("url", ""),
                    title=r.get("title", ""),
                    content=r.get("content", ""),
                    score=r.get("score", 0),
                    raw_content=r.get("raw_content", ""),
                ))

            return SearchResponse(
                query=query,
                results=results,
                search_time=time() - start_time,
                total_results=len(results),
            )

        except Exception as e:
            # F-RS-02: log the failure instead of silently swallowing it
            # (the exception variable was previously captured but unused).
            logger.warning("Web search failed for query '%s': %s", query, e)
            return SearchResponse(
                query=query,
                results=[],
                search_time=time() - start_time,
                total_results=0,
            )

    def multi_search(
        self,
        queries: list[str],
        max_results_per_query: int = 3,
    ) -> list[SearchResponse]:
        """
        多查询搜索

        Args:
            queries: 查询列表
            max_results_per_query: 每个查询的最大结果数

        Returns:
            搜索响应列表
        """
        responses = []

        for query in queries:
            response = self.search(query, max_results_per_query)
            responses.append(response)

        return responses

    def deduplicate(
        self,
        responses: list[SearchResponse],
    ) -> list[SearchResult]:
        """
        去重结果

        Args:
            responses: 搜索响应列表

        Returns:
            去重后的结果列表
        """
        seen_urls = set()
        unique_results = []

        for response in responses:
            for result in response.results:
                if result.url not in seen_urls:
                    seen_urls.add(result.url)
                    unique_results.append(result)

        # 按分数排序
        unique_results.sort(key=lambda x: -x.score)

        return unique_results
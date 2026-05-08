"""
Auto Ingest Processor - 自动摄入处理器

处理搜索结果的自动摄入
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import hashlib


@dataclass
class IngestItem:
    """摄入项"""
    item_id: str
    content: str
    source_url: str
    title: str
    metadata: dict = field(default_factory=dict)


@dataclass
class IngestResult:
    """摄入结果"""
    items_processed: int = 0
    items_successful: int = 0
    items_failed: int = 0
    wiki_pages_created: list[str] = field(default_factory=list)
    processing_time: float = 0.0


class AutoIngestProcessor:
    """
    自动摄入处理器

    将搜索结果自动处理为 Wiki 内容：
    1. 提取关键内容
    2. 生成页面结构
    3. 触发两步摄入流程
    4. 提取实体和概念
    """

    def __init__(
        self,
        wiki_path: Optional[Path] = None,
        sources_path: Optional[Path] = None,
    ):
        """
        初始化处理器

        Args:
            wiki_path: Wiki 目录路径
            sources_path: 原始来源目录路径
        """
        self.wiki_path = wiki_path or Path(".saw/wiki")
        self.sources_path = sources_path or Path(".saw/sources")

    def process_search_results(
        self,
        results: list[dict],
        research_topic: str,
    ) -> IngestResult:
        """
        处理搜索结果

        Args:
            results: 搜索结果列表
            research_topic: 研究主题

        Returns:
            摄入结果
        """
        from time import time
        start_time = time()

        result = IngestResult()

        # 确保目录存在
        self.sources_path.mkdir(parents=True, exist_ok=True)

        for search_result in results:
            result.items_processed += 1

            try:
                # 创建摄入项
                item = self._create_ingest_item(search_result, research_topic)

                # 保存来源
                source_path = self._save_source(item)

                # 触发摄入（简化：直接创建 wiki 页面）
                wiki_page = self._create_wiki_page(item)

                result.items_successful += 1
                result.wiki_pages_created.append(wiki_page)

            except Exception:
                result.items_failed += 1

        result.processing_time = time() - start_time

        return result

    def _create_ingest_item(
        self,
        search_result: dict,
        research_topic: str,
    ) -> IngestItem:
        """创建摄入项"""
        url = search_result.get("url", "")
        title = search_result.get("title", "Untitled")
        content = search_result.get("raw_content", "") or search_result.get("content", "")

        # 生成 ID
        item_id = hashlib.md5(url.encode()).hexdigest()[:12]

        return IngestItem(
            item_id=item_id,
            content=content,
            source_url=url,
            title=title,
            metadata={
                "research_topic": research_topic,
                "score": search_result.get("score", 0),
                "ingested_at": datetime.now().isoformat(),
            },
        )

    def _save_source(self, item: IngestItem) -> Path:
        """保存原始来源"""
        filename = f"{item.item_id}.md"
        path = self.sources_path / filename

        content = f"""# {item.title}

> Source: {item.source_url}
> Ingested: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

{item.content}

---
*Auto-ingested from Deep Research*
"""

        path.write_text(content, encoding="utf-8")

        return path

    def _create_wiki_page(self, item: IngestItem) -> str:
        """创建 Wiki 页面"""
        self.wiki_path.mkdir(parents=True, exist_ok=True)

        page_id = f"research-{item.item_id}"
        filename = f"{page_id}.md"
        path = self.wiki_path / filename

        content = f"""# Research: {item.title}

---
type: research
sources:
  - {item.source_url}
research_topic: {item.metadata.get('research_topic', 'Unknown')}
score: {item.metadata.get('score', 0)}
created: {datetime.now().strftime('%Y-%m-%d')}
---

## For future Claude

This page was auto-generated from Deep Research.
Source: {item.source_url}

---

## Summary

{item.content[:1000]}{'...' if len(item.content) > 1000 else ''}

## Source

- [{item.title}]({item.source_url})

---
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

        path.write_text(content, encoding="utf-8")

        return page_id

    def synthesize_research(
        self,
        items: list[IngestItem],
        research_topic: str,
        llm_client: Optional[object] = None,
    ) -> str:
        """
        综合研究结果

        Args:
            items: 摄入项列表
            research_topic: 研究主题
            llm_client: LLM 客户端（可选）

        Returns:
            综合页面 ID
        """
        # 生成综合页面
        page_id = f"synthesis-{hashlib.md5(research_topic.encode()).hexdigest()[:12]}"
        path = self.wiki_path / f"{page_id}.md"

        # 构建内容
        lines = [
            f"# Synthesis: {research_topic}",
            "",
            "---",
            f"type: research-synthesis",
            f"created: {datetime.now().strftime('%Y-%m-%d')}",
            "---",
            "",
            "## For future Claude",
            "",
            f"This synthesis combines {len(items)} sources on '{research_topic}'.",
            "",
            "---",
            "",
            "## Sources",
            "",
        ]

        for item in items:
            lines.append(f"- [[{item.item_id}]] {item.title}")

        lines.extend([
            "",
            "---",
            "",
            "*Auto-synthesized from Deep Research*",
        ])

        path.write_text("\n".join(lines), encoding="utf-8")

        return page_id
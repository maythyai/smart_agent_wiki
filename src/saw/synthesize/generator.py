"""
Page Generator - 综合页面生成器

自动生成综合页面
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import json


@dataclass
class SynthesisPage:
    """
    综合页面

    AI-first 格式的综合页面
    """
    page_id: str
    title: str
    content: str
    patterns: list[str]  # pattern IDs
    clusters: list[str]  # cluster IDs
    confidence: float
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    sources: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)  # wiki links
    metadata: dict = field(default_factory=dict)

    def to_markdown(self) -> str:
        """
        转换为 markdown 格式

        AI-first 格式：包含 For future Claude 前言
        """
        lines = [
            f"# {self.title}",
            "",
            "> [!ai-first] This page is optimized for LLM retrieval",
            f"> Generated: {self.created_at.strftime('%Y-%m-%d')}",
            f"> Confidence: {self.confidence:.2f}",
            "",
            "## For future Claude",
            "",
            f"This synthesis page aggregates {len(self.patterns)} patterns "
            f"and {len(self.clusters)} claim clusters. "
            f"Sources: {', '.join(self.sources[:5])}.",
            "",
            "---",
            "",
            "## Summary",
            "",
            self.content,
            "",
            "## Sources",
            "",
        ]

        for source in self.sources[:10]:
            lines.append(f"- [[{source}]]")

        lines.extend([
            "",
            "## Related Pages",
            "",
        ])

        for link in self.links[:10]:
            lines.append(f"- [[{link}]]")

        lines.extend([
            "",
            "---",
            "",
            f"*Last updated: {self.last_updated.strftime('%Y-%m-%d %H:%M')}*",
        ])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "page_id": self.page_id,
            "title": self.title,
            "content": self.content,
            "patterns": self.patterns,
            "clusters": self.clusters,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "sources": self.sources,
            "links": self.links,
            "metadata": self.metadata,
        }


@dataclass
class GenerationResult:
    """生成结果"""
    pages: list[SynthesisPage] = field(default_factory=list)
    generation_time: float = 0.0


class PageGenerator:
    """
    综合页面生成器

    根据模式和聚合簇生成综合页面：
    1. 合并模式和聚合信息
    2. 生成页面内容
    3. 创建 AI-first 格式
    4. 链接到原始来源
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
    ):
        """
        初始化页面生成器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir

    def generate(
        self,
        patterns: list[dict],
        clusters: list[dict],
    ) -> GenerationResult:
        """
        生成综合页面

        Args:
            patterns: 模式列表
            clusters: 聚合簇列表

        Returns:
            生成结果
        """
        start_time = datetime.now()
        pages = []

        # 为每个模式和簇组合生成页面
        for pattern in patterns:
            # 找到相关的簇
            related_clusters = [
                c for c in clusters
                if self._is_related(pattern, c)
            ]

            if not related_clusters:
                continue

            page = SynthesisPage(
                page_id=self._generate_id(pattern["pattern_id"]),
                title=self._generate_title(pattern),
                content=self._generate_content(pattern, related_clusters),
                patterns=[pattern["pattern_id"]],
                clusters=[c["cluster_id"] for c in related_clusters],
                confidence=self._calculate_confidence(pattern, related_clusters),
                sources=self._collect_sources(related_clusters),
                links=self._generate_links(pattern, related_clusters),
                metadata={
                    "pattern_name": pattern.get("name", ""),
                    "pattern_occurrences": pattern.get("occurrences", 0),
                },
            )

            pages.append(page)

        generation_time = (datetime.now() - start_time).total_seconds()

        return GenerationResult(
            pages=pages,
            generation_time=generation_time,
        )

    def _is_related(self, pattern: dict, cluster: dict) -> bool:
        """检查模式与簇是否相关"""
        # 简单实现：检查关键词是否出现在主题中
        pattern_keywords = pattern.get("keywords", [])
        cluster_topic = cluster.get("topic", "").lower()

        for keyword in pattern_keywords:
            if keyword.lower() in cluster_topic:
                return True

        return False

    def _generate_id(self, base: str) -> str:
        """生成页面 ID"""
        return f"syn-{base}"

    def _generate_title(self, pattern: dict) -> str:
        """生成页面标题"""
        name = pattern.get("name", "Unnamed Pattern")
        return f"Synthesis: {name}"

    def _generate_content(
        self,
        pattern: dict,
        clusters: list[dict],
    ) -> str:
        """生成页面内容"""
        lines = [
            "## Pattern Analysis",
            "",
            f"This synthesis page captures a recurring pattern identified "
            f"across {pattern.get('occurrences', 0)} occurrences.",
            "",
            f"**Pattern**: {pattern.get('name', 'Unknown')}",
            f"**Keywords**: {', '.join(pattern.get('keywords', []))}",
            "",
            "## Aggregated Claims",
            "",
        ]

        for cluster in clusters[:5]:
            lines.append(f"### {cluster.get('topic', 'General')}")
            lines.append("")
            lines.append(cluster.get("summary", ""))
            lines.append(f"*Confidence: {cluster.get('confidence', 0):.2f}*")
            lines.append("")

        return "\n".join(lines)

    def _calculate_confidence(
        self,
        pattern: dict,
        clusters: list[dict],
    ) -> float:
        """计算页面置信度"""
        pattern_conf = pattern.get("confidence", 0.5)
        cluster_confs = [c.get("confidence", 0.5) for c in clusters]

        # 加权平均
        if cluster_confs:
            return (pattern_conf * 0.4 + sum(cluster_confs) / len(cluster_confs) * 0.6)
        return pattern_conf

    def _collect_sources(self, clusters: list[dict]) -> list[str]:
        """收集所有来源"""
        sources = set()
        for cluster in clusters:
            for source in cluster.get("sources", []):
                sources.add(source)
        return list(sources)[:10]

    def _generate_links(
        self,
        pattern: dict,
        clusters: list[dict],
    ) -> list[str]:
        """生成 wiki 链接"""
        links = []

        # 添加来源链接
        for source in pattern.get("sources", []):
            links.append(f"Source/{source}")

        # 添加簇链接
        for cluster in clusters:
            links.append(f"Cluster/{cluster['cluster_id']}")

        return links[:20]

    def save_page(
        self,
        page: SynthesisPage,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        保存页面到文件

        Args:
            page: 综合页面
            output_dir: 输出目录

        Returns:
            文件路径
        """
        output_dir = output_dir or self.output_dir or Path("wiki/synthesis")
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{page.page_id}.md"
        filepath = output_dir / filename

        filepath.write_text(page.to_markdown(), encoding="utf-8")

        return filepath

    def save_all(
        self,
        pages: list[SynthesisPage],
        output_dir: Optional[Path] = None,
    ) -> list[Path]:
        """
        保存所有页面

        Args:
            pages: 页面列表
            output_dir: 输出目录

        Returns:
            文件路径列表
        """
        paths = []
        for page in pages:
            path = self.save_page(page, output_dir)
            paths.append(path)
        return paths
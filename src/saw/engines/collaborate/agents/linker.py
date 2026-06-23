"""Linker Agent - Cross-linking and knowledge graph maintenance.

Per D-01: Cross-link discovery, graph edge maintenance, entity relation extraction.
Per D-02: model_tier='haiku' for high-frequency low-cost operations.
"""
from __future__ import annotations

import json

from saw.adapters.llm.router import LLMRouter
from saw.domain.agent import AgentContext, AgentResult, AgentTask
from saw.engines.collaborate.agents.base import BaseAgent

LINKER_PROMPT = """你是 Smart Agent Wiki 的交叉链接专家。

职责：
- 发现 Wiki 页面间的关联关系
- 维护知识图谱的边
- 提取实体关系

工具权限：saw_search, saw_query
约束：仅发现关系，不创建新内容"""


class LinkerAgent(BaseAgent):
    """Linker agent for cross-link discovery.

    Uses Haiku model for cost-effective relationship detection.
    """

    def __init__(self, llm_router: LLMRouter | None) -> None:
        """Initialize the Linker agent.

        Args:
            llm_router: LLM router for model access (can be None for testing).
        """
        super().__init__(
            name="Linker",
            model_tier="haiku",
            system_prompt=LINKER_PROMPT,
            tools_allowed=["saw_search", "saw_query"],
        )
        self._llm = llm_router

    async def execute(
        self,
        task: AgentTask,
        context: AgentContext,
        tools: list,
    ) -> AgentResult:
        """Execute a linker task.

        Args:
            task: The task to execute.
            context: Execution context.
            tools: Available tools.

        Returns:
            AgentResult with discovered links.
        """
        # If no LLM router, use keyword-based link detection
        if self._llm is None:
            links = self._find_links_fallback(task)
            return AgentResult(
                success=True,
                payload=links,
                confidence=1,
                metadata={"agent": self.name, "model_tier": self.model_tier, "fallback": True},
            )

        messages = self._build_messages(task, context)
        model = "claude-3-5-haiku-latest"
        response = await self._llm.completion(model=model, messages=messages)
        return self._parse_response(response)

    def _parse_response(self, response) -> AgentResult:
        """Parse LLM response into AgentResult."""
        content = response.choices[0].message.content or "{}"
        try:
            data = json.loads(content)
            return AgentResult(
                success=True,
                payload=data,
                confidence=2,
                metadata={"model": "haiku"},
            )
        except json.JSONDecodeError:
            return AgentResult(
                success=True,
                payload={"raw": content},
                confidence=1,
                metadata={"model": "haiku"},
            )

    def _find_links_fallback(self, task: AgentTask) -> dict:
        """Keyword-based link detection when LLM is unavailable."""
        payload = task.payload or {}
        content = payload.get("content", "")
        source_slug = payload.get("source_slug", "")
        other_pages = payload.get("other_pages", [])

        links = []

        # Find explicit wiki links [[slug]]
        import re
        explicit = re.findall(r"\[\[([^\]]+)\]\]", content)
        for link_target in explicit:
            if link_target != source_slug:
                links.append({
                    "source": source_slug,
                    "target": link_target,
                    "type": "explicit",
                    "confidence": 4,
                })

        # Find keyword matches in other pages
        content_lower = content.lower()
        for page in other_pages:
            page_slug = page.get("slug", "")
            page_title = page.get("title", "").lower()
            if page_slug and page_slug != source_slug and page_title:
                if page_title in content_lower:
                    links.append({
                        "source": source_slug,
                        "target": page_slug,
                        "type": "keyword",
                        "confidence": 2,
                    })

        return {
            "links": links,
            "count": len(links),
            "mode": "keyword-based",
        }
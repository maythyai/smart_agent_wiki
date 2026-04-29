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
        # If no LLM router, return mock success for testing
        if self._llm is None:
            return AgentResult(
                success=True,
                payload={"message": "Linker task processed"},
                confidence=1,
                metadata={"agent": self.name, "model_tier": self.model_tier},
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
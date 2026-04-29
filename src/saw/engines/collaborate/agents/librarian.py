"""Librarian Agent - Index maintenance and classification.

Per D-01: Index maintenance, classification, search optimization agent.
Per D-02: model_tier='haiku' for high-frequency low-cost operations.
"""
from __future__ import annotations

import json

from saw.adapters.llm.router import LLMRouter
from saw.domain.agent import AgentContext, AgentResult, AgentTask
from saw.engines.collaborate.agents.base import BaseAgent

LIBRARIAN_PROMPT = """你是 Smart Agent Wiki 的索引管理员。

职责：
- 维护知识库索引结构
- 对页面进行分类和标签管理
- 优化搜索结果排序
- 提取文档元数据

工具权限：saw_search, saw_ingest, saw_status
约束：不得修改 Wiki 页面内容，仅操作索引和元数据"""


class LibrarianAgent(BaseAgent):
    """Librarian agent for index and metadata operations.

    Uses Haiku model for cost-effective high-frequency tasks.
    """

    def __init__(self, llm_router: LLMRouter | None) -> None:
        """Initialize the Librarian agent.

        Args:
            llm_router: LLM router for model access (can be None for testing).
        """
        super().__init__(
            name="Librarian",
            model_tier="haiku",
            system_prompt=LIBRARIAN_PROMPT,
            tools_allowed=["saw_search", "saw_ingest", "saw_status"],
        )
        self._llm = llm_router

    async def execute(
        self,
        task: AgentTask,
        context: AgentContext,
        tools: list,
    ) -> AgentResult:
        """Execute a librarian task.

        Args:
            task: The task to execute.
            context: Execution context.
            tools: Available tools.

        Returns:
            AgentResult with operation outcome.
        """
        # If no LLM router, return mock success for testing
        if self._llm is None:
            return AgentResult(
                success=True,
                payload={"message": "Librarian task processed"},
                confidence=1,
                metadata={"agent": self.name, "model_tier": self.model_tier},
            )

        messages = self._build_messages(task, context)
        # Use Haiku model for cost-effective processing
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
                confidence=2,  # Single source by default
                metadata={"model": "haiku"},
            )
        except json.JSONDecodeError:
            return AgentResult(
                success=True,
                payload={"raw": content},
                confidence=1,
                metadata={"model": "haiku"},
            )
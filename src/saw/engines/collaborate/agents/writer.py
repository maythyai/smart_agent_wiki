"""Writer Agent - Content creation and page drafting.

Per D-01: Content creation, summary generation, information synthesis agent.
Per D-02: model_tier='sonnet' for quality-balanced operations.
"""
from __future__ import annotations

import json

from saw.adapters.llm.router import LLMRouter
from saw.domain.agent import AgentContext, AgentResult, AgentTask
from saw.engines.collaborate.agents.base import BaseAgent

WRITER_PROMPT = """你是 Smart Agent Wiki 的内容创作者。

职责：
- 根据 Claims 撰写 Wiki 页面
- 生成文档摘要
- 整合多个来源的信息

工具权限：saw_query, saw_compile, saw_search
约束：所有内容必须有 source_uuid 引用，不得凭空创作"""


class WriterAgent(BaseAgent):
    """Writer agent for content creation.

    Uses Sonnet model for quality-balanced content generation.
    """

    def __init__(self, llm_router: LLMRouter | None) -> None:
        """Initialize the Writer agent.

        Args:
            llm_router: LLM router for model access (can be None for testing).
        """
        super().__init__(
            name="Writer",
            model_tier="sonnet",
            system_prompt=WRITER_PROMPT,
            tools_allowed=["saw_query", "saw_compile", "saw_search"],
        )
        self._llm = llm_router

    async def execute(
        self,
        task: AgentTask,
        context: AgentContext,
        tools: list,
    ) -> AgentResult:
        """Execute a writer task.

        Args:
            task: The task to execute.
            context: Execution context.
            tools: Available tools.

        Returns:
            AgentResult with created content.
        """
        # If no LLM router, return mock success for testing
        if self._llm is None:
            return AgentResult(
                success=True,
                payload={"message": "Writer task processed"},
                confidence=1,
                metadata={"agent": self.name, "model_tier": self.model_tier},
            )

        messages = self._build_messages(task, context)
        model = "claude-sonnet-4-20250514"
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
                metadata={"model": "sonnet"},
            )
        except json.JSONDecodeError:
            return AgentResult(
                success=True,
                payload={"raw": content},
                confidence=1,
                metadata={"model": "sonnet"},
            )
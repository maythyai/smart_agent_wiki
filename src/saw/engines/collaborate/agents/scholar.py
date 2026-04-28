"""Scholar Agent - Deep reasoning and synthesis.

Per D-01: Deep reasoning, multi-source synthesis, complex query processing.
Per D-02: model_tier='opus' for deep reasoning operations.
"""
from __future__ import annotations

from saw.adapters.llm.router import LLMRouter
from saw.domain.agent import AgentContext, AgentResult, AgentTask
from saw.engines.collaborate.agents.base import BaseAgent

SCHOLAR_PROMPT = """你是 Smart Agent Wiki 的深度推理专家。

职责：
- 进行复杂的多步推理
- 综合多个来源生成综述
- 处理需要深度理解的问题

工具权限：saw_query, saw_search, saw_compile, saw_verify
约束：高成本操作，仅在需要深度推理时调用"""


class ScholarAgent(BaseAgent):
    """Scholar agent for deep reasoning.

    Uses Opus model for complex multi-step reasoning.
    """

    def __init__(self, llm_router: LLMRouter | None) -> None:
        """Initialize the Scholar agent.

        Args:
            llm_router: LLM router for model access (can be None for testing).
        """
        super().__init__(
            name="Scholar",
            model_tier="opus",
            system_prompt=SCHOLAR_PROMPT,
            tools_allowed=["saw_query", "saw_search", "saw_compile", "saw_verify"],
        )
        self._llm = llm_router

    async def execute(
        self,
        task: AgentTask,
        context: AgentContext,
        tools: list,
    ) -> AgentResult:
        """Execute a scholar task.

        Args:
            task: The task to execute.
            context: Execution context.
            tools: Available tools.

        Returns:
            AgentResult with reasoning output.
        """
        # If no LLM router, return mock success for testing
        if self._llm is None:
            return AgentResult(
                success=True,
                payload={"message": "Scholar task processed"},
                confidence=1,
                metadata={"agent": self.name, "model_tier": self.model_tier},
            )

        messages = self._build_messages(task, context)
        model = "claude-opus-4-20250514"
        response = await self._llm.completion(model=model, messages=messages)
        return self._parse_response(response)

    def _parse_response(self, response) -> AgentResult:
        """Parse LLM response into AgentResult."""
        import json

        content = response.choices[0].message.content or "{}"
        try:
            data = json.loads(content)
            return AgentResult(
                success=True,
                payload=data,
                confidence=3,  # Scholar outputs have higher default confidence
                metadata={"model": "opus"},
            )
        except json.JSONDecodeError:
            return AgentResult(
                success=True,
                payload={"raw": content},
                confidence=2,
                metadata={"model": "opus"},
            )
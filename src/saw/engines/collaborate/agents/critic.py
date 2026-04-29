"""Critic Agent - Quality review and contradiction detection.

Per D-01: Quality review, contradiction detection, improvement suggestions agent.
Per D-02: model_tier='sonnet' for quality-balanced operations.
"""
from __future__ import annotations

import json

from saw.adapters.llm.router import LLMRouter
from saw.domain.agent import AgentContext, AgentResult, AgentTask
from saw.engines.collaborate.agents.base import BaseAgent

CRITIC_PROMPT = """你是 Smart Agent Wiki 的质量审核员。

职责：
- 审核草稿质量，评估 confidence 级别
- 检测内容矛盾和逻辑问题
- 提供具体的改进建议

输出格式：
- confidence: 1-4 (对应 Unverified 到 Human Verified)
- issues: 问题列表
- suggestions: 改进建议"""


class CriticAgent(BaseAgent):
    """Critic agent for quality review.

    Uses Sonnet model for balanced quality analysis.
    """

    def __init__(self, llm_router: LLMRouter | None) -> None:
        """Initialize the Critic agent.

        Args:
            llm_router: LLM router for model access (can be None for testing).
        """
        super().__init__(
            name="Critic",
            model_tier="sonnet",
            system_prompt=CRITIC_PROMPT,
            tools_allowed=["saw_query", "saw_verify", "saw_lint"],
        )
        self._llm = llm_router

    async def execute(
        self,
        task: AgentTask,
        context: AgentContext,
        tools: list,
    ) -> AgentResult:
        """Execute a critic task.

        Args:
            task: The task to execute.
            context: Execution context.
            tools: Available tools.

        Returns:
            AgentResult with review findings.
        """
        # If no LLM router, return mock success for testing
        if self._llm is None:
            return AgentResult(
                success=True,
                payload={"message": "Critic task processed"},
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
            confidence = data.get("confidence", 2)
            return AgentResult(
                success=True,
                payload=data,
                confidence=min(4, max(1, confidence)),  # Clamp to 1-4
                metadata={"model": "sonnet"},
            )
        except json.JSONDecodeError:
            return AgentResult(
                success=True,
                payload={"raw": content},
                confidence=1,
                metadata={"model": "sonnet"},
            )
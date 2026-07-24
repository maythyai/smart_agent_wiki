"""Scholar Agent - Deep reasoning and synthesis.

Per D-01: Deep reasoning, multi-source synthesis, complex query processing.
Per D-02: model_tier='opus' for deep reasoning operations.
"""
from __future__ import annotations

import json

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

    def __init__(self, llm_router: LLMRouter | None, feedback_engine=None) -> None:
        """Initialize the Scholar agent.

        Args:
            llm_router: LLM router for model access (can be None for testing).
            feedback_engine: Optional FeedbackEngine for submitting change
                requests when research proposes updates to existing pages.
        """
        super().__init__(
            name="Scholar",
            model_tier="opus",
            system_prompt=SCHOLAR_PROMPT,
            tools_allowed=["saw_query", "saw_search", "saw_compile", "saw_verify"],
        )
        self._llm = llm_router
        self._feedback = feedback_engine

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
        # If no LLM router, use aggregation-based research
        if self._llm is None:
            research = self._research_fallback(task)
            self._submit_cr_if_needed(research, task)
            return AgentResult(
                success=True,
                payload=research,
                confidence=2,
                metadata={"agent": self.name, "model_tier": self.model_tier, "fallback": True},
            )

        messages = self._build_messages(task, context)
        model = "claude-opus-4-20250514"
        response = await self._llm.completion(model=model, messages=messages)
        result = self._parse_response(response)
        self._submit_cr_if_needed(result.payload if isinstance(result.payload, dict) else {}, task)
        return result

    def _submit_cr_if_needed(self, research: dict, task: AgentTask) -> None:
        """Submit a ChangeRequest when research targets an existing page.

        Scholar proposes changes via CR (requiring approval) rather than
        directly modifying stable knowledge. Best-effort.
        """
        if self._feedback is None or not isinstance(research, dict):
            return
        try:
            payload = task.payload or {}
            target_page = payload.get("target_page") or payload.get("page")
            # Only open CR when there's an explicit target page to update
            if not target_page:
                return

            proposed = research.get("summary") or research.get("content") or ""
            if not proposed:
                return

            topic = research.get("topic", target_page)
            self._feedback.create_cr(
                title=f"Scholar research update: {topic}",
                target_page=target_page,
                proposed_content=str(proposed),
                creator="agent:Scholar",
                description=f"Research synthesis from {research.get('source_count', 0)} sources",
            )
        except Exception:  # noqa: BLE001 — feedback is best-effort
            pass

    def _parse_response(self, response) -> AgentResult:
        """Parse LLM response into AgentResult."""
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

    def _research_fallback(self, task: AgentTask) -> dict:
        """Aggregation-based research when LLM is unavailable."""
        payload = task.payload or {}
        topic = payload.get("topic", "Unknown")
        sources = payload.get("sources", [])

        # Aggregate statistics from sources
        source_count = len(sources)
        total_claims = sum(s.get("claims_count", 0) for s in sources if isinstance(s, dict))

        # Extract common themes (simple word frequency)
        all_content = " ".join(s.get("content", "") for s in sources if isinstance(s, dict))
        words = all_content.lower().split()
        stop_words = {"the", "is", "are", "was", "were", "and", "or", "a", "an", "in", "on", "to", "for"}
        word_freq = {}
        for w in words:
            w = w.strip(".,;:!?")
            if len(w) >= 5 and w not in stop_words:
                word_freq[w] = word_freq.get(w, 0) + 1
        themes = sorted(word_freq.items(), key=lambda x: -x[1])[:10]

        return {
            "topic": topic,
            "source_count": source_count,
            "total_claims": total_claims,
            "themes": [w for w, _ in themes],
            "summary": f"Found {source_count} sources with {total_claims} claims on '{topic}'",
            "mode": "aggregation",
        }
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

    def __init__(self, llm_router: LLMRouter | None, feedback_engine=None) -> None:
        """Initialize the Critic agent.

        Args:
            llm_router: LLM router for model access (can be None for testing).
            feedback_engine: Optional FeedbackEngine for opening knowledge issues
                when contradictions or quality problems are detected.
        """
        super().__init__(
            name="Critic",
            model_tier="sonnet",
            system_prompt=CRITIC_PROMPT,
            tools_allowed=["saw_query", "saw_verify", "saw_lint"],
        )
        self._llm = llm_router
        self._feedback = feedback_engine

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
        # If no LLM router, use heuristic-based quality checks
        if self._llm is None:
            review = self._review_fallback(task)
            self._open_issues_if_needed(review, task)
            return AgentResult(
                success=True,
                payload=review,
                confidence=1,
                metadata={"agent": self.name, "model_tier": self.model_tier, "fallback": True},
            )

        messages = self._build_messages(task, context)
        model = "claude-sonnet-4-20250514"
        response = await self._llm.completion(model=model, messages=messages)
        result = self._parse_response(response)
        self._open_issues_if_needed(result.payload if isinstance(result.payload, dict) else {}, task)
        return result

    def _open_issues_if_needed(self, review: dict, task: AgentTask) -> None:
        """Open KnowledgeIssues for contradictions/errors found during review.

        Best-effort: failures here never break the review flow.
        """
        if self._feedback is None or not isinstance(review, dict):
            return
        try:
            from saw.domain.feedback import IssueType

            findings = review.get("findings", [])
            issues = review.get("issues", [])
            problems = findings + (issues if isinstance(issues, list) else [])

            # Only open issues for error/contradiction severity
            serious = [
                p for p in problems
                if isinstance(p, dict)
                and (
                    p.get("severity") == "error"
                    or "contradict" in str(p.get("issue", "")).lower()
                )
            ]
            if not serious:
                return

            payload = task.payload or {}
            affected = payload.get("affected_pages", [])
            if not affected and payload.get("page"):
                affected = [payload["page"]]

            title = f"Critic detected {len(serious)} issue(s)"
            desc = "; ".join(
                str(p.get("issue") or p.get("description") or p) for p in serious[:5]
            )
            self._feedback.create_issue(
                issue_type=IssueType.CHALLENGE,
                title=title,
                description=desc,
                affected_pages=affected,
                reporter="agent:Critic",
            )
        except Exception:  # noqa: BLE001 — feedback is best-effort
            pass

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

    def _review_fallback(self, task: AgentTask) -> dict:
        """Heuristic-based quality review when LLM is unavailable."""
        payload = task.payload or {}
        content = payload.get("content", "")
        findings = []

        # Check content length
        if len(content) < 50:
            findings.append({"severity": "warning", "issue": "Content too short", "suggestion": "Expand content"})

        # Check for structure
        if not content.startswith("#"):
            findings.append({"severity": "info", "issue": "Missing title heading", "suggestion": "Add H1 heading"})

        # Check for citations
        if "[" not in content or "]" not in content:
            findings.append({"severity": "warning", "issue": "No citations found", "suggestion": "Add source references"})

        # Check for TODOs
        if "TODO" in content.upper() or "FIXME" in content.upper():
            findings.append({"severity": "error", "issue": "Contains TODO/FIXME", "suggestion": "Resolve incomplete items"})

        # Calculate quality score (1-4)
        score = 4 - len([f for f in findings if f["severity"] in ("error", "warning")])
        score = max(1, min(4, score))

        return {
            "findings": findings,
            "score": score,
            "passed": score >= 2,
            "mode": "heuristic",
        }
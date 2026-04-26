"""LLM Router with LiteLLM integration.

Per D-21: LiteLLM for multi-LLM support with configurable model.
Per D-10: Single LLM in Phase 1 (multi-LLM deferred to Phase 2).
Per RESEARCH.md Pitfall 6: Use synchronous litellm.completion() for Phase 1 CLI.
"""
from __future__ import annotations

import json
from typing import Any

import litellm

from saw.config.settings import LLMSettings


class LLMRouter:
    """LiteLLM model router with configurable extraction/query models."""

    def __init__(self, settings: LLMSettings) -> None:
        self._settings = settings
        # Default to gpt-4o-mini if extraction_model not configured
        self._extraction_model = settings.extraction_model or "gpt-4o-mini"
        self._query_model = settings.query_model or "gpt-4o-mini"

    def extract_claims(self, text: str, system_prompt: str) -> dict[str, Any]:
        """Extract claims from text using LLM.

        Args:
            text: Document content to extract from.
            system_prompt: Extraction prompt template.

        Returns:
            Parsed JSON dict with claims structure.
        """
        response = litellm.completion(
            model=self._extraction_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=0.1,  # Low temperature for stable extraction (per RESEARCH.md)
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Return empty structure if parsing fails
            return {"claims": []}

    def answer_query(self, context: str, question: str, system_prompt: str) -> str:
        """Answer a query based on context.

        Args:
            context: Compiled context from wiki pages.
            question: User question.
            system_prompt: Query prompt template.

        Returns:
            LLM response text.
        """
        response = litellm.completion(
            model=self._query_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
        )
        return response.choices[0].message.content or ""

    def _check_available(self) -> bool:
        """Check if LLM is reachable via a minimal completion call.

        Returns:
            True if LLM is available, False otherwise.
        """
        try:
            # Try a minimal completion to check availability
            litellm.completion(
                model=self._extraction_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
            )
            return True
        except Exception:
            return False
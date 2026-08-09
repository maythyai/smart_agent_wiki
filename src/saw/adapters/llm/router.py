"""LLM Router with LiteLLM integration.

Per D-21: LiteLLM for multi-LLM support with configurable model.
Per D-10: Single LLM in Phase 1 (multi-LLM deferred to Phase 2).
Per RESEARCH.md Pitfall 6: Use synchronous litellm.completion() for Phase 1 CLI.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import litellm

from saw.config.settings import LLMSettings
from saw.domain.exceptions import LLMError

logger = logging.getLogger(__name__)

# Default timeout for all LLM calls (seconds)
_DEFAULT_TIMEOUT: int = 30

# Retry configuration
_MAX_RETRIES: int = 3
_INITIAL_BACKOFF_S: float = 1.0


def _completion_with_retry(**kwargs: Any) -> Any:
    """Call litellm.completion() with exponential-backoff retry.

    Retries up to ``_MAX_RETRIES`` times on any exception, sleeping
    2^attempt * _INITIAL_BACKOFF_S seconds between attempts (1 s, 2 s, 4 s …).

    Raises:
        LLMError: When all retries are exhausted.
    """
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            return litellm.completion(**kwargs)
        except Exception as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                sleep_s = _INITIAL_BACKOFF_S * (2 ** attempt)
                logger.warning(
                    "LLM call failed (attempt %d/%d): %s — retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES + 1,
                    exc,
                    sleep_s,
                )
                time.sleep(sleep_s)

    raise LLMError(
        f"LLM call failed after {_MAX_RETRIES + 1} attempts: {last_exc}"
    ) from last_exc


# Mapping from model-name prefixes to the environment variable that must be set
# for the provider to be reachable.  Extend as new providers are added.
_MODEL_ENV_KEYS: dict[str, str] = {
    "gpt": "OPENAI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "google": "GOOGLE_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "cohere": "COHERE_API_KEY",
    "replicate": "REPLICATE_API_KEY",
    "huggingface": "HUGGINGFACE_API_KEY",
    "azure": "AZURE_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}


def _required_env_var(model: str) -> str | None:
    """Return the API-key env var name expected for *model*, or None."""
    model_lower = model.lower()
    for prefix, env_var in _MODEL_ENV_KEYS.items():
        if prefix in model_lower:
            return env_var
    return None


class LLMRouter:
    """LiteLLM model router with configurable extraction/query models."""

    def __init__(self, settings: LLMSettings) -> None:
        self._settings = settings
        # Default to gpt-4o-mini if extraction_model not configured
        self._extraction_model = settings.extraction_model or "gpt-4o-mini"
        self._query_model = settings.query_model or "gpt-4o-mini"
        self._api_base = getattr(settings, "api_base", "") or ""
        self._api_key = getattr(settings, "api_key", "") or ""
        self._timeout = getattr(settings, "timeout", 0) or _DEFAULT_TIMEOUT
        self._enable_thinking = getattr(settings, "enable_thinking", True)

    @staticmethod
    def _is_ollama_model(model: str) -> bool:
        """True when *model* routes through litellm's native Ollama provider."""
        return model.lower().startswith("ollama/")

    def _endpoint_kwargs(self, model: str) -> dict[str, Any]:
        """Return litellm kwargs for routing to a custom endpoint.

        When api_base is configured (e.g. Ollama at http://localhost:11434),
        litellm receives api_base; an api_key is only injected when required
        (OpenAI-compatible endpoints demand a non-empty key, native Ollama
        ignores it).

        Reasoning control depends on the provider:
        - ``ollama/`` models talk to /api/chat, where qwen3-style reasoning
          models default to thinking ON (slow, and combined with json format
          it can yield empty content). Disable it with the native ``think``
          parameter.
        - OpenAI-compatible endpoints use ``enable_thinking`` in extra_body.
        """
        kwargs: dict[str, Any] = {}
        if self._api_base:
            kwargs["api_base"] = self._api_base
            if self._api_key:
                kwargs["api_key"] = self._api_key
            elif not self._is_ollama_model(model):
                kwargs["api_key"] = "ollama"  # placeholder, ignored server-side
        if not self._enable_thinking:
            if self._is_ollama_model(model):
                kwargs["think"] = False
            else:
                kwargs["extra_body"] = {"enable_thinking": False}
        return kwargs

    def extract_claims(self, text: str, system_prompt: str) -> dict[str, Any]:
        """Extract claims from text using LLM.

        Args:
            text: Document content to extract from.
            system_prompt: Extraction prompt template.

        Returns:
            Parsed JSON dict with claims structure.

        Raises:
            LLMError: When the LLM call fails or the response is not valid JSON.
        """
        response = _completion_with_retry(
            model=self._extraction_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=0.1,  # Low temperature for stable extraction (per RESEARCH.md)
            response_format={"type": "json_object"},
            timeout=self._timeout,
            **self._endpoint_kwargs(self._extraction_model),
        )
        content = response.choices[0].message.content or ""
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            logger.warning(
                "LLM returned invalid JSON for extract_claims (model=%s): %s",
                self._extraction_model,
                content[:200],
            )
            raise LLMError(
                f"LLM returned unparseable JSON from {self._extraction_model}: {exc}"
            ) from exc

    def answer_query(self, context: str, question: str, system_prompt: str) -> str:
        """Answer a query based on context.

        Args:
            context: Compiled context from wiki pages.
            question: User question.
            system_prompt: Query prompt template.

        Returns:
            LLM response text.

        Raises:
            LLMError: When the LLM call fails after all retries.
        """
        response = _completion_with_retry(
            model=self._query_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
            timeout=self._timeout,
            **self._endpoint_kwargs(self._query_model),
        )
        return response.choices[0].message.content or ""

    def _check_available(self) -> bool:
        """Check whether the configured LLM provider is likely reachable.

        Instead of making a real API call (which costs tokens and latency), this
        validates that the expected API-key environment variable is set for the
        configured model.  Returns True when no known provider prefix is matched
        (optimistic fallback for custom / local models).

        When a custom api_base is configured (Ollama/vLLM/etc.), the endpoint is
        assumed reachable and env-var checks are skipped.
        """
        if self._api_base:
            return True
        for model in (self._extraction_model, self._query_model):
            env_var = _required_env_var(model)
            if env_var and not os.environ.get(env_var):
                logger.warning(
                    "LLM provider env var %s is not set for model %s",
                    env_var,
                    model,
                )
                return False
        return True

    # ─── Generic completion API (used by collaborate agents & compile engine) ──

    def complete(
        self,
        model: str | None = None,
        messages: list[dict[str, str]] | None = None,
        prompt: str | None = None,
        system: str | None = None,
        temperature: float = 0.7,
        response_format: dict[str, str] | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> Any:
        """Generic synchronous completion call.

        Accepts either ``messages`` (chat format) or ``prompt`` (single user
        message). Returns the raw litellm response object so callers can access
        ``.choices[0].message.content``.

        Args:
            model: Model name. Defaults to query_model.
            messages: Chat-format messages list.
            prompt: Single user prompt (alternative to messages).
            system: Optional system prompt (used with prompt arg).
            temperature: Sampling temperature.
            response_format: Optional format spec (e.g. {"type": "json_object"}).
            timeout: Per-call timeout in seconds.

        Raises:
            LLMError: When all retries are exhausted.
        """
        if messages is None:
            if prompt is None:
                raise LLMError("complete() requires either messages or prompt")
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

        resolved_model = model or self._query_model
        call_kwargs: dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
            "temperature": temperature,
            "timeout": timeout or self._timeout,
            **self._endpoint_kwargs(resolved_model),
            **kwargs,
        }
        if response_format is not None:
            call_kwargs["response_format"] = response_format

        return _completion_with_retry(**call_kwargs)

    async def completion(
        self,
        model: str | None = None,
        messages: list[dict[str, str]] | None = None,
        prompt: str | None = None,
        system: str | None = None,
        temperature: float = 0.7,
        response_format: dict[str, str] | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> Any:
        """Async completion call used by collaborate agents.

        Wraps the synchronous retry logic in a thread executor so it can be
        awaited from async agent code without blocking the event loop.

        Returns:
            Raw litellm response object with ``.choices[0].message.content``.
        """
        import asyncio

        return await asyncio.to_thread(
            self.complete,
            model=model,
            messages=messages,
            prompt=prompt,
            system=system,
            temperature=temperature,
            response_format=response_format,
            timeout=timeout,
            **kwargs,
        )

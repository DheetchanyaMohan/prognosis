"""LLM client: provider-independent chat model access.

This is the only module in the codebase that imports a provider's SDK
directly. LangGraph nodes never import anthropic (or any other provider
SDK) themselves — they depend on the ChatModel Protocol below and get a
concrete instance from get_chat_model(). Swapping or adding a provider
means writing one class satisfying ChatModel and registering it in
get_chat_model(); no node changes.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from functools import lru_cache
from typing import Protocol

from app.core.config import get_settings


class ChatModel(Protocol):
    """The interface every LLM-calling node depends on."""

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Returns the full completion text in one call."""
        ...

    def stream_complete(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        """Yields the completion text incrementally, chunk by chunk."""
        ...


class LLMProviderError(Exception):
    """Raised when a provider call fails after exhausting all retries."""


class AnthropicChatModel:
    """ChatModel implementation backed by the Anthropic API.

    Retries a fixed set of transient errors (connection issues, rate
    limits, transient 5xx/overload responses) with exponential backoff;
    non-transient errors (auth, bad request, etc.) propagate immediately
    since retrying them can't help.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int = 2000,
        max_retries: int | None = None,
        retry_backoff_seconds: float | None = None,
    ) -> None:
        import anthropic

        settings = get_settings()
        self._client = anthropic.Anthropic(api_key=api_key or settings.anthropic_api_key)
        self._model = model or settings.anthropic_model
        self._max_tokens = max_tokens
        self._max_retries = max_retries if max_retries is not None else settings.llm_max_retries
        self._retry_backoff_seconds = (
            retry_backoff_seconds
            if retry_backoff_seconds is not None
            else settings.llm_retry_backoff_seconds
        )

    def _retryable_errors(self) -> tuple[type[Exception], ...]:
        import anthropic

        return (
            anthropic.APIConnectionError,
            anthropic.APITimeoutError,
            anthropic.RateLimitError,
            anthropic.InternalServerError,
            anthropic.OverloadedError,
        )

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                return "".join(block.text for block in response.content if block.type == "text")
            except self._retryable_errors() as exc:
                last_error = exc
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_backoff_seconds * (2**attempt))

        raise LLMProviderError(
            f"Anthropic completion failed after {self._max_retries} attempt(s): {last_error}"
        ) from last_error

    def stream_complete(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        with self._client.messages.stream(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            yield from stream.text_stream


@lru_cache
def get_chat_model(provider: str | None = None) -> ChatModel:
    """Factory returning a cached ChatModel for `provider` (defaults to
    settings.llm_provider). This is the single place a new provider gets
    registered; raises ValueError for anything unrecognized rather than
    silently falling back to a default.
    """
    settings = get_settings()
    resolved_provider = provider or settings.llm_provider

    if resolved_provider == "anthropic":
        return AnthropicChatModel()

    raise ValueError(f"Unknown LLM provider: {resolved_provider!r}")
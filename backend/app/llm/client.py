"""LLM client: provider-independent chat model access.

This is the only module in the codebase that imports a provider's SDK
directly. LangGraph nodes never import anthropic/google-genai (or any
other provider SDK) themselves — they depend on the ChatModel Protocol
below and get a concrete instance from get_chat_model(). Swapping or
adding a provider means writing one class satisfying ChatModel and
registering it in get_chat_model(); no node changes. Two providers are
registered today: Anthropic and Gemini.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Protocol

from app.core.config import get_settings

if TYPE_CHECKING:
    from google.genai import errors


class ChatModel(Protocol):
    """The interface every LLM-calling node depends on."""

    def complete(
        self, system_prompt: str, user_prompt: str, response_schema: Any | None = None
    ) -> str:
        """Returns the full completion text in one call.

        `response_schema` is an optional structural hint (a Pydantic
        model, or a `list[SomeModel]` generic alias) describing the
        expected shape of the response. Providers with native
        schema-constrained JSON output (currently: Gemini) use it to
        guarantee well-formed, unfenced JSON directly from the API,
        instead of relying on the prompt text alone to ask for JSON —
        which chat-tuned models routinely ignore by wrapping the
        response in a markdown code fence regardless of instructions.
        Providers without an equivalent native mode (currently:
        Anthropic) accept the parameter but ignore it.
        """
        ...

    def complete_structured(
        self, system_prompt: str, user_prompt: str, response_schema: Any
    ) -> Any:
        """Returns already-parsed, schema-conformant Python data (a list
        or dict of plain values — not validated model instances; Pydantic
        validation still happens once, centrally, in
        app.llm.structured_output).

        Providers with native structured output (Gemini) return the
        provider's own pre-parsed result directly — this is what lets
        callers stop doing their own json.loads() on raw text entirely,
        avoiding a whole class of "the model's text wasn't quite valid
        JSON" failures (markdown fences, truncation, etc.) that a second,
        redundant parse step can't fix anyway if the provider's own parse
        already failed. Providers without native support (Anthropic) fall
        back to requesting JSON via complete() and parsing the text
        themselves.
        """
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

    def complete(
        self, system_prompt: str, user_prompt: str, response_schema: Any | None = None
    ) -> str:
        # response_schema is accepted for Protocol conformance but unused here:
        # Anthropic has no equivalent "constrain output to this JSON schema"
        # mode wired up yet (it would need tool-use forcing, a different
        # mechanism from Gemini's response_schema) — Future Enhancement.
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

    def complete_structured(
        self, system_prompt: str, user_prompt: str, response_schema: Any
    ) -> Any:
        # No native structured-output mode wired up for Anthropic yet
        # (Future Enhancement — would need tool-use forcing). Falls back
        # to requesting JSON via complete() and parsing the text
        # ourselves; json.JSONDecodeError propagates to the caller
        # (app.llm.structured_output), same as it always has.
        import json

        raw_text = self.complete(system_prompt, user_prompt, response_schema=response_schema)
        return json.loads(raw_text)


class GeminiChatModel:
    """ChatModel implementation backed by the Google Gemini API.

    Retries transient server errors (5xx) and rate-limit responses (429)
    with exponential backoff; other client errors (auth, bad request,
    etc.) propagate immediately since retrying them can't help. 429
    arrives as a ClientError in this SDK's hierarchy (it's a 4xx status),
    so retryability is decided by inspecting the status code, not just
    the exception class — unlike AnthropicChatModel, where each retryable
    condition already has its own distinct exception type.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_output_tokens: int = 2000,
        max_retries: int | None = None,
        retry_backoff_seconds: float | None = None,
    ) -> None:
        from google import genai

        settings = get_settings()
        self._client = genai.Client(api_key=api_key or settings.gemini_api_key)
        self._model = model or settings.gemini_model
        self._max_output_tokens = max_output_tokens
        self._max_retries = max_retries if max_retries is not None else settings.llm_max_retries
        self._retry_backoff_seconds = (
            retry_backoff_seconds
            if retry_backoff_seconds is not None
            else settings.llm_retry_backoff_seconds
        )

    def _is_retryable(self, exc: errors.APIError) -> bool:
        from google.genai import errors as errors_module

        if isinstance(exc, errors_module.ServerError):
            return True
        if isinstance(exc, errors_module.ClientError):
            return exc.code == 429
        return False

    def _build_config(self, system_prompt: str, response_schema: Any | None = None) -> Any:
        from google.genai import types

        config_kwargs: dict[str, Any] = {
            "system_instruction": system_prompt,
            "max_output_tokens": self._max_output_tokens,
        }
        if response_schema is not None:
            from pydantic import TypeAdapter

            # Deliberately response_json_schema, not response_schema.
            # response_schema maps to Gemini's restricted Schema proto,
            # which does not support `additionalProperties` outside Vertex
            # Enterprise mode — but our models use extra="forbid", which
            # always produces `additionalProperties: false` in their JSON
            # schema. That field survives the SDK's own client-side check
            # (which only guards *truthy* values) and gets rejected by the
            # live API instead ("Unknown name additional_properties").
            # response_json_schema is the SDK's own documented alternative
            # for exactly this: real JSON Schema, with additionalProperties
            # explicitly on its supported-fields list. TypeAdapter (not
            # hand-rolled schema construction) is pydantic's own canonical
            # way to get a JSON Schema for both a single model and a
            # generic like list[SomeModel].
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_json_schema"] = TypeAdapter(response_schema).json_schema()

            # Gemini models allocate a "thinking" token budget that shares
            # the same output-token pool as the actual answer — with no
            # control at all, a model can spend the whole pool on hidden
            # thinking, leaving zero content parts for the JSON payload
            # itself (response.text becomes None, not just malformed).
            # Structured extraction from evidence we already gathered
            # doesn't need chain-of-thought — any reasoning the model
            # wants to show belongs in the explanation/rationale fields of
            # the schema itself, not hidden thinking tokens.
            #
            # thinking_level, not thinking_budget: thinking_budget is
            # retired starting with Gemini 3.5 models and causes a 400
            # INVALID_ARGUMENT if set at all, regardless of value.
            # thinking_level is the documented replacement (a coarse enum:
            # MINIMAL/LOW/MEDIUM/HIGH, no explicit "disabled" value).
            # MINIMAL is the lowest available setting, not a guaranteed
            # zero — watch thoughts_token_count in practice.
            config_kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_level=types.ThinkingLevel.MINIMAL
            )
        return types.GenerateContentConfig(**config_kwargs)

    def complete(
        self, system_prompt: str, user_prompt: str, response_schema: Any | None = None
    ) -> str:
        from google.genai import errors as errors_module

        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=user_prompt,
                    config=self._build_config(system_prompt, response_schema),
                )
                return response.text or ""
            except errors_module.APIError as exc:
                if not self._is_retryable(exc):
                    raise
                last_error = exc
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_backoff_seconds * (2**attempt))

        raise LLMProviderError(
            f"Gemini completion failed after {self._max_retries} attempt(s): {last_error}"
        ) from last_error

    def stream_complete(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        stream = self._client.models.generate_content_stream(
            model=self._model,
            contents=user_prompt,
            config=self._build_config(system_prompt),
        )
        for chunk in stream:
            if chunk.text:
                yield chunk.text

    def _diagnose_empty_response(self, response: Any) -> str:
        """Builds an actionable message from the response's own diagnostic
        fields when .parsed comes back empty — a raw 'not valid JSON'
        message is useless for telling apart truncation, safety blocking,
        or a genuine malformed response, and this is what needed
        inspecting to find the previous fix's real remaining gap."""
        candidates = response.candidates or []
        finish_reason = candidates[0].finish_reason if candidates else None
        usage = response.usage_metadata
        thoughts_tokens = usage.thoughts_token_count if usage else None
        return (
            f"finish_reason={finish_reason}, thoughts_token_count={thoughts_tokens}, "
            f"raw_text={response.text!r}"
        )

    def complete_structured(
        self, system_prompt: str, user_prompt: str, response_schema: Any
    ) -> Any:
        from google.genai import errors as errors_module

        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=user_prompt,
                    config=self._build_config(system_prompt, response_schema),
                )
                if response.parsed is not None:
                    return response.parsed
                # The SDK's own parse attempt (json.loads on response.text)
                # already failed or there was no text at all — a second
                # attempt on our side can't recover data that was never
                # there. Surface why, rather than a generic parse error.
                raise LLMProviderError(
                    f"Gemini returned no parseable structured output "
                    f"({self._diagnose_empty_response(response)})"
                )
            except errors_module.APIError as exc:
                if not self._is_retryable(exc):
                    raise
                last_error = exc
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_backoff_seconds * (2**attempt))

        raise LLMProviderError(
            f"Gemini completion failed after {self._max_retries} attempt(s): {last_error}"
        ) from last_error


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
    if resolved_provider == "gemini":
        return GeminiChatModel()

    raise ValueError(f"Unknown LLM provider: {resolved_provider!r}")
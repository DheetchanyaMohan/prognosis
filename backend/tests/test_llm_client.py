from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.llm.client import AnthropicChatModel, LLMProviderError, get_chat_model


def _request() -> httpx.Request:
    return httpx.Request("POST", "https://api.anthropic.com/v1/messages")


def _response(status: int = 500) -> httpx.Response:
    return httpx.Response(status, request=_request())


def _fake_completion(text: str) -> SimpleNamespace:
    """Mimics the shape of an Anthropic Message response enough for
    AnthropicChatModel.complete to extract text from it."""
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


@pytest.fixture(autouse=True)
def _no_real_sleep():
    """Retry tests use backoff purely for the code path, not real timing."""
    with patch("app.llm.client.time.sleep"):
        yield


# --- complete: happy path ------------------------------------------------


def test_complete_returns_text_on_first_try() -> None:
    model = AnthropicChatModel(api_key="test-key", max_retries=3, retry_backoff_seconds=0)
    with patch.object(
        model._client.messages, "create", return_value=_fake_completion("hello")
    ) as mock_create:
        result = model.complete("system", "user")

    assert result == "hello"
    assert mock_create.call_count == 1


# --- complete: retry behavior --------------------------------------------


def test_retries_transient_error_then_succeeds() -> None:
    import anthropic

    model = AnthropicChatModel(api_key="test-key", max_retries=3, retry_backoff_seconds=0)
    side_effects = [
        anthropic.APIConnectionError(request=_request()),
        anthropic.RateLimitError("rate limited", response=_response(429), body=None),
        _fake_completion("succeeded on third try"),
    ]
    with patch.object(model._client.messages, "create", side_effect=side_effects) as mock_create:
        result = model.complete("system", "user")

    assert result == "succeeded on third try"
    assert mock_create.call_count == 3


def test_raises_llm_provider_error_after_exhausting_retries() -> None:
    import anthropic

    model = AnthropicChatModel(api_key="test-key", max_retries=2, retry_backoff_seconds=0)
    with patch.object(
        model._client.messages,
        "create",
        side_effect=anthropic.InternalServerError("down", response=_response(503), body=None),
    ) as mock_create:
        with pytest.raises(LLMProviderError, match="failed after 2 attempt"):
            model.complete("system", "user")

    assert mock_create.call_count == 2


def test_non_retryable_error_propagates_immediately() -> None:
    import anthropic

    model = AnthropicChatModel(api_key="test-key", max_retries=3, retry_backoff_seconds=0)
    with patch.object(
        model._client.messages,
        "create",
        side_effect=anthropic.BadRequestError("bad request", response=_response(400), body=None),
    ) as mock_create:
        with pytest.raises(anthropic.BadRequestError):
            model.complete("system", "user")

    assert mock_create.call_count == 1  # no retry for a non-transient error


# --- stream_complete -----------------------------------------------------


def test_stream_complete_yields_chunks() -> None:
    model = AnthropicChatModel(api_key="test-key")

    fake_stream = MagicMock()
    fake_stream.__enter__.return_value = fake_stream
    fake_stream.__exit__.return_value = False
    fake_stream.text_stream = iter(["hel", "lo"])

    with patch.object(model._client.messages, "stream", return_value=fake_stream):
        chunks = list(model.stream_complete("system", "user"))

    assert chunks == ["hel", "lo"]


# --- get_chat_model factory ------------------------------------------------


def test_get_chat_model_returns_anthropic_for_known_provider() -> None:
    get_chat_model.cache_clear()
    model = get_chat_model("anthropic")
    assert isinstance(model, AnthropicChatModel)
    get_chat_model.cache_clear()


def test_get_chat_model_raises_for_unknown_provider() -> None:
    get_chat_model.cache_clear()
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_chat_model("some_other_provider")
    get_chat_model.cache_clear()


def test_get_chat_model_is_cached() -> None:
    get_chat_model.cache_clear()
    first = get_chat_model("anthropic")
    second = get_chat_model("anthropic")
    assert first is second
    get_chat_model.cache_clear()
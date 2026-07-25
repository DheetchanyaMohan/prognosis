from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.llm.client import AnthropicChatModel, GeminiChatModel, LLMProviderError, get_chat_model


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


# --- AnthropicChatModel: complete_structured (no native mode, falls back) --


def test_anthropic_complete_structured_parses_json_text() -> None:
    model = AnthropicChatModel(api_key="test-key")
    with patch.object(
        model._client.messages, "create", return_value=_fake_completion('[{"a": 1}]')
    ):
        result = model.complete_structured("system", "user", response_schema=list)

    assert result == [{"a": 1}]


def test_anthropic_complete_structured_propagates_json_decode_error() -> None:
    import json

    model = AnthropicChatModel(api_key="test-key")
    with patch.object(
        model._client.messages, "create", return_value=_fake_completion("not json")
    ):
        with pytest.raises(json.JSONDecodeError):
            model.complete_structured("system", "user", response_schema=list)


# --- get_chat_model factory ------------------------------------------------


def test_get_chat_model_returns_anthropic_for_known_provider() -> None:
    get_chat_model.cache_clear()
    model = get_chat_model("anthropic")
    assert isinstance(model, AnthropicChatModel)
    get_chat_model.cache_clear()


def test_get_chat_model_returns_gemini_for_known_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import get_settings

    # Unlike Anthropic's SDK, google-genai requires an API key at client
    # construction time, not just at request time — this must be set
    # before GeminiChatModel() can even be constructed.
    get_settings.cache_clear()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    get_chat_model.cache_clear()

    model = get_chat_model("gemini")
    assert isinstance(model, GeminiChatModel)

    get_chat_model.cache_clear()
    get_settings.cache_clear()


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


# --- GeminiChatModel: happy path -----------------------------------------


def _fake_gemini_response(text: str) -> SimpleNamespace:
    """Mimics the shape of a Gemini GenerateContentResponse enough for
    GeminiChatModel.complete to extract text from it (the SDK exposes
    `.text` as a computed property)."""
    return SimpleNamespace(text=text)


def test_gemini_complete_returns_text_on_first_try() -> None:
    model = GeminiChatModel(api_key="test-key", max_retries=3, retry_backoff_seconds=0)
    with patch.object(
        model._client.models, "generate_content", return_value=_fake_gemini_response("hello")
    ) as mock_generate:
        result = model.complete("system", "user")

    assert result == "hello"
    assert mock_generate.call_count == 1


def test_gemini_complete_handles_empty_text() -> None:
    model = GeminiChatModel(api_key="test-key")
    with patch.object(
        model._client.models, "generate_content", return_value=_fake_gemini_response(None)  # type: ignore[arg-type]
    ):
        assert model.complete("system", "user") == ""


# --- GeminiChatModel: retry behavior --------------------------------------


def test_gemini_retries_server_error_then_succeeds() -> None:
    from google.genai import errors

    model = GeminiChatModel(api_key="test-key", max_retries=3, retry_backoff_seconds=0)
    side_effects = [
        errors.ServerError(503, {"error": {"message": "unavailable", "status": "UNAVAILABLE"}}),
        errors.ClientError(
            429, {"error": {"message": "rate limited", "status": "RESOURCE_EXHAUSTED"}}
        ),
        _fake_gemini_response("succeeded on third try"),
    ]
    with patch.object(
        model._client.models, "generate_content", side_effect=side_effects
    ) as mock_generate:
        result = model.complete("system", "user")

    assert result == "succeeded on third try"
    assert mock_generate.call_count == 3


def test_gemini_raises_llm_provider_error_after_exhausting_retries() -> None:
    from google.genai import errors

    model = GeminiChatModel(api_key="test-key", max_retries=2, retry_backoff_seconds=0)
    with patch.object(
        model._client.models,
        "generate_content",
        side_effect=errors.ServerError(500, {"error": {"message": "down", "status": "INTERNAL"}}),
    ) as mock_generate:
        with pytest.raises(LLMProviderError, match="failed after 2 attempt"):
            model.complete("system", "user")

    assert mock_generate.call_count == 2


def test_gemini_non_retryable_client_error_propagates_immediately() -> None:
    from google.genai import errors

    model = GeminiChatModel(api_key="test-key", max_retries=3, retry_backoff_seconds=0)
    with patch.object(
        model._client.models,
        "generate_content",
        side_effect=errors.ClientError(
            400, {"error": {"message": "bad request", "status": "INVALID_ARGUMENT"}}
        ),
    ) as mock_generate:
        with pytest.raises(errors.ClientError):
            model.complete("system", "user")

    assert mock_generate.call_count == 1  # no retry for a non-transient (non-429) client error


# --- GeminiChatModel: native structured output ---------------------------


def test_gemini_build_config_without_schema_has_no_json_mime_type() -> None:
    model = GeminiChatModel(api_key="test-key")
    config = model._build_config("system prompt")
    assert config.response_mime_type is None
    assert config.response_json_schema is None


def test_gemini_build_config_with_schema_requests_native_json_mode() -> None:
    from pydantic import TypeAdapter

    from app.llm.models import Hypothesis

    model = GeminiChatModel(api_key="test-key")
    config = model._build_config("system prompt", response_schema=list[Hypothesis])

    assert config.response_mime_type == "application/json"
    assert config.response_json_schema == TypeAdapter(list[Hypothesis]).json_schema()


def test_gemini_build_config_schema_has_no_unsupported_additional_properties_field() -> None:
    """Regression test for the exact live-API failure this fix addresses:
    additionalProperties must be present (it's how extra="forbid" is
    expressed) and must survive in response_json_schema, which explicitly
    supports it — unlike response_schema, which does not in Gemini
    Developer API mode."""
    from app.llm.models import Hypothesis

    model = GeminiChatModel(api_key="test-key")
    config = model._build_config("system prompt", response_schema=list[Hypothesis])

    item_schema = config.response_json_schema["$defs"]["Hypothesis"]
    assert item_schema["additionalProperties"] is False
    assert config.response_schema is None  # the old, incompatible field must be unused


def test_gemini_complete_forwards_response_schema_to_generate_content() -> None:
    from pydantic import TypeAdapter

    from app.llm.models import Hypothesis

    model = GeminiChatModel(api_key="test-key")
    with patch.object(
        model._client.models, "generate_content", return_value=_fake_gemini_response("[]")
    ) as mock_generate:
        model.complete("system", "user", response_schema=list[Hypothesis])

    sent_config = mock_generate.call_args.kwargs["config"]
    assert sent_config.response_mime_type == "application/json"
    assert sent_config.response_json_schema == TypeAdapter(list[Hypothesis]).json_schema()


def test_gemini_build_config_disables_thinking_when_schema_given() -> None:
    """Regression test: Gemini's thinking-token budget shares the same
    output-token pool as the actual answer — structured extraction from
    evidence we already gathered doesn't need chain-of-thought, so
    thinking is set to its lowest level for these calls.

    Uses thinking_level, not thinking_budget: thinking_budget is retired
    starting with Gemini 3.5 models and causes a 400 INVALID_ARGUMENT if
    set at all. thinking_level is the documented replacement.
    """
    from google.genai.types import ThinkingLevel

    from app.llm.models import Hypothesis

    model = GeminiChatModel(api_key="test-key")

    config_without_schema = model._build_config("system prompt")
    assert config_without_schema.thinking_config is None

    config_with_schema = model._build_config("system prompt", response_schema=list[Hypothesis])
    assert config_with_schema.thinking_config.thinking_level == ThinkingLevel.MINIMAL
    assert config_with_schema.thinking_config.thinking_budget is None


# --- GeminiChatModel: complete_structured (native .parsed) ----------------


def test_gemini_complete_structured_returns_parsed_data() -> None:
    from app.llm.models import Hypothesis

    model = GeminiChatModel(api_key="test-key")
    fake_response = SimpleNamespace(parsed=[{"a": 1}], text="[{\"a\": 1}]")
    with patch.object(model._client.models, "generate_content", return_value=fake_response):
        result = model.complete_structured("system", "user", response_schema=list[Hypothesis])

    assert result == [{"a": 1}]


def test_gemini_complete_structured_raises_with_diagnostics_when_parsed_is_none() -> None:
    from app.llm.models import Hypothesis

    model = GeminiChatModel(api_key="test-key", max_retries=1)
    fake_candidate = SimpleNamespace(finish_reason="MAX_TOKENS")
    fake_usage = SimpleNamespace(thoughts_token_count=1987)
    fake_response = SimpleNamespace(
        parsed=None, text=None, candidates=[fake_candidate], usage_metadata=fake_usage
    )
    with patch.object(model._client.models, "generate_content", return_value=fake_response):
        with pytest.raises(LLMProviderError, match="MAX_TOKENS") as exc_info:
            model.complete_structured("system", "user", response_schema=list[Hypothesis])

    assert "1987" in str(exc_info.value)


# --- GeminiChatModel: stream_complete --------------------------------------


def test_gemini_stream_complete_yields_chunks() -> None:
    model = GeminiChatModel(api_key="test-key")
    fake_chunks = [SimpleNamespace(text="hel"), SimpleNamespace(text="lo")]

    with patch.object(
        model._client.models, "generate_content_stream", return_value=iter(fake_chunks)
    ):
        chunks = list(model.stream_complete("system", "user"))

    assert chunks == ["hel", "lo"]


def test_gemini_stream_complete_skips_empty_chunks() -> None:
    model = GeminiChatModel(api_key="test-key")
    fake_chunks = [
        SimpleNamespace(text="hel"), SimpleNamespace(text=None), SimpleNamespace(text="lo")
    ]

    with patch.object(
        model._client.models, "generate_content_stream", return_value=iter(fake_chunks)
    ):
        chunks = list(model.stream_complete("system", "user"))

    assert chunks == ["hel", "lo"]
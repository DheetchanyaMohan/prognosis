"""Structured output generation.

Wraps a ChatModel's structured completion with Pydantic validation, so
every LLM-calling node gets back typed, validated objects instead of
parsing raw text itself. No node in app.agent.nodes should ever call
json.loads or model_validate directly on an LLM response — that logic
lives here, once.

This module does not parse JSON text itself: it calls
ChatModel.complete_structured(), which already returns native Python
data (a list/dict of plain values) — parsed by the provider's own native
structured-output mechanism when available (Gemini's response.parsed),
or by the provider's own fallback parsing otherwise (Anthropic). A
second, redundant json.loads() here couldn't recover data that already
failed to parse once; the real fix for that class of failure is at the
provider layer (see app.llm.client.GeminiChatModel), not here.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from app.llm.client import ChatModel


class StructuredOutputError(ValueError):
    """Raised when an LLM response can't be parsed/validated into the
    requested model(s). Subclasses ValueError so existing `except
    ValueError` handling upstream still catches it."""


def generate_structured_list[T: BaseModel](
    chat_model: ChatModel,
    system_prompt: str,
    user_prompt: str,
    item_model: type[T],
) -> list[T]:
    """Calls chat_model.complete_structured, then validates each returned
    item against item_model.

    Raises StructuredOutputError on malformed output rather than
    silently returning an empty list — a node failing loudly on bad
    output is safer than one that looks like it succeeded with nothing.
    """
    # list[item_model] here constructs a runtime value (a generic alias
    # object, passed through to the provider's response_schema) — not a
    # type annotation. mypy's semantic analyzer can't tell the two apart
    # for this syntax shape; this is a documented mypy limitation, not a
    # real type error. See: https://mypy.readthedocs.io/en/stable/common_issues.html#variables-vs-type-aliases
    schema: Any = list[item_model]  # type: ignore[valid-type]

    try:
        raw_items = chat_model.complete_structured(
            system_prompt, user_prompt, response_schema=schema
        )
    except (ValueError, KeyError, TypeError) as exc:
        # Covers json.JSONDecodeError (a ValueError subclass) from
        # providers that fall back to text parsing, and any other
        # provider-side structured-output failure.
        raise StructuredOutputError(f"LLM did not return usable structured output: {exc}") from exc

    if not isinstance(raw_items, list):
        raise StructuredOutputError(
            f"Expected a JSON array of {item_model.__name__}, got {type(raw_items).__name__}"
        )

    try:
        return [item_model.model_validate(item) for item in raw_items]
    except ValidationError as exc:
        raise StructuredOutputError(f"LLM response item failed validation: {exc}") from exc


def generate_structured_object[T: BaseModel](
    chat_model: ChatModel,
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
) -> T:
    """Same as generate_structured_list, but for a single JSON object
    response rather than an array. Not currently used by any node (both
    Hypothesis and Recommendation are produced as lists), included for
    completeness — e.g. a future LLM-based router returning one
    classification object.
    """
    try:
        raw_item = chat_model.complete_structured(
            system_prompt, user_prompt, response_schema=response_model
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise StructuredOutputError(f"LLM did not return usable structured output: {exc}") from exc

    try:
        return response_model.model_validate(raw_item)
    except ValidationError as exc:
        raise StructuredOutputError(f"LLM response failed validation: {exc}") from exc
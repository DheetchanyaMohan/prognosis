"""Structured output generation.

Wraps a ChatModel completion with JSON parsing and Pydantic validation,
so every LLM-calling node gets back typed, validated objects instead of
parsing raw text itself. No node in app.agent.nodes should ever call
json.loads or model_validate directly on an LLM response — that logic
lives here, once.
"""

from __future__ import annotations

import json

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
    """Calls chat_model.complete, parses the response as a JSON array,
    and validates each item against item_model.

    Raises StructuredOutputError on malformed output rather than
    silently returning an empty list — a node failing loudly on bad
    output is safer than one that looks like it succeeded with nothing.
    """
    raw_response = chat_model.complete(system_prompt, user_prompt)

    try:
        raw_items = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise StructuredOutputError(f"LLM response was not valid JSON: {exc}") from exc

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
    raw_response = chat_model.complete(system_prompt, user_prompt)

    try:
        raw_item = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise StructuredOutputError(f"LLM response was not valid JSON: {exc}") from exc

    try:
        return response_model.model_validate(raw_item)
    except ValidationError as exc:
        raise StructuredOutputError(f"LLM response failed validation: {exc}") from exc
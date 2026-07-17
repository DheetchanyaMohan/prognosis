from __future__ import annotations

import json

import pytest
from pydantic import BaseModel

from app.llm.structured_output import (
    StructuredOutputError,
    generate_structured_list,
    generate_structured_object,
)


class _Item(BaseModel):
    name: str
    value: int


class FakeChatModel:
    def __init__(self, response: str) -> None:
        self._response = response

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        return self._response

    def stream_complete(self, system_prompt: str, user_prompt: str):
        yield self._response


# --- generate_structured_list -------------------------------------------


def test_parses_valid_json_array() -> None:
    response = json.dumps([{"name": "a", "value": 1}, {"name": "b", "value": 2}])
    items = generate_structured_list(FakeChatModel(response), "sys", "user", _Item)

    assert items == [_Item(name="a", value=1), _Item(name="b", value=2)]


def test_empty_array_returns_empty_list() -> None:
    items = generate_structured_list(FakeChatModel("[]"), "sys", "user", _Item)
    assert items == []


def test_malformed_json_raises_structured_output_error() -> None:
    with pytest.raises(StructuredOutputError, match="not valid JSON"):
        generate_structured_list(FakeChatModel("not json"), "sys", "user", _Item)


def test_non_array_raises_structured_output_error() -> None:
    response = json.dumps({"name": "a", "value": 1})
    with pytest.raises(StructuredOutputError, match="JSON array"):
        generate_structured_list(FakeChatModel(response), "sys", "user", _Item)


def test_invalid_item_raises_structured_output_error() -> None:
    response = json.dumps([{"name": "a"}])  # missing required "value"
    with pytest.raises(StructuredOutputError, match="failed validation"):
        generate_structured_list(FakeChatModel(response), "sys", "user", _Item)


def test_structured_output_error_is_a_value_error() -> None:
    """Downstream `except ValueError` handling must still catch this."""
    assert issubclass(StructuredOutputError, ValueError)


# --- generate_structured_object ---------------------------------------


def test_parses_valid_json_object() -> None:
    response = json.dumps({"name": "a", "value": 1})
    item = generate_structured_object(FakeChatModel(response), "sys", "user", _Item)
    assert item == _Item(name="a", value=1)


def test_object_malformed_json_raises() -> None:
    with pytest.raises(StructuredOutputError, match="not valid JSON"):
        generate_structured_object(FakeChatModel("not json"), "sys", "user", _Item)


def test_object_invalid_item_raises() -> None:
    response = json.dumps({"name": "a"})  # missing "value"
    with pytest.raises(StructuredOutputError):
        generate_structured_object(FakeChatModel(response), "sys", "user", _Item)
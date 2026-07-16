"""Tests for the parts of app.agent.state actually owned by app.agent:
TraceEntry. Hypothesis/Recommendation validation now lives in
tests/test_llm_models.py, next to their real owner, app.llm.models.
"""

import pytest
from pydantic import ValidationError

from app.agent.state import TraceEntry


def test_trace_entry_defaults() -> None:
    entry = TraceEntry(
        node="router", reasoning="picked the target run", evidence_summary="run_005 selected"
    )
    assert entry.tools_called == []
    assert entry.timestamp is not None


def test_trace_entry_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        TraceEntry(
            node="router", reasoning="x", evidence_summary="x", unexpected_field="not allowed"
        )
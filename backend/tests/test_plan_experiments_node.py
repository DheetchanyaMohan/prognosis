from __future__ import annotations

import json

import pytest

from app.agent.nodes.plan_experiments import _build_evidence_sections, plan_experiments_node
from app.agent.state import AgentState
from app.llm import Hypothesis, StructuredOutputError


class FakeChatModel:
    def __init__(self, response: str) -> None:
        self._response = response
        self.last_user_prompt: str | None = None

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        self.last_user_prompt = user_prompt
        return self._response

    def stream_complete(self, system_prompt: str, user_prompt: str):
        yield self._response


_VALID_RESPONSE = json.dumps(
    [
        {
            "title": "Add dropout",
            "rationale": "Generalization gap is widening with dropout=0.0.",
            "supporting_evidence": ["loss_gap=0.5", "dropout=0.0"],
            "expected_benefit": "Reduced overfitting",
            "estimated_effort": "low",
            "confidence": 0.85,
            "provenance": ["diagnostics:generalization_gap", "knowledge:regularization"],
        },
        {
            "title": "Increase dataset size",
            "rationale": "train_size is small relative to model capacity.",
            "supporting_evidence": ["train_size=1500"],
            "expected_benefit": "Better generalization",
            "estimated_effort": "medium",
            "confidence": 0.5,
            "provenance": ["diagnostics:generalization_gap"],
        },
    ]
)

_HYPOTHESIS = Hypothesis(
    title="Overfitting", explanation="Gap widening", supporting_evidence=["x"], confidence=0.8
)


def test_no_hypotheses_skips_llm_call_entirely() -> None:
    client = FakeChatModel("should never be called")
    result = plan_experiments_node({"user_query": "what is dropout?"}, chat_model=client)

    assert result["recommendations"] == []
    assert client.last_user_prompt is None
    assert "no specific run analyzed" in result["trace"][0].reasoning


def test_produces_ranked_recommendations() -> None:
    client = FakeChatModel(_VALID_RESPONSE)
    state: AgentState = {"user_query": "why is my model overfitting?", "hypotheses": [_HYPOTHESIS]}

    result = plan_experiments_node(state, chat_model=client)

    recs = result["recommendations"]
    assert len(recs) == 2
    assert recs[0].confidence >= recs[1].confidence
    assert recs[0].title == "Add dropout"


def test_trace_entry_reflects_llm_call() -> None:
    client = FakeChatModel(_VALID_RESPONSE)
    state: AgentState = {"user_query": "x", "hypotheses": [_HYPOTHESIS]}

    result = plan_experiments_node(state, chat_model=client)

    assert result["trace"][0].node == "plan_experiments"
    assert result["trace"][0].tools_called == ["llm.generate_structured_list"]


def test_malformed_json_raises() -> None:
    client = FakeChatModel("not json")
    state: AgentState = {"user_query": "x", "hypotheses": [_HYPOTHESIS]}
    with pytest.raises(StructuredOutputError, match="not valid JSON"):
        plan_experiments_node(state, chat_model=client)


def test_recommendation_missing_field_raises() -> None:
    bad = json.dumps([{"title": "X", "rationale": "Y"}])
    client = FakeChatModel(bad)
    state: AgentState = {"user_query": "x", "hypotheses": [_HYPOTHESIS]}
    with pytest.raises(StructuredOutputError):
        plan_experiments_node(state, chat_model=client)


def test_invalid_effort_level_raises() -> None:
    bad = json.dumps(
        [
            {
                "title": "X", "rationale": "Y", "supporting_evidence": ["a"],
                "expected_benefit": "b", "estimated_effort": "extreme",
                "confidence": 0.5, "provenance": ["p"],
            }
        ]
    )
    client = FakeChatModel(bad)
    state: AgentState = {"user_query": "x", "hypotheses": [_HYPOTHESIS]}
    with pytest.raises(StructuredOutputError):
        plan_experiments_node(state, chat_model=client)


def test_sections_include_hypotheses() -> None:
    state: AgentState = {"user_query": "why?", "hypotheses": [_HYPOTHESIS]}
    sections = _build_evidence_sections(state)
    headings = [h for h, _ in sections]

    assert "Ranked hypotheses" in headings
    assert any("Overfitting" in content for _, content in sections)
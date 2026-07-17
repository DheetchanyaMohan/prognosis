from __future__ import annotations

from app.agent.nodes.finalize import finalize_node
from app.agent.state import AgentState
from app.llm import Hypothesis, Recommendation


def _hypothesis() -> Hypothesis:
    return Hypothesis(
        title="Overfitting", explanation="x", supporting_evidence=["x"], confidence=0.8
    )


def _recommendation() -> Recommendation:
    return Recommendation(
        title="Add dropout", rationale="x", supporting_evidence=["e"],
        expected_benefit="b", estimated_effort="low", confidence=0.8,
        provenance=["diagnostics:generalization_gap"],
    )


def test_finalize_appends_exactly_one_trace_entry() -> None:
    result = finalize_node({"request_type": "diagnose_run", "selected_run": "run_005"})
    assert len(result["trace"]) == 1
    assert result["trace"][0].node == "finalize"


def test_finalize_introduces_no_new_state_keys() -> None:
    result = finalize_node({"request_type": "general_question"})
    assert set(result.keys()) == {"trace"}


def test_finalize_summary_mentions_recommendations_when_present() -> None:
    state: AgentState = {
        "request_type": "diagnose_run", "selected_run": "run_005",
        "hypotheses": [_hypothesis()], "recommendations": [_recommendation()],
    }
    result = finalize_node(state)
    reasoning = result["trace"][0].reasoning
    assert "1 recommendation(s)" in reasoning
    assert "run_005" in reasoning


def test_finalize_summary_notes_hypotheses_without_recommendations() -> None:
    state: AgentState = {
        "request_type": "diagnose_run", "selected_run": "run_005", "hypotheses": [_hypothesis()],
    }
    result = finalize_node(state)
    assert "no recommendations" in result["trace"][0].reasoning


def test_finalize_summary_for_general_question() -> None:
    result = finalize_node({"request_type": "general_question"})
    reasoning = result["trace"][0].reasoning
    assert "general_question" in reasoning
    assert "no run-specific analysis" in reasoning
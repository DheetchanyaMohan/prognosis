from __future__ import annotations

from app.agent.graph import MAX_RETRIES
from app.agent.nodes.self_check import self_check_node
from app.agent.state import AgentState
from app.llm import Hypothesis, Recommendation
from app.rag.schemas import ChunkMetadata, DocumentSource, RetrievedChunk


def _hypothesis() -> Hypothesis:
    return Hypothesis(
        title="Overfitting", explanation="x", supporting_evidence=["x"], confidence=0.8
    )


def _grounded_recommendation() -> Recommendation:
    return Recommendation(
        title="Add dropout", rationale="x", supporting_evidence=["loss_gap=0.5"],
        expected_benefit="less overfitting", estimated_effort="low", confidence=0.8,
        provenance=["knowledge:regularization"],
    )


def _ungrounded_recommendation() -> Recommendation:
    return Recommendation(
        title="Try a bigger model", rationale="x", supporting_evidence=["vibes"],
        expected_benefit="maybe better", estimated_effort="high", confidence=0.3,
        provenance=["totally_made_up_source"],
    )


def _knowledge_chunk(source: str = "regularization") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"{source}::chunk_0", text="text", score=0.7,
        metadata=ChunkMetadata(
            source=source, source_type=DocumentSource.KNOWLEDGE_BASE, chunk_index=0
        ),
    )


# --- no hypotheses/recommendations (general question) -----------------


def test_general_question_needs_no_more_evidence() -> None:
    result = self_check_node({"hypotheses": [], "recommendations": []})
    assert result["needs_more_evidence"] is False
    assert result["retry_count"] == 0


# --- grounded recommendations -------------------------------------------


def test_grounded_recommendation_via_diagnostics_token_passes() -> None:
    state: AgentState = {
        "hypotheses": [_hypothesis()],
        "recommendations": [_grounded_recommendation()],
        "retrieved_knowledge": [_knowledge_chunk()],
        "retry_count": 0,
    }
    result = self_check_node(state)

    assert result["needs_more_evidence"] is False
    assert "grounded" in result["trace"][0].reasoning


# --- ungrounded recommendations trigger retry (once) -----------------------


def test_ungrounded_recommendation_requests_retry_when_under_cap() -> None:
    state: AgentState = {
        "hypotheses": [_hypothesis()],
        "recommendations": [_ungrounded_recommendation()],
        "retrieved_knowledge": [_knowledge_chunk()],
        "retry_count": 0,
    }
    result = self_check_node(state)

    assert result["needs_more_evidence"] is True
    assert result["retry_count"] == 1


def test_ungrounded_recommendation_stops_retrying_once_cap_reached() -> None:
    state: AgentState = {
        "hypotheses": [_hypothesis()],
        "recommendations": [_ungrounded_recommendation()],
        "retrieved_knowledge": [_knowledge_chunk()],
        "retry_count": MAX_RETRIES,
    }
    result = self_check_node(state)

    assert result["needs_more_evidence"] is False  # cap reached, must proceed to finalize
    assert result["retry_count"] == MAX_RETRIES  # unchanged, no further increment
    assert "reached" in result["trace"][0].reasoning


# --- grounding via known evidence tokens --------------------------------


def test_provenance_matching_retrieved_knowledge_source_is_grounded() -> None:
    rec = Recommendation(
        title="Add dropout", rationale="x", supporting_evidence=["e"],
        expected_benefit="b", estimated_effort="low", confidence=0.8,
        provenance=["knowledge:regularization"],
    )
    state: AgentState = {
        "hypotheses": [_hypothesis()],
        "recommendations": [rec],
        "retrieved_knowledge": [_knowledge_chunk("regularization")],
        "retry_count": 0,
    }
    result = self_check_node(state)
    assert result["needs_more_evidence"] is False


def test_provenance_referencing_selected_run_is_grounded() -> None:
    rec = Recommendation(
        title="Compare configs", rationale="x", supporting_evidence=["e"],
        expected_benefit="b", estimated_effort="low", confidence=0.8,
        provenance=["run:run_005"],
    )
    state: AgentState = {
        "hypotheses": [_hypothesis()],
        "recommendations": [rec],
        "selected_run": "run_005",
        "retry_count": 0,
    }
    result = self_check_node(state)
    assert result["needs_more_evidence"] is False


def test_empty_provenance_is_never_grounded() -> None:
    rec = Recommendation(
        title="X", rationale="x", supporting_evidence=["e"],
        expected_benefit="b", estimated_effort="low", confidence=0.8,
        provenance=[],
    )
    state: AgentState = {
        "hypotheses": [_hypothesis()], "recommendations": [rec],
        "retrieved_knowledge": [_knowledge_chunk()], "retry_count": 0,
    }
    result = self_check_node(state)
    assert result["needs_more_evidence"] is True


# --- zero recommendations despite hypotheses is itself weak evidence -------


def test_zero_recommendations_with_hypotheses_is_weak() -> None:
    state: AgentState = {"hypotheses": [_hypothesis()], "recommendations": [], "retry_count": 0}
    result = self_check_node(state)
    assert result["needs_more_evidence"] is True
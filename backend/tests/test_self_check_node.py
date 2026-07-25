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
    assert result["recommendations"][0].is_grounded is True


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
    assert result["recommendations"][0].is_grounded is False


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


# --- is_grounded population (structural, not just trace prose) -------------


def test_mixed_recommendations_each_get_their_own_grounding_flag() -> None:
    """A grounded and an ungrounded recommendation in the same call must
    each receive their own correct is_grounded value — not an all-or-
    nothing verdict for the whole list."""
    grounded = _grounded_recommendation()
    ungrounded = _ungrounded_recommendation()
    state: AgentState = {
        "hypotheses": [_hypothesis()],
        "recommendations": [grounded, ungrounded],
        "retrieved_knowledge": [_knowledge_chunk()],
        "retry_count": MAX_RETRIES,  # avoid the retry path so both survive to compare
    }
    result = self_check_node(state)

    returned = {r.title: r.is_grounded for r in result["recommendations"]}
    assert returned["Add dropout"] is True
    assert returned["Try a bigger model"] is False


def test_original_recommendation_objects_are_not_mutated() -> None:
    """model_copy() must produce new objects — the Recommendation
    instances passed in should be left exactly as they were."""
    original = _grounded_recommendation()
    assert original.is_grounded is False  # the default, pre-self_check

    state: AgentState = {
        "hypotheses": [_hypothesis()],
        "recommendations": [original],
        "retrieved_knowledge": [_knowledge_chunk()],
        "retry_count": 0,
    }
    self_check_node(state)

    assert original.is_grounded is False  # untouched by self_check_node


def test_recommendation_defaults_to_not_grounded_before_self_check_runs() -> None:
    """Recommendation.is_grounded defaults to False — plan_experiments
    (which constructs these before self_check ever runs) has no basis
    to claim grounding itself."""
    rec = _grounded_recommendation()
    assert rec.is_grounded is False
import pytest
from pydantic import ValidationError

from app.llm.models import Hypothesis, Recommendation


def test_hypothesis_confidence_must_be_in_unit_range() -> None:
    with pytest.raises(ValidationError):
        Hypothesis(title="Overfitting", explanation="x", supporting_evidence=[], confidence=1.5)


def test_hypothesis_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        Hypothesis(
            title="X", explanation="x", supporting_evidence=[], confidence=0.5,
            unexpected="not allowed",  # type: ignore[call-arg]
        )


def test_hypothesis_valid_construction() -> None:
    h = Hypothesis(
        title="Overfitting", explanation="Gap is widening",
        supporting_evidence=["generalization_gap trend=widening"], confidence=0.8,
    )
    assert h.confidence == 0.8


def test_recommendation_requires_valid_effort_level() -> None:
    with pytest.raises(ValidationError):
        Recommendation(
            title="Add dropout", rationale="x", supporting_evidence=[],
            expected_benefit="reduced gap", estimated_effort="extreme",  # type: ignore[arg-type]
            confidence=0.5, provenance=["diagnostics:generalization_gap"],
        )


def test_recommendation_valid_construction() -> None:
    rec = Recommendation(
        title="Add dropout", rationale="Generalization gap is widening with no regularization",
        supporting_evidence=["loss_gap=0.5", "dropout=0.0"],
        expected_benefit="Reduced overfitting, smaller train/val gap",
        estimated_effort="low", confidence=0.75,
        provenance=["diagnostics:generalization_gap", "knowledge:regularization"],
    )
    assert rec.estimated_effort == "low"
    assert len(rec.provenance) == 2
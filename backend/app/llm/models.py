"""Structured response models returned by the LLM.

Every shape an LLM call in this project can return lives here — nothing
else. app.agent.state imports Hypothesis/Recommendation from this module
rather than redefining them, so there is exactly one place that owns
"what the LLM is allowed to return." TraceEntry stays in app.agent.state
deliberately: it's constructed by nodes as bookkeeping, never returned by
an LLM, so it isn't a structured *LLM response* model.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

#: plan_experiments' estimated_effort — coarse on purpose. The LLM isn't
#: estimating engineer-hours, just signaling relative cost to try something.
EffortLevel = Literal["low", "medium", "high"]


class Hypothesis(BaseModel):
    """One candidate explanation for observed training behavior,
    synthesized from diagnostics + retrieved evidence — never asserted
    without evidence backing it."""

    model_config = ConfigDict(extra="forbid")

    title: str
    explanation: str
    supporting_evidence: list[str] = Field(
        description=(
            "Short evidence references backing this hypothesis, e.g. "
            "'generalization_gap trend=widening', 'knowledge:overfitting', 'run:run_003'"
        )
    )
    confidence: float = Field(ge=0.0, le=1.0)


class Recommendation(BaseModel):
    """One structured, evidence-linked next-experiment recommendation —
    the final actionable output of the diagnosis workflow."""

    model_config = ConfigDict(extra="forbid")

    title: str
    rationale: str
    supporting_evidence: list[str]
    expected_benefit: str
    estimated_effort: EffortLevel
    confidence: float = Field(ge=0.0, le=1.0)
    provenance: list[str] = Field(
        description=(
            "Traceable evidence sources for this recommendation, e.g. "
            "'diagnostics:generalization_gap', 'knowledge:regularization', 'run:run_003'"
        )
    )
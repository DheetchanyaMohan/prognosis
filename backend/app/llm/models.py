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


# supporting_evidence is capped at 3 items (max_length=3) deliberately: this
# becomes a real `maxItems` constraint in the JSON schema Gemini enforces
# natively, not just prompt wording. Gemini 2.5's thinking-token budget
# shares the same output-token pool as the answer itself, and a verbose
# schema plus an unbounded evidence list previously produced truncated
# (finish_reason=MAX_TOKENS) responses in practice — see
# HYPOTHESIS_GENERATION_SYSTEM_PROMPT for the matching prompt-level guidance
# (exactly 2 hypotheses, 2-3 sentence explanations). This rationale lives in
# a comment, not the docstring below, because Pydantic includes the class
# docstring verbatim in the generated JSON schema's "description" field —
# sent to Gemini on every call — so a long docstring here would itself
# contribute to the exact token-budget problem being solved.
class Hypothesis(BaseModel):
    """One candidate explanation for observed training behavior,
    synthesized from diagnostics + retrieved evidence — never asserted
    without evidence backing it."""

    model_config = ConfigDict(extra="forbid")

    title: str
    explanation: str
    supporting_evidence: list[str] = Field(
        max_length=3,
        description=(
            "At most 3 short evidence references backing this hypothesis, e.g. "
            "'generalization_gap trend=widening', 'knowledge:overfitting', 'run:run_003'"
        ),
    )
    confidence: float = Field(ge=0.0, le=1.0)


class Recommendation(BaseModel):
    """One structured, evidence-linked next-experiment recommendation —
    the final actionable output of the diagnosis workflow.

    is_grounded defaults to False here because it is not something the
    LLM determines — plan_experiments produces a Recommendation without
    a meaningful value for it. self_check_node is the sole writer: it
    already computes, per recommendation, whether its provenance
    references real evidence (that's the node's entire purpose), and
    overwrites this field with that exact result via model_copy(). No
    node other than self_check should ever set this field.
    """

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
    is_grounded: bool = Field(
        default=False,
        description=(
            "Whether self_check verified this recommendation's provenance actually "
            "references real evidence gathered during the run — not asserted by the LLM."
        ),
    )
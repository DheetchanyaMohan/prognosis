"""Self Check node.

Sixth node in the diagnosis graph. Verifies that every recommendation
produced by plan_experiments is actually grounded in evidence gathered
earlier in the run — not asserted by the LLM without backing. This is
deliberately deterministic (no LLM call): it only inspects state that
already exists, checking supporting_evidence/provenance are non-empty
and reference something real, and decides whether to request one more
retrieval pass. It never calls a tool and never talks to an LLM itself.

The retry cap lives here, not in app.agent.graph's routing function —
self_check is the one node with both the current retry_count and the
decision of whether evidence is weak in scope at the same time; see
app.agent.graph._route_after_self_check for why routing only trusts the
`needs_more_evidence` flag this node produces.
"""

from __future__ import annotations

from typing import Any

from app.agent.graph import MAX_RETRIES
from app.agent.state import AgentState, TraceEntry
from app.llm import Recommendation


def _known_evidence_tokens(state: AgentState) -> set[str]:
    """Collects every identifier a recommendation's provenance could
    legitimately reference: evidence categories, retrieved-doc sources,
    similar-run sources/run_ids, and the run(s) actually in scope."""
    tokens: set[str] = set()

    if state.get("diagnostics") is not None:
        tokens.add("diagnostics")
    if state.get("comparison") is not None:
        tokens.add("comparison")

    for chunk in state.get("retrieved_knowledge", []):
        tokens.add(chunk.metadata.source)
        tokens.add("knowledge")

    for chunk in state.get("similar_runs", []):
        tokens.add(chunk.metadata.source)
        if chunk.metadata.run_id:
            tokens.add(chunk.metadata.run_id)
        tokens.add("run")

    selected_run = state.get("selected_run")
    if selected_run:
        tokens.add(selected_run)
    comparison_run = state.get("comparison_run")
    if comparison_run:
        tokens.add(comparison_run)

    return tokens


def _is_grounded(recommendation: Recommendation, known_tokens: set[str]) -> bool:
    """A recommendation is grounded if it has both non-empty
    supporting_evidence and provenance, and at least one provenance entry
    references a known evidence token. Matching is substring-based (case
    insensitive) since the LLM writes free-form strings like
    'diagnostics:generalization_gap', not exact tokens.
    """
    if not recommendation.supporting_evidence or not recommendation.provenance:
        return False
    return any(
        token.lower() in entry.lower()
        for entry in recommendation.provenance
        for token in known_tokens
    )


def self_check_node(state: AgentState) -> dict[str, Any]:
    recommendations = state.get("recommendations", [])
    hypotheses = state.get("hypotheses", [])
    retry_count = state.get("retry_count", 0)

    # A general knowledge question legitimately produces neither
    # hypotheses nor recommendations — nothing to verify, not a failure.
    if not hypotheses and not recommendations:
        trace_entry = TraceEntry(
            node="self_check",
            tools_called=[],
            reasoning=(
                "No hypotheses or recommendations were produced (general knowledge "
                "question); nothing to verify."
            ),
            evidence_summary="0 recommendation(s) checked",
        )
        return {"needs_more_evidence": False, "retry_count": retry_count, "trace": [trace_entry]}

    known_tokens = _known_evidence_tokens(state)
    ungrounded = [r.title for r in recommendations if not _is_grounded(r, known_tokens)]
    evidence_is_weak = bool(ungrounded) or not recommendations

    can_retry = retry_count < MAX_RETRIES
    needs_more_evidence = evidence_is_weak and can_retry

    if needs_more_evidence:
        reasoning = (
            f"{len(ungrounded)} of {len(recommendations)} recommendation(s) lack grounded "
            f"evidence ({ungrounded}); requesting an additional retrieval pass "
            f"(retry {retry_count + 1} of {MAX_RETRIES})."
        )
    elif evidence_is_weak:
        reasoning = (
            f"{len(ungrounded)} of {len(recommendations)} recommendation(s) still lack "
            f"grounded evidence after the retry cap ({MAX_RETRIES}) was reached; "
            "proceeding to finalize rather than looping indefinitely."
        )
    else:
        reasoning = f"All {len(recommendations)} recommendation(s) are grounded in cited evidence."

    trace_entry = TraceEntry(
        node="self_check",
        tools_called=[],
        reasoning=reasoning,
        evidence_summary=(
            f"{len(recommendations) - len(ungrounded)}/{len(recommendations)} "
            "recommendation(s) grounded"
        ),
    )

    return {
        "needs_more_evidence": needs_more_evidence,
        "retry_count": retry_count + 1 if needs_more_evidence else retry_count,
        "trace": [trace_entry],
    }
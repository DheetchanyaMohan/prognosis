"""Plan Experiments node.

Fifth node in the diagnosis graph. Turns the ranked hypotheses
(generate_hypotheses) into concrete, evidence-linked next-experiment
recommendations via a single LLM call. No new evidence is fetched here,
and no tool is called other than the LLM client itself.

Reuses AnthropicLLMClient/LLMClient from generate_hypotheses rather than
redefining an Anthropic wrapper — there is exactly one LLM client
implementation in this codebase, used by both LLM-calling nodes.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.agent.nodes.generate_hypotheses import AnthropicLLMClient, LLMClient
from app.agent.state import AgentState, Recommendation, TraceEntry


@lru_cache
def _default_llm_client() -> LLMClient:
    return AnthropicLLMClient()


_SYSTEM_PROMPT = """You are an experienced ML engineer proposing next experiments.

You will be given ranked hypotheses about what is happening in a training run, \
deterministic diagnostics, and retrieved documentation. Using ONLY this \
evidence, produce a prioritized list of 2 to 4 concrete next-experiment \
recommendations. Every recommendation's provenance list must cite the \
specific evidence (a hypothesis, a diagnostic fact, a retrieved document, or \
a historical run) that justifies it — never recommend something you cannot \
tie back to something you were given.

Respond with ONLY a JSON array, no other text, matching this shape:
[{"title": str, "rationale": str, "supporting_evidence": [str, ...], \
"expected_benefit": str, "estimated_effort": "low" | "medium" | "high", \
"confidence": float between 0.0 and 1.0, "provenance": [str, ...]}]
"""


def _build_user_prompt(state: AgentState) -> str:
    parts = [f"User question: {state.get('user_query', '')}"]

    hypotheses = state.get("hypotheses", [])
    if hypotheses:
        hypotheses_text = "\n".join(h.model_dump_json() for h in hypotheses)
        parts.append(f"Ranked hypotheses:\n{hypotheses_text}")

    diagnostics = state.get("diagnostics")
    if diagnostics is not None:
        parts.append("Deterministic diagnostics:\n" + diagnostics.model_dump_json(indent=2))

    comparison = state.get("comparison")
    if comparison is not None:
        parts.append("Run comparison:\n" + comparison.model_dump_json(indent=2))

    knowledge = state.get("retrieved_knowledge", [])
    if knowledge:
        knowledge_text = "\n\n".join(f"[{c.metadata.source}] {c.text}" for c in knowledge)
        parts.append(f"Retrieved documentation:\n{knowledge_text}")

    similar_runs = state.get("similar_runs", [])
    if similar_runs:
        similar_text = "\n\n".join(f"[{c.metadata.source}] {c.text}" for c in similar_runs)
        parts.append(f"Similar historical runs:\n{similar_text}")

    return "\n\n".join(parts)


def _parse_recommendations(raw_response: str) -> list[Recommendation]:
    """Parses the LLM's JSON array response into validated Recommendation
    models. Raises ValueError on malformed output rather than silently
    returning an empty list."""
    try:
        raw_items = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM response was not valid JSON: {exc}") from exc

    if not isinstance(raw_items, list):
        raise ValueError(
            f"Expected a JSON array of recommendations, got {type(raw_items).__name__}"
        )

    return [Recommendation.model_validate(item) for item in raw_items]


def plan_experiments_node(
    state: AgentState, llm_client: LLMClient | None = None
) -> dict[str, Any]:
    hypotheses = state.get("hypotheses", [])
    if not hypotheses:
        trace_entry = TraceEntry(
            node="plan_experiments",
            tools_called=[],
            reasoning=(
                "No hypotheses were generated (likely a general knowledge question "
                "with no specific run analyzed), so there is nothing to plan "
                "experiments against."
            ),
            evidence_summary="0 recommendation(s) produced",
        )
        return {"recommendations": [], "trace": [trace_entry]}

    llm_client = llm_client or _default_llm_client()

    user_prompt = _build_user_prompt(state)
    raw_response = llm_client.complete(_SYSTEM_PROMPT, user_prompt)
    recommendations = _parse_recommendations(raw_response)

    # Rank by confidence, descending, so downstream nodes and the
    # frontend can assume recommendations[0] is the top priority.
    recommendations.sort(key=lambda r: r.confidence, reverse=True)

    reasoning = (
        f"Planned {len(recommendations)} recommendation(s) from {len(hypotheses)} "
        f"ranked hypothesis(es)."
    )
    if recommendations:
        reasoning += (
            f" Top recommendation: {recommendations[0].title!r} "
            f"(effort={recommendations[0].estimated_effort}, "
            f"confidence={recommendations[0].confidence:.2f})."
        )

    trace_entry = TraceEntry(
        node="plan_experiments",
        tools_called=["llm_client.complete"],
        reasoning=reasoning,
        evidence_summary=f"{len(recommendations)} recommendation(s) produced",
    )

    return {"recommendations": recommendations, "trace": [trace_entry]}
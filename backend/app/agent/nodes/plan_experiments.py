"""Plan Experiments node.

Fifth node in the diagnosis graph. Turns the ranked hypotheses
(generate_hypotheses) into concrete, evidence-linked next-experiment
recommendations via a single LLM call.

All LLM interaction is delegated to app.llm: this node builds the
evidence sections from state, then calls
app.llm.generate_structured_list. It never imports a provider SDK, never
inlines a prompt string, and never parses raw LLM output itself.
"""

from __future__ import annotations

from typing import Any

from app.agent.state import AgentState, TraceEntry
from app.llm import (
    EXPERIMENT_PLANNING_SYSTEM_PROMPT,
    ChatModel,
    Recommendation,
    build_user_prompt,
    generate_structured_list,
    get_chat_model,
)


def _build_evidence_sections(state: AgentState) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []

    hypotheses = state.get("hypotheses", [])
    if hypotheses:
        hypotheses_text = "\n".join(h.model_dump_json() for h in hypotheses)
        sections.append(("Ranked hypotheses", hypotheses_text))

    diagnostics = state.get("diagnostics")
    if diagnostics is not None:
        sections.append(("Deterministic diagnostics", diagnostics.model_dump_json(indent=2)))

    comparison = state.get("comparison")
    if comparison is not None:
        sections.append(("Run comparison", comparison.model_dump_json(indent=2)))

    knowledge = state.get("retrieved_knowledge", [])
    if knowledge:
        knowledge_text = "\n\n".join(f"[{c.metadata.source}] {c.text}" for c in knowledge)
        sections.append(("Retrieved documentation", knowledge_text))

    similar_runs = state.get("similar_runs", [])
    if similar_runs:
        similar_text = "\n\n".join(f"[{c.metadata.source}] {c.text}" for c in similar_runs)
        sections.append(("Similar historical runs", similar_text))

    return sections


def plan_experiments_node(
    state: AgentState, chat_model: ChatModel | None = None
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

    chat_model = chat_model or get_chat_model()

    user_prompt = build_user_prompt(state.get("user_query", ""), _build_evidence_sections(state))
    recommendations = generate_structured_list(
        chat_model, EXPERIMENT_PLANNING_SYSTEM_PROMPT, user_prompt, Recommendation
    )

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
        tools_called=["llm.generate_structured_list"],
        reasoning=reasoning,
        evidence_summary=f"{len(recommendations)} recommendation(s) produced",
    )

    return {"recommendations": recommendations, "trace": [trace_entry]}
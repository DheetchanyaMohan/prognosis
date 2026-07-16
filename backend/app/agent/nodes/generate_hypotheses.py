"""Generate Hypotheses node.

Fourth node in the diagnosis graph, and the first one that reasons rather
than just gathering evidence. Synthesizes ranked hypotheses for what's
happening in the selected run(s) by combining deterministic diagnostics
(analyze_metrics), retrieved documentation, and historical run evidence
(retrieve_context) via a single LLM call.

All LLM interaction is delegated to app.llm: this node builds the
evidence sections from state, then calls
app.llm.generate_structured_list. It never imports a provider SDK, never
inlines a prompt string, and never parses raw LLM output itself.
"""

from __future__ import annotations

from typing import Any

from app.agent.state import AgentState, TraceEntry
from app.llm import (
    HYPOTHESIS_GENERATION_SYSTEM_PROMPT,
    ChatModel,
    Hypothesis,
    build_user_prompt,
    generate_structured_list,
    get_chat_model,
)


def _build_evidence_sections(state: AgentState) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []

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


def generate_hypotheses_node(
    state: AgentState, chat_model: ChatModel | None = None
) -> dict[str, Any]:
    chat_model = chat_model or get_chat_model()

    user_prompt = build_user_prompt(state.get("user_query", ""), _build_evidence_sections(state))
    hypotheses = generate_structured_list(
        chat_model, HYPOTHESIS_GENERATION_SYSTEM_PROMPT, user_prompt, Hypothesis
    )

    # Rank by confidence, descending, so downstream nodes and the
    # frontend can assume hypotheses[0] is the leading theory.
    hypotheses.sort(key=lambda h: h.confidence, reverse=True)

    reasoning = (
        f"Synthesized {len(hypotheses)} hypothesis(es) from diagnostics, "
        f"{len(state.get('retrieved_knowledge', []))} knowledge chunk(s), and "
        f"{len(state.get('similar_runs', []))} similar-run chunk(s)."
    )
    if hypotheses:
        reasoning += (
            f" Leading hypothesis: {hypotheses[0].title!r} "
            f"(confidence={hypotheses[0].confidence:.2f})."
        )

    trace_entry = TraceEntry(
        node="generate_hypotheses",
        tools_called=["llm.generate_structured_list"],
        reasoning=reasoning,
        evidence_summary=f"{len(hypotheses)} ranked hypothesis(es) produced",
    )

    return {"hypotheses": hypotheses, "trace": [trace_entry]}
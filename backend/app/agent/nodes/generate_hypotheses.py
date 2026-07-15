"""Generate Hypotheses node.

Fourth node in the diagnosis graph, and the first one that reasons rather
than just gathering evidence. Synthesizes ranked hypotheses for what's
happening in the selected run(s) by combining deterministic diagnostics
(analyze_metrics), retrieved documentation, and historical run evidence
(retrieve_context) via a single LLM call. No new evidence is fetched
here, and no tool is called other than the LLM client itself.

The LLM is given the evidence already gathered and instructed to cite it
directly — it does not have access to any tool, so it cannot invent
evidence that isn't already in the prompt.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Protocol

from app.agent.state import AgentState, Hypothesis, TraceEntry


class LLMClient(Protocol):
    """The interface this node depends on. AnthropicLLMClient implements
    this against the real Anthropic API; tests substitute a fake with
    the same shape, with no network access or API key needed."""

    def complete(self, system_prompt: str, user_prompt: str) -> str: ...


class AnthropicLLMClient:
    """Thin wrapper around the Anthropic API.

    Constructed lazily (only when generate_hypotheses_node is called with
    no injected llm_client) so importing this module never requires
    ANTHROPIC_API_KEY to be set — only actually running the node for
    real does.
    """

    def __init__(self) -> None:
        import anthropic

        from app.core.config import get_settings

        settings = get_settings()
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")


@lru_cache
def _default_llm_client() -> LLMClient:
    return AnthropicLLMClient()


_SYSTEM_PROMPT = """You are an experienced ML engineer diagnosing a training run.

You will be given deterministic diagnostic facts, retrieved documentation, \
and evidence from similar historical runs. Using ONLY this evidence, propose \
2 to 4 ranked hypotheses for what is happening. Every hypothesis's \
supporting_evidence list must cite specific facts you were given — never \
invent evidence, and never state a hypothesis you cannot tie back to \
something in the provided context. If the evidence is too thin to support \
any hypothesis with reasonable confidence, say so by returning fewer, \
lower-confidence hypotheses rather than inventing certainty.

Respond with ONLY a JSON array, no other text, matching this shape:
[{"title": str, "explanation": str, "supporting_evidence": [str, ...], \
"confidence": float between 0.0 and 1.0}]
"""


def _build_user_prompt(state: AgentState) -> str:
    parts = [f"User question: {state.get('user_query', '')}"]

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


def _parse_hypotheses(raw_response: str) -> list[Hypothesis]:
    """Parses the LLM's JSON array response into validated Hypothesis
    models. Raises ValueError on malformed output rather than silently
    returning an empty list — a diagnosis node failing loudly is safer
    than one that looks like it succeeded with zero hypotheses."""
    try:
        raw_items = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM response was not valid JSON: {exc}") from exc

    if not isinstance(raw_items, list):
        raise ValueError(f"Expected a JSON array of hypotheses, got {type(raw_items).__name__}")

    return [Hypothesis.model_validate(item) for item in raw_items]


def generate_hypotheses_node(
    state: AgentState, llm_client: LLMClient | None = None
) -> dict[str, Any]:
    llm_client = llm_client or _default_llm_client()

    user_prompt = _build_user_prompt(state)
    raw_response = llm_client.complete(_SYSTEM_PROMPT, user_prompt)
    hypotheses = _parse_hypotheses(raw_response)

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
        tools_called=["llm_client.complete"],
        reasoning=reasoning,
        evidence_summary=f"{len(hypotheses)} ranked hypothesis(es) produced",
    )

    return {"hypotheses": hypotheses, "trace": [trace_entry]}
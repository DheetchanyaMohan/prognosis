"""Prompt templates.

Every prompt used by an LLM-calling node lives here — nodes never inline
prompt text. build_user_prompt is a generic assembler shared by every
node; each node supplies only its own system prompt constant and its own
list of (heading, content) evidence sections, keeping this module
domain-agnostic (it knows nothing about RunDiagnostics, RetrievedChunk,
or any other app-specific type).
"""

from __future__ import annotations

from collections.abc import Sequence


def build_user_prompt(user_query: str, sections: Sequence[tuple[str, str]]) -> str:
    """Renders the user's question followed by each non-empty
    (heading, content) evidence section, in the order given.

    Shared by every LLM-calling node so prompt formatting is consistent
    everywhere an LLM is called, rather than reimplemented per node.
    Empty-content sections are omitted rather than rendered as an empty
    heading with nothing under it.
    """
    parts = [f"User question: {user_query}"]
    parts.extend(f"{heading}:\n{content}" for heading, content in sections if content)
    return "\n\n".join(parts)


HYPOTHESIS_GENERATION_SYSTEM_PROMPT = """You are an experienced ML engineer diagnosing a \
training run.

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


EXPERIMENT_PLANNING_SYSTEM_PROMPT = """You are an experienced ML engineer proposing next \
experiments.

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
"""Finalize node.

Last node in the diagnosis graph. Produces no new evidence, hypotheses,
or recommendations — its only job is to close out the trace with a
clear, human-readable summary of what the graph produced.

The "final structured response" this node is responsible for is the
AgentState itself once the graph terminates here — every consumer
(LangGraph's own .invoke() return value, the frontend, the eval harness)
already reads recommendations/hypotheses/diagnostics/trace directly off
AgentState, so finalize does not introduce a second, parallel output
shape to keep in sync with it.
"""

from __future__ import annotations

from typing import Any

from app.agent.state import AgentState, TraceEntry


def finalize_node(state: AgentState) -> dict[str, Any]:
    request_type = state.get("request_type", "general_question")
    selected_run = state.get("selected_run")
    recommendations = state.get("recommendations", [])
    hypotheses = state.get("hypotheses", [])

    if recommendations:
        summary = (
            f"Produced {len(recommendations)} recommendation(s) for a {request_type!r} "
            f"request on {selected_run or 'no specific run'}, backed by "
            f"{len(hypotheses)} hypothesis(es)."
        )
    elif hypotheses:
        summary = (
            f"Produced {len(hypotheses)} hypothesis(es) but no recommendations for a "
            f"{request_type!r} request on {selected_run or 'no specific run'}."
        )
    else:
        summary = f"Answered a {request_type!r} request with no run-specific analysis."

    trace_entry = TraceEntry(
        node="finalize",
        tools_called=[],
        reasoning=f"Diagnosis workflow complete. {summary}",
        evidence_summary=(
            f"{len(hypotheses)} hypothesis(es), {len(recommendations)} recommendation(s)"
        ),
    )

    return {"trace": [trace_entry]}
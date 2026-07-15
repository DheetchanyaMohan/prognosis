"""Router node.

First node in the diagnosis graph. Classifies the user's request,
resolves any run references via app.tools.experiment_tool, and
initializes the parts of AgentState every downstream node depends on.

Performs no retrieval and no analysis — those belong to retrieve_context
and analyze_metrics respectively. Classification here is deliberately
rule-based (regex + keyword matching), not an LLM call: routing is a
cheap, deterministic decision, and keeping it rule-based makes it fully
unit-testable without a model in the loop.
"""

from __future__ import annotations

import re
from typing import Any

from app.agent.state import AgentState, RequestType, TraceEntry
from app.tools import experiment_tool

_RUN_ID_PATTERN = re.compile(r"\brun_\d{3}\b")

#: Phrases suggesting the user means "my most recent run" without naming
#: one explicitly, e.g. "why is my model overfitting?".
_IMPLICIT_RECENT_RUN_PHRASES = (
    "my model", "my run", "my experiment", "this run", "the run",
    "latest run", "latest experiment", "current run",
)

#: Phrases suggesting the user wants two runs compared against each other.
_COMPARISON_PHRASES = ("compare", " vs ", " vs. ", "versus", "difference between")


def _extract_run_ids(query: str) -> list[str]:
    """Finds run_XXX-style references in the query, de-duplicated while
    preserving order of first appearance."""
    seen: dict[str, None] = {}
    for match in _RUN_ID_PATTERN.finditer(query.lower()):
        seen.setdefault(match.group(0), None)
    return list(seen.keys())


def _mentions_comparison(query: str) -> bool:
    lowered = query.lower()
    return any(phrase in lowered for phrase in _COMPARISON_PHRASES)


def _mentions_implicit_recent_run(query: str) -> bool:
    lowered = query.lower()
    return any(phrase in lowered for phrase in _IMPLICIT_RECENT_RUN_PHRASES)


def router_node(state: AgentState) -> dict[str, Any]:
    query = state.get("user_query", "")
    tools_called: list[str] = []

    # Resolve every run_id literally mentioned in the query, dropping any
    # that don't actually exist rather than failing the whole request —
    # a typo'd run_id degrades to a general question, it doesn't crash.
    mentioned_run_ids = _extract_run_ids(query)
    resolved_ids: list[str] = []
    unresolved_ids: list[str] = []
    for run_id in mentioned_run_ids:
        tools_called.append("experiment_tool.get_run")
        try:
            experiment_tool.get_run(run_id)
        except experiment_tool.RunNotFoundError:
            unresolved_ids.append(run_id)
        else:
            resolved_ids.append(run_id)

    request_type: RequestType
    selected_run: str | None = None
    comparison_run: str | None = None

    if len(resolved_ids) >= 2:
        request_type = "compare_runs"
        selected_run, comparison_run = resolved_ids[0], resolved_ids[1]

    elif len(resolved_ids) == 1 and _mentions_comparison(query):
        # A comparison was requested but only one run was named explicitly;
        # compare against the most recent other run as the natural baseline.
        tools_called.append("experiment_tool.list_recent_runs")
        selected_run = resolved_ids[0]
        comparison_run = next(
            (
                r.run_id
                for r in experiment_tool.list_recent_runs(limit=5)
                if r.run_id != selected_run
            ),
            None,
        )
        request_type = "compare_runs" if comparison_run is not None else "diagnose_run"

    elif len(resolved_ids) == 1:
        request_type = "diagnose_run"
        selected_run = resolved_ids[0]

    elif _mentions_implicit_recent_run(query):
        tools_called.append("experiment_tool.list_recent_runs")
        recent = experiment_tool.list_recent_runs(limit=1)
        if recent:
            request_type = "diagnose_run"
            selected_run = recent[0].run_id
        else:
            request_type = "general_question"

    else:
        request_type = "general_question"

    reasoning_parts = [f"Classified request as {request_type!r}."]
    if mentioned_run_ids:
        reasoning_parts.append(f"Run references found in query: {mentioned_run_ids}.")
    if unresolved_ids:
        reasoning_parts.append(f"Could not resolve run id(s) {unresolved_ids}; ignored.")
    if selected_run:
        reasoning_parts.append(f"Selected run: {selected_run}.")
    if comparison_run:
        reasoning_parts.append(f"Comparison run: {comparison_run}.")

    trace_entry = TraceEntry(
        node="router",
        tools_called=tools_called,
        reasoning=" ".join(reasoning_parts),
        evidence_summary=(
            f"request_type={request_type!r}, selected_run={selected_run!r}, "
            f"comparison_run={comparison_run!r}"
        ),
    )

    return {
        "request_type": request_type,
        "selected_run": selected_run,
        "comparison_run": comparison_run,
        "trace": [trace_entry],
    }
"""Analyze Metrics node.

Third node in the diagnosis graph. Calls app.tools.metrics_tool to
compute (diagnose_run requests) or compare (compare_runs requests)
deterministic metrics for the request's selected run(s). Performs no
retrieval and no synthesis — it only gathers the deterministic evidence
that generate_hypotheses reasons over next. No metric is computed here;
every number comes straight from metrics_tool, which itself defers to
the deterministic analysis layer.
"""

from __future__ import annotations

from typing import Any

from app.agent.state import AgentState, TraceEntry
from app.tools import metrics_tool
from app.tools.experiment_tool import RunNotFoundError
from app.tools.schemas import RunComparisonResult, RunDiagnostics, RunSummaryView


def analyze_metrics_node(state: AgentState) -> dict[str, Any]:
    request_type = state.get("request_type", "general_question")
    selected_run = state.get("selected_run")
    comparison_run = state.get("comparison_run")

    tools_called: list[str] = []
    diagnostics: RunDiagnostics | None = None
    run_summary: RunSummaryView | None = None
    comparison: RunComparisonResult | None = None
    reasoning: str

    if request_type == "compare_runs" and selected_run and comparison_run:
        tools_called.append("metrics_tool.compare_runs")
        try:
            comparison = metrics_tool.compare_runs(selected_run, comparison_run)
        except RunNotFoundError as exc:
            reasoning = (
                f"Requested comparison between {selected_run!r} and "
                f"{comparison_run!r}, but {exc}"
            )
        else:
            diagnostics = comparison.run_a_diagnostics
            changed_fields = [d.field for d in comparison.config_differences]
            reasoning = (
                f"Compared {selected_run} against {comparison_run}: "
                f"{len(comparison.config_differences)} hyperparameter(s) differ "
                f"({changed_fields})."
            )

    elif request_type == "diagnose_run" and selected_run:
        tools_called.append("metrics_tool.summarize_run")
        try:
            run_summary = metrics_tool.summarize_run(selected_run)
        except RunNotFoundError as exc:
            reasoning = f"Requested diagnosis of {selected_run!r}, but {exc}"
        except ValueError as exc:
            # The deterministic analysis layer raises this when a run has
            # no completed epochs yet — a real, expected condition, not a bug.
            reasoning = f"Could not analyze {selected_run!r}: {exc}"
        else:
            diagnostics = run_summary.diagnostics
            reasoning = (
                f"Analyzed {selected_run}: generalization gap trend is "
                f"{diagnostics.generalization_gap.trend!r}, "
                f"plateaued={diagnostics.plateau.plateaued}, "
                f"unstable={diagnostics.instability.is_unstable}."
            )

    elif request_type in ("compare_runs", "diagnose_run"):
        # Router classified the request as needing a run, but didn't
        # actually resolve one (e.g. compare_runs with no baseline found).
        reasoning = (
            f"Request classified as {request_type!r} but no run was resolved "
            "by the router; skipping metric analysis."
        )

    else:
        reasoning = "General knowledge question; no metrics tools were called."

    trace_entry = TraceEntry(
        node="analyze_metrics",
        tools_called=tools_called,
        reasoning=reasoning,
        evidence_summary=(
            f"diagnostics={'present' if diagnostics else 'none'}, "
            f"comparison={'present' if comparison else 'none'}"
        ),
    )

    return {
        "diagnostics": diagnostics,
        "run_summary": run_summary,
        "comparison": comparison,
        "trace": [trace_entry],
    }
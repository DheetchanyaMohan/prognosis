"""Diagnosis service: the one place that invokes the LangGraph workflow.

This is the entire "DiagnosisService" layer in the architecture:

    FastAPI endpoint -> DiagnosisService -> LangGraph workflow -> Structured response

Both app.api.routes.diagnosis and scripts/validate_agent.py call
run_diagnosis() — neither builds a graph, constructs a query, or reads
AgentState fields itself. This is deliberate: there is exactly one
implementation of "run the diagnosis workflow and turn it into a typed
response," so a change to how the graph is invoked or how its output is
shaped never needs to happen in two places.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.agent.graph import build_graph
from app.services.schemas import DiagnosisResponse
from app.tools import experiment_tool

DEFAULT_QUERY_TEMPLATE = (
    "Why did {run_id} behave the way it did during training, and what should I try next?"
)


def _build_default_query(run_id: str) -> str:
    return DEFAULT_QUERY_TEMPLATE.format(run_id=run_id)


def run_diagnosis(
    run_id: str, query: str | None = None, db: Session | None = None
) -> DiagnosisResponse:
    """Runs the complete LangGraph diagnosis workflow for `run_id` and
    returns its full output as a typed DiagnosisResponse.

    Validates `run_id` exists *before* invoking the graph — a REST
    resource path naming a run that doesn't exist should fail fast with
    a clear error, rather than spend an LLM call on a request the router
    would only degrade into a generic "general_question" for anyway.
    Raises RunNotFoundError (from app.tools.experiment_tool) if it
    doesn't; callers (the API route) translate that into a 404.

    `query` overrides the default diagnostic phrasing — useful for a
    custom question (e.g. one naming a second run to compare against),
    but the request is always anchored to `run_id` as the primary
    subject, matching the REST resource this service backs
    (`POST /api/v1/runs/{run_id}/diagnose`).

    Any exception raised while the graph itself executes (LLMProviderError,
    StructuredOutputError, or anything else) propagates unchanged — this
    function does not catch or reinterpret graph-execution failures;
    that classification is the API route's job (see
    app.api.routes.diagnosis), so scripts/validate_agent.py sees the
    exact same exception types a test or a future caller would.
    """
    # Fails fast and clearly for an unknown run_id, before any LLM call.
    experiment_tool.get_run(run_id, db=db)

    resolved_query = query or _build_default_query(run_id)

    graph = build_graph()
    result = graph.invoke({"user_query": resolved_query})

    return DiagnosisResponse(
        run_id=run_id,
        generated_at=datetime.now(UTC),
        user_query=resolved_query,
        request_type=result.get("request_type", "general_question"),
        selected_run=result.get("selected_run"),
        comparison_run=result.get("comparison_run"),
        retrieved_knowledge=result.get("retrieved_knowledge", []),
        similar_runs=result.get("similar_runs", []),
        diagnostics=result.get("diagnostics"),
        run_summary=result.get("run_summary"),
        comparison=result.get("comparison"),
        hypotheses=result.get("hypotheses", []),
        recommendations=result.get("recommendations", []),
        retry_count=result.get("retry_count", 0),
        needs_more_evidence=result.get("needs_more_evidence", False),
        trace=result.get("trace", []),
    )
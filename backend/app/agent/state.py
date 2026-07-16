"""Graph state for the LangGraph diagnosis workflow.

This module defines the state schema only — no node logic, no tool
calls, no LLM calls. Nodes (app.agent.nodes.*) read this state and return
partial updates to it; app.agent.graph wires the nodes together around
this shape.
"""

from __future__ import annotations

import operator
from datetime import UTC, datetime
from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field

from app.llm.models import Hypothesis, Recommendation
from app.rag.schemas import RetrievedChunk
from app.tools.schemas import RunComparisonResult, RunDiagnostics, RunSummaryView

#: What the router classified the user's request as.
RequestType = Literal["diagnose_run", "compare_runs", "general_question"]


class TraceEntry(BaseModel):
    """One step of the agent's execution trace.

    Every node appends exactly one of these. This is what the frontend's
    live execution view renders — each entry must be enough, on its own,
    for a person to understand what the node did and why without reading
    code.
    """

    model_config = ConfigDict(extra="forbid")

    node: str = Field(description="Name of the node that produced this entry")
    tools_called: list[str] = Field(
        default_factory=list,
        description="Fully-qualified tools invoked by this node, e.g. 'metrics_tool.analyze_run'",
    )
    reasoning: str = Field(description="Why this node did what it did, in plain language")
    evidence_summary: str = Field(
        description="A short, concrete description of what evidence or output this step produced"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentState(TypedDict, total=False):
    """The full LangGraph state.

    total=False: every node returns only the keys it updates, and
    LangGraph merges that partial dict into the running state — no node
    has to restate fields it didn't touch.

    `trace`, `retrieved_knowledge`, and `similar_runs` use an `operator.add`
    reducer so that a self_check-triggered retry *extends* the evidence
    already gathered (and the trace already recorded) instead of
    overwriting it; every other field is last-write-wins, which is
    LangGraph's default merge behavior for a TypedDict field with no
    reducer annotation.
    """

    # Input
    user_query: str

    # Router output
    request_type: RequestType
    selected_run: str | None
    comparison_run: str | None

    # Retrieve Context output (accumulates across a retry)
    retrieved_knowledge: Annotated[list[RetrievedChunk], operator.add]
    similar_runs: Annotated[list[RetrievedChunk], operator.add]

    # Analyze Metrics output
    diagnostics: RunDiagnostics | None
    run_summary: RunSummaryView | None
    comparison: RunComparisonResult | None

    # Generate Hypotheses output
    hypotheses: list[Hypothesis]

    # Plan Experiments output
    recommendations: list[Recommendation]

    # Self Check control
    retry_count: int
    needs_more_evidence: bool

    # Explainability (accumulates across the whole run)
    trace: Annotated[list[TraceEntry], operator.add]
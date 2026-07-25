"""Response contract for the LangGraph diagnosis workflow.

DiagnosisResponse is the single, complete, typed shape of "everything the
agent produced" for one diagnosis run. Both app.api.routes.diagnosis and
scripts/validate_agent.py consume this exact model — there is no second,
API-only or script-only response shape. Every nested field reuses an
existing Pydantic model from elsewhere in the codebase (app.agent.state,
app.llm.models, app.rag.schemas, app.tools.schemas) rather than
redefining an equivalent one here, so this module owns only the
top-level envelope.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.agent.state import RequestType, TraceEntry
from app.llm.models import Hypothesis, Recommendation
from app.rag.schemas import RetrievedChunk
from app.tools.schemas import RunComparisonResult, RunDiagnostics, RunSummaryView


class DiagnosisResponse(BaseModel):
    """The complete output of one LangGraph diagnosis run — every field
    the graph itself produced, not a reduced summary. The execution
    trace is included deliberately: the diagnosis *process* (what was
    retrieved, what the router decided, whether a retry happened) is as
    much a feature of this project as the final recommendations.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(description="The run_id this diagnosis was requested for (path param)")
    generated_at: datetime = Field(description="When this diagnosis was produced")

    user_query: str = Field(description="The question sent to the agent (default or custom)")
    request_type: RequestType = Field(
        description="The router's classification: diagnose_run, compare_runs, or general_question"
    )
    selected_run: str | None = Field(
        description="The run_id the router resolved as the primary subject, if any"
    )
    comparison_run: str | None = Field(
        description="The second run_id being compared against, if request_type is compare_runs"
    )

    retrieved_knowledge: list[RetrievedChunk] = Field(
        description="Knowledge-base chunks retrieved as evidence (may be empty)"
    )
    similar_runs: list[RetrievedChunk] = Field(
        description="Prior-run-summary chunks retrieved as evidence (may be empty)"
    )

    diagnostics: RunDiagnostics | None = Field(
        description="Deterministic diagnostics for selected_run, if request_type needed them"
    )
    run_summary: RunSummaryView | None = Field(
        description="Config + diagnostics bundle for selected_run, if request_type is diagnose_run"
    )
    comparison: RunComparisonResult | None = Field(
        description="Diagnostics + config diff for both runs, if request_type is compare_runs"
    )

    hypotheses: list[Hypothesis] = Field(
        description="Ranked candidate explanations, each with its own supporting_evidence"
    )
    recommendations: list[Recommendation] = Field(
        description="Ranked next-experiment recommendations, each with its own provenance"
    )

    retry_count: int = Field(description="How many times self_check requested more evidence")
    needs_more_evidence: bool = Field(
        description="self_check's final verdict — always False once the graph has finalized"
    )

    trace: list[TraceEntry] = Field(
        description="One entry per node executed, in order — the full execution process"
    )
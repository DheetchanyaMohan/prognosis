"""API-layer response models.

Where a tool-layer model (app.tools.schemas.ExperimentRecord,
RunDiagnostics, app.config.schema.RunConfig, ...) already fits a
response exactly, routes return it directly instead of wrapping it in a
duplicate model here. This module only defines shapes the tool layer
doesn't already have a model for: the health check, and the Pydantic
mirror of the summary.json shape (app.data_generation.summary.RunSummary
is a plain dataclass, written to disk — this is the validated shape the
API returns after reading it back).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.config.schema import RunConfig
from app.tools.schemas import RunDiagnostics


class HealthComponentStatus(BaseModel):
    """Status of a single dependency the app relies on."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error", "not_configured"]
    detail: str | None = None


class HealthResponse(BaseModel):
    """GET /health response. `status` is 'degraded' if any component that
    the app cannot function without (database, chroma) reports 'error';
    an unconfigured LLM provider is a valid, non-degraded dev-time state.
    """

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "degraded"]
    database: HealthComponentStatus
    chroma: HealthComponentStatus
    llm_provider: HealthComponentStatus


class RunSummaryResponse(BaseModel):
    """Mirrors app.data_generation.summary.RunSummary field-for-field."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    total_epochs_completed: int
    best_epoch: int
    best_val_loss: float
    final_train_loss: float
    final_val_loss: float
    final_train_acc: float
    final_val_acc: float
    wall_clock_sec: float
    diverged: bool
    description: str


class RunDetailResponse(BaseModel):
    """GET /runs/{run_id} response: config, summary, and diagnostics for
    one run. summary/diagnostics are None rather than a 404 when their
    files don't exist yet — a run mid-training or freshly trained but
    not yet diagnosed is a normal state, not an error."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    config: RunConfig
    summary: RunSummaryResponse | None = Field(
        default=None, description="None if summary.json has not been generated yet"
    )
    diagnostics: RunDiagnostics | None = Field(
        default=None, description="None if diagnostics.json has not been generated yet"
    )


class DiagnoseRequest(BaseModel):
    """POST /runs/{run_id}/diagnose request body — entirely optional; an
    empty or absent body runs the default diagnostic query for the run
    named in the path. This is the only request model this feature adds:
    the response shape (DiagnosisResponse) is owned by app.services,
    since scripts/validate_agent.py returns the identical object with no
    HTTP layer involved at all.
    """

    model_config = ConfigDict(extra="forbid")

    query: str | None = Field(
        default=None,
        description=(
            "Custom question for the agent, e.g. one naming a second run to "
            "compare against. If omitted, a default 'why did this run behave "
            "this way and what should I try next' query is used."
        ),
    )
"""Structured outputs for the deterministic analysis layer and the agent
tool layer built on top of it.

Every analysis function in app.tools.metrics_analysis, and every function
in app.tools.metrics_tool / experiment_tool / retrieval_tool, returns one
of these models — never a plain dict — so consumers (training pipeline,
LangGraph nodes, the eval harness, the frontend) get a typed, validated,
self-documenting contract instead of guessing dict keys.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GeneralizationGapResult(BaseModel):
    """Train/val gap at the final epoch in the history, plus its trend
    over the run so far."""

    model_config = ConfigDict(extra="forbid")

    epoch: int = Field(description="Epoch this measurement is taken at (the last epoch in history)")
    train_loss: float
    val_loss: float
    loss_gap: float = Field(description="val_loss - train_loss; positive means val is worse")
    loss_gap_pct: float = Field(description="loss_gap relative to train_loss, as a percentage")
    train_acc: float
    val_acc: float
    accuracy_gap: float = Field(
        description="train_acc - val_acc; positive means train outperforms val"
    )
    trend: Literal["widening", "narrowing", "stable"] = Field(
        description=(
            "Compares mean loss_gap in the second half of the run vs the first half. "
            "'stable' is also returned when fewer than 4 epochs are available, since "
            "there isn't enough data to call a trend meaningfully."
        )
    )


class PlateauResult(BaseModel):
    """Whether a metric has flatlined over its most recent epochs."""

    model_config = ConfigDict(extra="forbid")

    metric: Literal["train_loss", "val_loss"]
    window: int = Field(description="Number of most recent epochs examined")
    threshold: float = Field(description="Max allowed range within the window to call it a plateau")
    plateaued: bool
    plateau_start_epoch: int | None = Field(
        description=(
            "Epoch at the start of the earliest window that already satisfies the "
            "flatness condition; None if not plateaued or if there isn't enough data"
        )
    )
    observed_range: float | None = Field(
        description="max-min of the metric over the most recent window; None if insufficient data"
    )
    insufficient_data: bool = Field(
        description="True if epoch_history has fewer than `window` epochs"
    )


class InstabilityResult(BaseModel):
    """Whether a metric shows sharp spikes or high overall volatility."""

    model_config = ConfigDict(extra="forbid")

    metric: Literal["train_loss", "val_loss"]
    spike_relative_threshold: float = Field(
        description="An epoch-over-epoch relative increase above this counts as a spike"
    )
    coefficient_of_variation_threshold: float = Field(
        description="Overall std/mean above this flags high volatility without a single spike"
    )
    is_unstable: bool = Field(
        description="True if any spike occurred or the CV threshold was exceeded"
    )
    spike_epochs: list[int] = Field(description="Epochs where a spike was detected")
    coefficient_of_variation: float = Field(
        description="std/mean of the metric across the full history"
    )


class BestEpochResult(BaseModel):
    """The epoch with the lowest validation loss."""

    model_config = ConfigDict(extra="forbid")

    epoch: int
    val_loss: float
    train_loss: float
    val_acc: float
    train_acc: float


class RunDiagnostics(BaseModel):
    """The full deterministic diagnostics bundle for one run — this is
    exactly what gets serialized to diagnostics.json."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    total_epochs: int
    generalization_gap: GeneralizationGapResult
    plateau: PlateauResult
    instability: InstabilityResult
    best_epoch: BestEpochResult


# --- Agent tool layer -------------------------------------------------
#
# The models below are returned by app.tools.experiment_tool and
# app.tools.metrics_tool — the abstraction boundary LangGraph nodes call
# through instead of touching SQLAlchemy, config.yaml, or diagnostics.json
# directly.


class RunRecord(BaseModel):
    """Tool-facing metadata about a single run — deliberately narrower
    than the ORM Run row (no file paths, no relationship objects)."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    experiment_name: str
    status: str
    created_at: datetime
    total_epochs: int = Field(description="Number of completed Metric rows for this run")


class ExperimentRecord(BaseModel):
    """Tool-facing metadata about an experiment and the runs within it."""

    model_config = ConfigDict(extra="forbid")

    experiment_name: str
    description: str | None
    created_at: datetime
    run_ids: list[str]


class RunSearchFilters(BaseModel):
    """Optional filters for experiment_tool.search_runs. All fields
    default to None, meaning "don't filter on this"."""

    model_config = ConfigDict(extra="forbid")

    experiment_name: str | None = None
    status: str | None = None


class RunConfigSummary(BaseModel):
    """A compact, tool-facing view of a run's hyperparameters — the
    fields most relevant to diagnosis and comparison, not the full
    RunConfig (which also carries seed, description, and run/experiment
    identifiers that aren't useful for a hyperparameter-level diff)."""

    model_config = ConfigDict(extra="forbid")

    train_size: int
    val_size: int
    augmentation: bool
    dropout: float
    optimizer: str
    lr: float
    lr_scheduler: str
    batch_size: int
    weight_decay: float
    epochs: int


class RunSummaryView(BaseModel):
    """Full contextual view of one run: metadata + config + diagnostics —
    what an agent needs before generating hypotheses about it, assembled
    without ever reading summary.json directly."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    experiment_name: str
    status: str
    created_at: datetime
    config: RunConfigSummary
    diagnostics: RunDiagnostics


class ConfigDiffEntry(BaseModel):
    """One hyperparameter that differs between two compared runs."""

    model_config = ConfigDict(extra="forbid")

    field: str
    run_a_value: float | int | str | bool
    run_b_value: float | int | str | bool


class RunComparisonResult(BaseModel):
    """Diagnostics for two runs, plus the hyperparameters that differ
    between them — the evidence a compare_experiments node needs."""

    model_config = ConfigDict(extra="forbid")

    run_a_id: str
    run_b_id: str
    run_a_diagnostics: RunDiagnostics
    run_b_diagnostics: RunDiagnostics
    config_differences: list[ConfigDiffEntry]
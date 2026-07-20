"""Deterministic analysis functions.

This module is the foundation of the diagnosis system and is deliberately
independent of LangGraph, RAG, FastAPI, and any LLM — every function here
is a pure, typed, unit-tested computation over `EpochMetrics`. The exact
same functions are called by:
  - the training pipeline, to generate diagnostics.json after training
  - future agent tools, for live diagnosis of an uploaded/selected run
  - the evaluation framework, to check the agent's diagnosis against them
  - the frontend dashboard, for direct display

Thresholds are module-level constants, each documented at its definition.
They were chosen for CrossEntropyLoss-scale losses (roughly 0-3) on this
project's CIFAR-10 subset task — recalibrate if this module is ever
pointed at a differently-scaled loss.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

from app.data_generation.metrics_writer import EpochMetrics
from app.models import Metric
from app.tools.schemas import (
    BestEpochResult,
    GeneralizationGapResult,
    InstabilityResult,
    PlateauResult,
    RunDiagnostics,
)

# --- Documented thresholds -------------------------------------------------

#: Minimum epochs needed before a generalization-gap trend is meaningful;
#: below this, `trend` is reported as "stable" rather than guessed at.
GAP_TREND_MIN_EPOCHS = 4

#: Absolute change in mean loss_gap between the first and second half of
#: the run required to call the trend "widening" or "narrowing" rather
#: than "stable".
GAP_TREND_DELTA_THRESHOLD = 0.02

#: Number of most recent epochs examined for plateau detection.
DEFAULT_PLATEAU_WINDOW = 5

#: Max allowed (max - min) range of the metric within the plateau window.
#: Loss moving by less than this over `DEFAULT_PLATEAU_WINDOW` epochs is
#: considered flat.
DEFAULT_PLATEAU_RANGE_THRESHOLD = 0.02

#: An epoch-over-epoch relative increase above this counts as a loss spike.
DEFAULT_SPIKE_RELATIVE_THRESHOLD = 0.5

#: Coefficient of variation (std / mean) above this, across the full run,
#: flags high volatility even without any single sharp spike.
DEFAULT_INSTABILITY_CV_THRESHOLD = 0.3


# --- Internal helpers --------------------------------------------------


def _require_nonempty(epoch_history: list[EpochMetrics]) -> None:
    if not epoch_history:
        raise ValueError("epoch_history must contain at least one epoch")


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values)


def _metric_value(metrics: EpochMetrics, metric: Literal["train_loss", "val_loss"]) -> float:
    return metrics.train_loss if metric == "train_loss" else metrics.val_loss


# --- Public analysis functions ------------------------------------------


def compute_generalization_gap(
    epoch_history: list[EpochMetrics],
    trend_delta_threshold: float = GAP_TREND_DELTA_THRESHOLD,
) -> GeneralizationGapResult:
    """Train/val gap at the final epoch, plus its trend over the run."""
    _require_nonempty(epoch_history)
    final = epoch_history[-1]

    loss_gap = final.val_loss - final.train_loss
    loss_gap_pct = (loss_gap / final.train_loss * 100) if final.train_loss != 0 else 0.0
    accuracy_gap = final.train_acc - final.val_acc

    trend: Literal["widening", "narrowing", "stable"] = "stable"
    if len(epoch_history) >= GAP_TREND_MIN_EPOCHS:
        mid = len(epoch_history) // 2
        first_half_gap = _mean(m.val_loss - m.train_loss for m in epoch_history[:mid])
        second_half_gap = _mean(m.val_loss - m.train_loss for m in epoch_history[mid:])
        delta = second_half_gap - first_half_gap
        if delta > trend_delta_threshold:
            trend = "widening"
        elif delta < -trend_delta_threshold:
            trend = "narrowing"

    return GeneralizationGapResult(
        epoch=final.epoch,
        train_loss=final.train_loss,
        val_loss=final.val_loss,
        loss_gap=loss_gap,
        loss_gap_pct=loss_gap_pct,
        train_acc=final.train_acc,
        val_acc=final.val_acc,
        accuracy_gap=accuracy_gap,
        trend=trend,
    )


def detect_plateau(
    epoch_history: list[EpochMetrics],
    metric: Literal["train_loss", "val_loss"] = "val_loss",
    window: int = DEFAULT_PLATEAU_WINDOW,
    range_threshold: float = DEFAULT_PLATEAU_RANGE_THRESHOLD,
) -> PlateauResult:
    """A run is plateaued if `metric`'s (max - min) range over the most
    recent `window` epochs is at or below `range_threshold`. Needs at
    least `window` epochs; fewer returns insufficient_data=True.
    """
    _require_nonempty(epoch_history)
    values = [_metric_value(m, metric) for m in epoch_history]
    epochs = [m.epoch for m in epoch_history]

    if len(values) < window:
        return PlateauResult(
            metric=metric,
            window=window,
            threshold=range_threshold,
            plateaued=False,
            plateau_start_epoch=None,
            observed_range=None,
            insufficient_data=True,
        )

    tail = values[-window:]
    observed_range = max(tail) - min(tail)
    plateaued = observed_range <= range_threshold

    plateau_start_epoch: int | None = None
    if plateaued:
        # Scan forward for the earliest window that already satisfies the
        # flatness condition, so plateau_start_epoch reflects when it began.
        for start in range(0, len(values) - window + 1):
            window_values = values[start : start + window]
            if max(window_values) - min(window_values) <= range_threshold:
                plateau_start_epoch = epochs[start]
                break

    return PlateauResult(
        metric=metric,
        window=window,
        threshold=range_threshold,
        plateaued=plateaued,
        plateau_start_epoch=plateau_start_epoch,
        observed_range=observed_range,
        insufficient_data=False,
    )


def detect_instability(
    epoch_history: list[EpochMetrics],
    metric: Literal["train_loss", "val_loss"] = "train_loss",
    spike_relative_threshold: float = DEFAULT_SPIKE_RELATIVE_THRESHOLD,
    cv_threshold: float = DEFAULT_INSTABILITY_CV_THRESHOLD,
) -> InstabilityResult:
    """Combines two independent instability signals:

    1. Spikes: any epoch where `metric` increased by more than
       `spike_relative_threshold` relative to the previous epoch.
    2. Overall volatility: coefficient of variation (std / mean) of
       `metric` across the full history, flagged if it exceeds
       `cv_threshold`.

    is_unstable is True if either signal fires.
    """
    _require_nonempty(epoch_history)
    values = [_metric_value(m, metric) for m in epoch_history]
    epochs = [m.epoch for m in epoch_history]

    spike_epochs: list[int] = []
    for i in range(1, len(values)):
        previous = values[i - 1]
        if previous <= 0:
            continue  # relative comparison is undefined/meaningless here
        relative_increase = (values[i] - previous) / previous
        if relative_increase > spike_relative_threshold:
            spike_epochs.append(epochs[i])

    coefficient_of_variation = 0.0
    if len(values) >= 2:
        mean_value = _mean(values)
        if mean_value > 0:
            variance = sum((v - mean_value) ** 2 for v in values) / len(values)
            coefficient_of_variation = (variance**0.5) / mean_value

    is_unstable = bool(spike_epochs) or coefficient_of_variation > cv_threshold

    return InstabilityResult(
        metric=metric,
        spike_relative_threshold=spike_relative_threshold,
        coefficient_of_variation_threshold=cv_threshold,
        is_unstable=is_unstable,
        spike_epochs=spike_epochs,
        coefficient_of_variation=coefficient_of_variation,
    )


def select_best_epoch(epoch_history: list[EpochMetrics]) -> BestEpochResult:
    """Best epoch = lowest val_loss. Ties broken by the earliest epoch,
    since Python's min() keeps the first item encountered on a tie and
    epoch_history is expected in ascending epoch order.
    """
    _require_nonempty(epoch_history)
    best = min(epoch_history, key=lambda m: m.val_loss)
    return BestEpochResult(
        epoch=best.epoch,
        val_loss=best.val_loss,
        train_loss=best.train_loss,
        val_acc=best.val_acc,
        train_acc=best.train_acc,
    )


def summarize_run(run_id: str, epoch_history: list[EpochMetrics]) -> RunDiagnostics:
    """Bundles all four analyses into the single object serialized to
    diagnostics.json."""
    _require_nonempty(epoch_history)
    return RunDiagnostics(
        run_id=run_id,
        total_epochs=len(epoch_history),
        generalization_gap=compute_generalization_gap(epoch_history),
        plateau=detect_plateau(epoch_history),
        instability=detect_instability(epoch_history),
        best_epoch=select_best_epoch(epoch_history),
    )


# --- diagnostics.json generation -----------------------------------------


def write_diagnostics(diagnostics: RunDiagnostics, path: Path) -> None:
    """Thin wrapper: serializes an already-computed RunDiagnostics to disk.
    The training pipeline calls summarize_run() then this, after training
    completes — no analysis logic lives here, only serialization.
    """
    with path.open("w", encoding="utf-8") as f:
        f.write(diagnostics.model_dump_json(indent=2))
        f.write("\n")


def load_diagnostics(path: Path) -> RunDiagnostics:
    """Reads a previously written diagnostics.json back into a RunDiagnostics."""
    with path.open("r", encoding="utf-8") as f:
        return RunDiagnostics.model_validate(json.load(f))


# --- ORM bridge -----------------------------------------------------------


def epoch_history_from_metric_rows(rows: list[Metric]) -> list[EpochMetrics]:
    """Converts ORM Metric rows (what a DB-querying agent tool will have)
    into the EpochMetrics list every function above expects. Metric
    columns are nullable at the DB level; a row missing any numeric field
    is skipped as unusable for analysis. Result is sorted by epoch.
    """
    result: list[EpochMetrics] = []
    for row in sorted(rows, key=lambda r: r.epoch):
        row_values = (
            row.train_loss, row.val_loss, row.train_acc,
            row.val_acc, row.lr, row.epoch_time_sec,
        )
        if None in row_values:
            continue
        result.append(
            EpochMetrics(
                epoch=row.epoch,
                train_loss=row.train_loss,  # type: ignore[arg-type]
                val_loss=row.val_loss,  # type: ignore[arg-type]
                train_acc=row.train_acc,  # type: ignore[arg-type]
                val_acc=row.val_acc,  # type: ignore[arg-type]
                lr=row.lr,  # type: ignore[arg-type]
                epoch_time_sec=row.epoch_time_sec,  # type: ignore[arg-type]
            )
        )
    return result
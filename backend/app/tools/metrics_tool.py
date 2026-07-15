"""Diagnosis, comparison, and summary tools.

This is the only interface LangGraph nodes use to reach per-run metrics
and diagnostics. Internally these functions reuse
app.tools.metrics_analysis rather than recomputing anything, and pull
epoch history live from the database via
epoch_history_from_metric_rows — diagnostics.json is never read here,
so a run's diagnosis always reflects its current Metric rows.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.config.loader import load_run_config
from app.models import Run
from app.tools._db import ExperimentNotFoundError, RunNotFoundError, get_run_or_raise, session_scope
from app.tools.metrics_analysis import epoch_history_from_metric_rows
from app.tools.metrics_analysis import summarize_run as _analyze_epoch_history
from app.tools.schemas import (
    ConfigDiffEntry,
    RunComparisonResult,
    RunConfigSummary,
    RunDiagnostics,
    RunSummaryView,
)

__all__ = [
    "analyze_run",
    "compare_runs",
    "summarize_run",
    "RunNotFoundError",
    "ExperimentNotFoundError",
]


def _config_summary_for(run: Run) -> RunConfigSummary:
    config = load_run_config(Path(run.config_path))
    return RunConfigSummary(
        train_size=config.dataset.train_size,
        val_size=config.dataset.val_size,
        augmentation=config.dataset.augmentation,
        dropout=config.model.dropout,
        optimizer=config.training.optimizer,
        lr=config.training.lr,
        lr_scheduler=config.training.lr_scheduler,
        batch_size=config.training.batch_size,
        weight_decay=config.training.weight_decay,
        epochs=config.training.epochs,
    )


def _diagnostics_for(run: Run) -> RunDiagnostics:
    epoch_history = epoch_history_from_metric_rows(run.metrics)
    return _analyze_epoch_history(run.run_name, epoch_history)


def analyze_run(run_id: str, db: Session | None = None) -> RunDiagnostics:
    """Full deterministic diagnostics bundle for one run (generalization
    gap, plateau, instability, best epoch), computed live from its
    Metric rows via the deterministic analysis layer.

    Raises RunNotFoundError if no such run exists, and ValueError (from
    the analysis layer) if the run has no completed epochs yet.
    """
    with session_scope(db) as session:
        run = get_run_or_raise(session, run_id)
        return _diagnostics_for(run)


def summarize_run(run_id: str, db: Session | None = None) -> RunSummaryView:
    """Full contextual view of one run: metadata + hyperparameters +
    diagnostics — what an agent needs before generating hypotheses about
    it. Broader than analyze_run, which returns diagnostics alone.

    Raises RunNotFoundError if no such run exists.
    """
    with session_scope(db) as session:
        run = get_run_or_raise(session, run_id)
        return RunSummaryView(
            run_id=run_id,
            experiment_name=run.experiment.name,
            status=run.status,
            created_at=run.created_at,
            config=_config_summary_for(run),
            diagnostics=_diagnostics_for(run),
        )


def compare_runs(run_a: str, run_b: str, db: Session | None = None) -> RunComparisonResult:
    """Diagnostics for both runs, plus a hyperparameter-level config
    diff — the evidence a compare_experiments node needs to explain what
    changed between two runs and how each turned out.

    Raises RunNotFoundError if either run_id doesn't exist.
    """
    with session_scope(db) as session:
        a = get_run_or_raise(session, run_a)
        b = get_run_or_raise(session, run_b)

        a_config = _config_summary_for(a)
        b_config = _config_summary_for(b)
        differences = [
            ConfigDiffEntry(
                field=field,
                run_a_value=getattr(a_config, field),
                run_b_value=getattr(b_config, field),
            )
            for field in RunConfigSummary.model_fields
            if getattr(a_config, field) != getattr(b_config, field)
        ]

        return RunComparisonResult(
            run_a_id=run_a,
            run_b_id=run_b,
            run_a_diagnostics=_diagnostics_for(a),
            run_b_diagnostics=_diagnostics_for(b),
            config_differences=differences,
        )
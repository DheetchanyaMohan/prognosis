"""Persists a completed run's metadata and per-epoch metrics using the
existing SQLAlchemy models (app.models.Experiment/Run/Metric). No new
persistence logic is defined here beyond wiring — the models already
carry the schema, cascades, and constraints.

Phase 2: the five artifact-path columns no longer exist on Run at all
(see app/models/run.py), so the empty-string placeholders Phase 1 needed
to satisfy their NOT NULL constraint are gone too — there is nothing
left to work around. Artifact paths are derived on demand via
app.tools.run_paths.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.data_generation.metrics_writer import EpochMetrics
from app.models import Experiment, Metric, Run


def get_or_create_experiment(
    db: Session, name: str, description: str | None = None
) -> Experiment:
    experiment = db.query(Experiment).filter(Experiment.name == name).one_or_none()
    if experiment is not None:
        return experiment
    experiment = Experiment(name=name, description=description)
    db.add(experiment)
    db.flush()  # populate experiment.id without committing the transaction yet
    return experiment


def persist_run(
    db: Session,
    experiment: Experiment,
    run_id: str,
    status: str,
    epoch_history: list[EpochMetrics],
) -> Run:
    run = Run(experiment=experiment, run_name=run_id, status=status)
    for m in epoch_history:
        run.metrics.append(
            Metric(
                epoch=m.epoch,
                train_loss=m.train_loss,
                val_loss=m.val_loss,
                train_acc=m.train_acc,
                val_acc=m.val_acc,
                lr=m.lr,
                epoch_time_sec=m.epoch_time_sec,
            )
        )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
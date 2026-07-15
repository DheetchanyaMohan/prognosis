"""Experiment and run metadata access.

This is the only interface LangGraph nodes use to reach experiment
metadata. No SQLAlchemy import should ever be necessary outside this
module (and app.tools.metrics_tool, which shares the same internal
session helper) for anything agent-facing.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Experiment, Run
from app.tools._db import ExperimentNotFoundError, RunNotFoundError, get_run_or_raise, session_scope
from app.tools.schemas import ExperimentRecord, RunRecord, RunSearchFilters

__all__ = [
    "get_run",
    "search_runs",
    "load_experiment",
    "list_recent_runs",
    "RunNotFoundError",
    "ExperimentNotFoundError",
]


def _to_run_record(run: Run) -> RunRecord:
    return RunRecord(
        run_id=run.run_name,
        experiment_name=run.experiment.name,
        status=run.status,
        created_at=run.created_at,
        total_epochs=len(run.metrics),
    )


def get_run(run_id: str, db: Session | None = None) -> RunRecord:
    """Looks up a single run by its run_id (e.g. 'run_005').

    Raises RunNotFoundError if no such run exists.
    """
    with session_scope(db) as session:
        run = get_run_or_raise(session, run_id)
        return _to_run_record(run)


def search_runs(
    filters: RunSearchFilters | None = None, db: Session | None = None
) -> list[RunRecord]:
    """Searches runs by optional experiment_name and/or status. With no
    filters, returns every run, ordered by creation time."""
    filters = filters or RunSearchFilters()
    with session_scope(db) as session:
        query = session.query(Run).join(Experiment)
        if filters.experiment_name is not None:
            query = query.filter(Experiment.name == filters.experiment_name)
        if filters.status is not None:
            query = query.filter(Run.status == filters.status)
        runs = query.order_by(Run.created_at).all()
        return [_to_run_record(r) for r in runs]


def load_experiment(experiment_name: str, db: Session | None = None) -> ExperimentRecord:
    """Looks up an experiment by name, including the run_ids within it.

    Raises ExperimentNotFoundError if no such experiment exists.
    """
    with session_scope(db) as session:
        experiment = (
            session.query(Experiment).filter(Experiment.name == experiment_name).one_or_none()
        )
        if experiment is None:
            raise ExperimentNotFoundError(f"No experiment found with name={experiment_name!r}")
        return ExperimentRecord(
            experiment_name=experiment.name,
            description=experiment.description,
            created_at=experiment.created_at,
            run_ids=[r.run_name for r in experiment.runs],
        )


def list_recent_runs(limit: int = 10, db: Session | None = None) -> list[RunRecord]:
    """Returns the most recently created runs, newest first, across all experiments."""
    with session_scope(db) as session:
        runs = session.query(Run).order_by(Run.created_at.desc()).limit(limit).all()
        return [_to_run_record(r) for r in runs]
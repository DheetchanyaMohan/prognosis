import pytest
from sqlalchemy.orm import Session

from app.data_generation.metrics_writer import EpochMetrics
from app.data_generation.persistence import get_or_create_experiment, persist_run
from app.tools.experiment_tool import (
    ExperimentNotFoundError,
    RunNotFoundError,
    get_run,
    list_recent_runs,
    load_experiment,
    search_runs,
)
from app.tools.schemas import RunSearchFilters


def _seed_run(db: Session, experiment_name: str, run_id: str, status: str = "complete") -> None:
    experiment = get_or_create_experiment(db, name=experiment_name)
    db.commit()
    persist_run(
        db=db, experiment=experiment, run_id=run_id,
        config_path="x", metrics_path="x", log_path="x", summary_path="x",
        diagnostics_path="x", status=status,
        epoch_history=[EpochMetrics(1, 0.5, 0.6, 0.7, 0.6, 0.001, 1.0)],
    )


def test_get_run_returns_expected_fields(db_session: Session) -> None:
    _seed_run(db_session, "exp_a", "run_001")

    record = get_run("run_001", db=db_session)

    assert record.run_id == "run_001"
    assert record.experiment_name == "exp_a"
    assert record.status == "complete"
    assert record.total_epochs == 1


def test_get_run_raises_when_missing(db_session: Session) -> None:
    with pytest.raises(RunNotFoundError):
        get_run("run_nonexistent", db=db_session)


def test_search_runs_no_filters_returns_all(db_session: Session) -> None:
    _seed_run(db_session, "exp_a", "run_001")
    _seed_run(db_session, "exp_b", "run_002")

    results = search_runs(db=db_session)
    assert {r.run_id for r in results} == {"run_001", "run_002"}


def test_search_runs_filters_by_experiment_name(db_session: Session) -> None:
    _seed_run(db_session, "exp_a", "run_001")
    _seed_run(db_session, "exp_b", "run_002")

    results = search_runs(RunSearchFilters(experiment_name="exp_a"), db=db_session)
    assert [r.run_id for r in results] == ["run_001"]


def test_search_runs_filters_by_status(db_session: Session) -> None:
    _seed_run(db_session, "exp_a", "run_001", status="complete")
    _seed_run(db_session, "exp_a", "run_002", status="diverged")

    results = search_runs(RunSearchFilters(status="diverged"), db=db_session)
    assert [r.run_id for r in results] == ["run_002"]


def test_load_experiment_returns_run_ids(db_session: Session) -> None:
    _seed_run(db_session, "exp_a", "run_001")
    _seed_run(db_session, "exp_a", "run_002")

    record = load_experiment("exp_a", db=db_session)
    assert record.experiment_name == "exp_a"
    assert set(record.run_ids) == {"run_001", "run_002"}


def test_load_experiment_raises_when_missing(db_session: Session) -> None:
    with pytest.raises(ExperimentNotFoundError):
        load_experiment("exp_nonexistent", db=db_session)


def test_list_recent_runs_respects_limit(db_session: Session) -> None:
    for i in range(5):
        _seed_run(db_session, "exp_a", f"run_{i:03d}")

    results = list_recent_runs(limit=3, db=db_session)
    assert len(results) == 3
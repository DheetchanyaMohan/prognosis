from sqlalchemy.orm import Session

from app.data_generation.metrics_writer import EpochMetrics
from app.data_generation.persistence import get_or_create_experiment, persist_run
from app.models import Metric, Run


def test_persist_run_creates_run_and_metrics(db_session: Session) -> None:
    experiment = get_or_create_experiment(db_session, name="exp_test", description="desc")
    db_session.commit()

    history = [
        EpochMetrics(1, 0.9, 1.0, 0.5, 0.4, 0.001, 1.2),
        EpochMetrics(2, 0.7, 0.8, 0.6, 0.5, 0.001, 1.1),
    ]
    run = persist_run(
        db=db_session,
        experiment=experiment,
        run_id="run_test",
        config_path="x", metrics_path="x", log_path="x", summary_path="x",
        diagnostics_path="x", status="complete",
        epoch_history=history,
    )

    assert run.id is not None
    assert db_session.query(Run).count() == 1
    assert db_session.query(Metric).count() == 2


def test_get_or_create_experiment_is_idempotent(db_session: Session) -> None:
    first = get_or_create_experiment(db_session, name="exp_dup")
    db_session.commit()
    second = get_or_create_experiment(db_session, name="exp_dup")
    assert first.id == second.id


def test_deleting_experiment_cascades_through_run_to_metrics(db_session: Session) -> None:
    from app.models import Experiment

    experiment = get_or_create_experiment(db_session, name="exp_cascade")
    db_session.commit()
    persist_run(
        db=db_session, experiment=experiment, run_id="run_cascade",
        config_path="x", metrics_path="x", log_path="x", summary_path="x",
        diagnostics_path="x", status="complete",
        epoch_history=[EpochMetrics(1, 0.5, 0.5, 0.5, 0.5, 0.001, 1.0)],
    )

    db_session.delete(db_session.get(Experiment, experiment.id))
    db_session.commit()

    assert db_session.query(Run).count() == 0
    assert db_session.query(Metric).count() == 0
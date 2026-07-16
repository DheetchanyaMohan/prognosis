from pathlib import Path

import pytest
import yaml
from sqlalchemy.orm import Session

from app.config.schema import DatasetConfig, ModelConfig, RunConfig, TrainingConfig
from app.data_generation.metrics_writer import EpochMetrics
from app.data_generation.persistence import get_or_create_experiment, persist_run
from app.tools.experiment_tool import RunNotFoundError
from app.tools.metrics_tool import analyze_run, compare_runs, summarize_run


def _write_config(path: Path, run_id: str, dropout: float, lr: float, batch_size: int = 64) -> None:
    config = RunConfig(
        run_id=run_id,
        experiment_name="exp_test",
        seed=0,
        description="test run",
        dataset=DatasetConfig(train_size=1000, val_size=500, augmentation=True),
        model=ModelConfig(dropout=dropout),
        training=TrainingConfig(
            optimizer="adam", lr=lr, batch_size=batch_size, weight_decay=0.0001
        ),
    )
    path.write_text(yaml.safe_dump(config.model_dump(), sort_keys=False))


def _seed_run(
    db: Session, tmp_path: Path, run_id: str, dropout: float = 0.3, lr: float = 0.001
) -> None:
    experiment = get_or_create_experiment(db, name="exp_test")
    db.commit()

    config_path = tmp_path / f"{run_id}_config.yaml"
    _write_config(config_path, run_id, dropout=dropout, lr=lr)

    history = [
        EpochMetrics(1, 1.0, 1.2, 0.4, 0.35, lr, 1.0),
        EpochMetrics(2, 0.7, 0.6, 0.6, 0.62, lr, 1.0),
        EpochMetrics(3, 0.5, 0.9, 0.75, 0.55, lr, 1.0),
    ]
    persist_run(
        db=db, experiment=experiment, run_id=run_id,
        config_path=str(config_path), metrics_path="x", log_path="x",
        summary_path="x", diagnostics_path="x", status="complete",
        epoch_history=history,
    )


# --- analyze_run ---------------------------------------------------------


def test_analyze_run_matches_direct_analysis_layer_call(
    db_session: Session, tmp_path: Path
) -> None:
    _seed_run(db_session, tmp_path, "run_001")

    diagnostics = analyze_run("run_001", db=db_session)

    assert diagnostics.run_id == "run_001"
    assert diagnostics.total_epochs == 3
    assert diagnostics.best_epoch.epoch == 2  # lowest val_loss in the seeded history


def test_analyze_run_raises_when_missing(db_session: Session) -> None:
    with pytest.raises(RunNotFoundError):
        analyze_run("run_nonexistent", db=db_session)


# --- summarize_run ---------------------------------------------------------


def test_summarize_run_includes_config_and_diagnostics(db_session: Session, tmp_path: Path) -> None:
    _seed_run(db_session, tmp_path, "run_001", dropout=0.5, lr=0.01)

    view = summarize_run("run_001", db=db_session)

    assert view.run_id == "run_001"
    assert view.experiment_name == "exp_test"
    assert view.status == "complete"
    assert view.config.dropout == 0.5
    assert view.config.lr == 0.01
    assert view.diagnostics.best_epoch.epoch == 2


def test_summarize_run_raises_when_missing(db_session: Session) -> None:
    with pytest.raises(RunNotFoundError):
        summarize_run("run_nonexistent", db=db_session)


# --- compare_runs ---------------------------------------------------------


def test_compare_runs_detects_differing_hyperparameters(
    db_session: Session, tmp_path: Path
) -> None:
    _seed_run(db_session, tmp_path, "run_101", dropout=0.0, lr=0.001)
    _seed_run(db_session, tmp_path, "run_102", dropout=0.5, lr=0.001)

    result = compare_runs("run_101", "run_102", db=db_session)

    assert result.run_a_id == "run_101"
    assert result.run_b_id == "run_102"
    diff_fields = {d.field for d in result.config_differences}
    assert "dropout" in diff_fields
    assert "lr" not in diff_fields  # both runs used the same lr


def test_compare_runs_includes_diagnostics_for_both(db_session: Session, tmp_path: Path) -> None:
    _seed_run(db_session, tmp_path, "run_101")
    _seed_run(db_session, tmp_path, "run_102")

    result = compare_runs("run_101", "run_102", db=db_session)

    assert result.run_a_diagnostics.run_id == "run_101"
    assert result.run_b_diagnostics.run_id == "run_102"


def test_compare_runs_raises_when_either_missing(db_session: Session, tmp_path: Path) -> None:
    _seed_run(db_session, tmp_path, "run_101")
    with pytest.raises(RunNotFoundError):
        compare_runs("run_101", "run_nonexistent", db=db_session)
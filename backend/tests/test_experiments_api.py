from __future__ import annotations

import json
from pathlib import Path

import httpx
import yaml
from sqlalchemy.orm import Session

from app.config.schema import DatasetConfig, ModelConfig, RunConfig, TrainingConfig
from app.data_generation.metrics_writer import EpochMetrics
from app.data_generation.persistence import get_or_create_experiment, persist_run


def _write_config(path: Path, run_id: str) -> None:
    config = RunConfig(
        run_id=run_id,
        experiment_name="exp_test",
        seed=0,
        description="test run",
        dataset=DatasetConfig(train_size=1000, val_size=500, augmentation=True),
        model=ModelConfig(dropout=0.3),
        training=TrainingConfig(optimizer="adam", lr=0.001, batch_size=64, weight_decay=0.0001),
    )
    path.write_text(yaml.safe_dump(config.model_dump(), sort_keys=False))


def _write_summary(path: Path, run_id: str) -> None:
    path.write_text(
        json.dumps(
            {
                "run_id": run_id, "total_epochs_completed": 2, "best_epoch": 1,
                "best_val_loss": 0.6, "final_train_loss": 0.5, "final_val_loss": 0.6,
                "final_train_acc": 0.7, "final_val_acc": 0.65, "wall_clock_sec": 12.3,
                "diverged": False, "description": "test summary",
            }
        )
    )


def _write_diagnostics(path: Path, run_id: str) -> None:
    path.write_text(
        json.dumps(
            {
                "run_id": run_id, "total_epochs": 2,
                "generalization_gap": {
                    "epoch": 2, "train_loss": 0.5, "val_loss": 0.6, "loss_gap": 0.1,
                    "loss_gap_pct": 20.0, "train_acc": 0.7, "val_acc": 0.65,
                    "accuracy_gap": 0.05, "trend": "stable",
                },
                "plateau": {
                    "metric": "val_loss", "window": 5, "threshold": 0.02, "plateaued": False,
                    "plateau_start_epoch": None, "observed_range": None, "insufficient_data": True,
                },
                "instability": {
                    "metric": "train_loss", "spike_relative_threshold": 0.5,
                    "coefficient_of_variation_threshold": 0.3, "is_unstable": False,
                    "spike_epochs": [], "coefficient_of_variation": 0.01,
                },
                "best_epoch": {
                    "epoch": 1, "val_loss": 0.6, "train_loss": 0.5,
                    "val_acc": 0.65, "train_acc": 0.7,
                },
            }
        )
    )


def _seed_run(
    db: Session,
    tmp_path: Path,
    run_id: str,
    experiment_name: str = "exp_test",
    with_summary: bool = True,
    with_diagnostics: bool = True,
) -> None:
    experiment = get_or_create_experiment(db, name=experiment_name, description="a test experiment")
    db.commit()

    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    config_path = run_dir / "config.yaml"
    _write_config(config_path, run_id)

    summary_path = run_dir / "summary.json"
    if with_summary:
        _write_summary(summary_path, run_id)

    diagnostics_path = run_dir / "diagnostics.json"
    if with_diagnostics:
        _write_diagnostics(diagnostics_path, run_id)

    persist_run(
        db=db, experiment=experiment, run_id=run_id,
        config_path=str(config_path), metrics_path="x", log_path="x",
        summary_path=str(summary_path), diagnostics_path=str(diagnostics_path),
        status="complete",
        epoch_history=[
            EpochMetrics(1, 0.6, 0.7, 0.65, 0.6, 0.001, 1.0),
            EpochMetrics(2, 0.5, 0.6, 0.7, 0.65, 0.001, 1.0),
        ],
    )


# --- GET /api/v1/experiments -------------------------------------------


async def test_list_experiments_empty(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/api/v1/experiments")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_experiments_returns_seeded_experiment(
    api_client: httpx.AsyncClient, db_session: Session, tmp_path: Path
) -> None:
    _seed_run(db_session, tmp_path, "run_001", experiment_name="exp_alpha")

    response = await api_client.get("/api/v1/experiments")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["experiment_name"] == "exp_alpha"
    assert body[0]["run_ids"] == ["run_001"]


# --- GET /api/v1/experiments/{experiment_id} -------------------------------


async def test_get_experiment_returns_details(
    api_client: httpx.AsyncClient, db_session: Session, tmp_path: Path
) -> None:
    _seed_run(db_session, tmp_path, "run_001", experiment_name="exp_alpha")

    response = await api_client.get("/api/v1/experiments/exp_alpha")

    assert response.status_code == 200
    body = response.json()
    assert body["experiment_name"] == "exp_alpha"
    assert body["description"] == "a test experiment"


async def test_get_experiment_404_when_missing(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/api/v1/experiments/does_not_exist")
    assert response.status_code == 404
    assert "does_not_exist" in response.json()["detail"]


# --- GET /api/v1/runs/{run_id} -----------------------------------------


async def test_get_run_detail_full(
    api_client: httpx.AsyncClient, db_session: Session, tmp_path: Path
) -> None:
    _seed_run(db_session, tmp_path, "run_001")

    response = await api_client.get("/api/v1/runs/run_001")

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == "run_001"
    assert body["config"]["dataset"]["train_size"] == 1000
    assert body["summary"]["best_epoch"] == 1
    assert body["diagnostics"]["generalization_gap"]["trend"] == "stable"


async def test_get_run_detail_404_when_missing(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/api/v1/runs/does_not_exist")
    assert response.status_code == 404
    assert "does_not_exist" in response.json()["detail"]


async def test_get_run_detail_null_summary_and_diagnostics_when_not_yet_generated(
    api_client: httpx.AsyncClient, db_session: Session, tmp_path: Path
) -> None:
    _seed_run(db_session, tmp_path, "run_002", with_summary=False, with_diagnostics=False)

    response = await api_client.get("/api/v1/runs/run_002")

    assert response.status_code == 200
    body = response.json()
    assert body["summary"] is None
    assert body["diagnostics"] is None
    assert body["config"] is not None  # config always present


async def test_get_run_detail_partial_when_only_summary_exists(
    api_client: httpx.AsyncClient, db_session: Session, tmp_path: Path
) -> None:
    _seed_run(db_session, tmp_path, "run_003", with_summary=True, with_diagnostics=False)

    response = await api_client.get("/api/v1/runs/run_003")

    assert response.status_code == 200
    body = response.json()
    assert body["summary"] is not None
    assert body["diagnostics"] is None
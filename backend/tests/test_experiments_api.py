from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
import yaml
from sqlalchemy.orm import Session

from app.config.schema import DatasetConfig, ModelConfig, RunConfig, TrainingConfig
from app.core.config import get_settings
from app.data_generation.metrics_writer import EpochMetrics
from app.data_generation.persistence import get_or_create_experiment, persist_run
from app.tools import run_paths


@pytest.fixture(autouse=True)
def _data_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """The run-detail and comparison routes resolve config.yaml's
    location via run_paths, which depends on settings.data_root — point
    it at tmp_path for the duration of each test, matching where
    _seed_run below actually writes files."""
    get_settings.cache_clear()
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    yield
    get_settings.cache_clear()


def _write_config(path: Path, run_id: str, experiment_name: str, dropout: float = 0.3) -> None:
    config = RunConfig(
        run_id=run_id,
        experiment_name=experiment_name,
        seed=0,
        description="test run",
        dataset=DatasetConfig(train_size=1000, val_size=500, augmentation=True),
        model=ModelConfig(dropout=dropout),
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
    run_id: str,
    experiment_name: str = "exp_test",
    with_summary: bool = True,
    with_diagnostics: bool = True,
    dropout: float = 0.3,
) -> None:
    experiment = get_or_create_experiment(db, name=experiment_name, description="a test experiment")
    db.commit()

    run_dir = run_paths.run_directory(experiment_name, run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_config(run_dir / "config.yaml", run_id, experiment_name, dropout=dropout)

    if with_summary:
        _write_summary(run_dir / "summary.json", run_id)
    if with_diagnostics:
        _write_diagnostics(run_dir / "diagnostics.json", run_id)

    persist_run(
        db=db, experiment=experiment, run_id=run_id, status="complete",
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
    api_client: httpx.AsyncClient, db_session: Session
) -> None:
    _seed_run(db_session, "run_001", experiment_name="exp_alpha")

    response = await api_client.get("/api/v1/experiments")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["experiment_name"] == "exp_alpha"
    assert body[0]["run_ids"] == ["run_001"]


# --- GET /api/v1/experiments/{experiment_id} -------------------------------


async def test_get_experiment_returns_details(
    api_client: httpx.AsyncClient, db_session: Session
) -> None:
    _seed_run(db_session, "run_001", experiment_name="exp_alpha")

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


async def test_get_run_detail_full(api_client: httpx.AsyncClient, db_session: Session) -> None:
    _seed_run(db_session, "run_001")

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
    api_client: httpx.AsyncClient, db_session: Session
) -> None:
    _seed_run(db_session, "run_002", with_summary=False, with_diagnostics=False)

    response = await api_client.get("/api/v1/runs/run_002")

    assert response.status_code == 200
    body = response.json()
    assert body["summary"] is None
    assert body["diagnostics"] is None
    assert body["config"] is not None  # config always present


async def test_get_run_detail_partial_when_only_summary_exists(
    api_client: httpx.AsyncClient, db_session: Session
) -> None:
    _seed_run(db_session, "run_003", with_summary=True, with_diagnostics=False)

    response = await api_client.get("/api/v1/runs/run_003")

    assert response.status_code == 200
    body = response.json()
    assert body["summary"] is not None
    assert body["diagnostics"] is None


# --- GET /api/v1/runs/{run_a_id}/compare/{run_b_id} -----------------------


async def test_compare_runs_returns_config_differences(
    api_client: httpx.AsyncClient, db_session: Session
) -> None:
    _seed_run(db_session, "run_101", dropout=0.0)
    _seed_run(db_session, "run_102", dropout=0.5)

    response = await api_client.get("/api/v1/runs/run_101/compare/run_102")

    assert response.status_code == 200
    body = response.json()
    assert body["run_a_id"] == "run_101"
    assert body["run_b_id"] == "run_102"
    diff_fields = {d["field"] for d in body["config_differences"]}
    assert "dropout" in diff_fields


async def test_compare_runs_includes_diagnostics_for_both_runs(
    api_client: httpx.AsyncClient, db_session: Session
) -> None:
    _seed_run(db_session, "run_101")
    _seed_run(db_session, "run_102")

    response = await api_client.get("/api/v1/runs/run_101/compare/run_102")

    assert response.status_code == 200
    body = response.json()
    assert body["run_a_diagnostics"]["run_id"] == "run_101"
    assert body["run_b_diagnostics"]["run_id"] == "run_102"


async def test_compare_runs_404_when_first_run_missing(
    api_client: httpx.AsyncClient, db_session: Session
) -> None:
    _seed_run(db_session, "run_102")

    response = await api_client.get("/api/v1/runs/does_not_exist/compare/run_102")

    assert response.status_code == 404
    assert "does_not_exist" in response.json()["detail"]


async def test_compare_runs_404_when_second_run_missing(
    api_client: httpx.AsyncClient, db_session: Session
) -> None:
    _seed_run(db_session, "run_101")

    response = await api_client.get("/api/v1/runs/run_101/compare/does_not_exist")

    assert response.status_code == 404
    assert "does_not_exist" in response.json()["detail"]


async def test_compare_runs_registered_in_openapi(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/openapi.json")
    schema = response.json()

    path_item = schema["paths"].get("/api/v1/runs/{run_a_id}/compare/{run_b_id}")
    assert path_item is not None
    assert "get" in path_item
    response_schema = path_item["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert response_schema["$ref"].endswith("RunComparisonResult")
import json
from pathlib import Path

import pytest

from app.data_generation.metrics_writer import EpochMetrics
from app.data_generation.summary import build_summary, write_summary


def test_build_summary_picks_best_epoch_by_val_loss() -> None:
    history = [
        EpochMetrics(1, 1.0, 1.2, 0.40, 0.35, 0.001, 1.0),
        EpochMetrics(2, 0.7, 0.6, 0.60, 0.62, 0.001, 1.0),  # best val_loss
        EpochMetrics(3, 0.5, 0.9, 0.75, 0.55, 0.001, 1.0),  # val_loss regressed again
    ]
    summary = build_summary("run_test", history, wall_clock_sec=10.0, diverged=False)

    assert summary.best_epoch == 2
    assert summary.best_val_loss == 0.6
    assert summary.total_epochs_completed == 3
    assert summary.final_val_loss == 0.9
    assert not summary.diverged
    assert "run_test" in summary.description


def test_build_summary_rejects_empty_history() -> None:
    with pytest.raises(ValueError):
        build_summary("run_empty", [], wall_clock_sec=0.0, diverged=False)


def test_diverged_summary_reflects_status_in_description() -> None:
    history = [EpochMetrics(1, 50.0, 60.0, 0.1, 0.1, 0.1, 1.0)]
    summary = build_summary("run_bad", history, wall_clock_sec=1.0, diverged=True)
    assert summary.diverged
    assert "diverged" in summary.description


def test_write_summary_produces_valid_json(tmp_path: Path) -> None:
    history = [EpochMetrics(1, 0.5, 0.6, 0.7, 0.65, 0.001, 1.0)]
    summary = build_summary("run_json", history, wall_clock_sec=2.0, diverged=False)
    path = tmp_path / "summary.json"
    write_summary(summary, path)

    with path.open() as f:
        loaded = json.load(f)
    assert loaded["run_id"] == "run_json"
    assert loaded["best_epoch"] == 1
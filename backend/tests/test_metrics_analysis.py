import json
from pathlib import Path

import pytest

from app.data_generation.metrics_writer import EpochMetrics
from app.models import Metric
from app.tools.metrics_analysis import (
    compute_generalization_gap,
    detect_instability,
    detect_plateau,
    epoch_history_from_metric_rows,
    load_diagnostics,
    select_best_epoch,
    summarize_run,
    write_diagnostics,
)


def _m(
    epoch: int, train_loss: float, val_loss: float,
    train_acc: float = 0.5, val_acc: float = 0.5,
) -> EpochMetrics:
    return EpochMetrics(
        epoch=epoch, train_loss=train_loss, val_loss=val_loss,
        train_acc=train_acc, val_acc=val_acc, lr=0.001, epoch_time_sec=1.0,
    )


# --- compute_generalization_gap ------------------------------------------


def test_gap_basic_values() -> None:
    history = [_m(1, 1.0, 1.2, train_acc=0.6, val_acc=0.5)]
    result = compute_generalization_gap(history)
    assert result.loss_gap == pytest.approx(0.2)
    assert result.loss_gap_pct == pytest.approx(20.0)
    assert result.accuracy_gap == pytest.approx(0.1)
    assert result.trend == "stable"  # only 1 epoch: not enough data for a trend


def test_gap_zero_train_loss_does_not_crash() -> None:
    result = compute_generalization_gap([_m(1, 0.0, 0.5)])
    assert result.loss_gap_pct == 0.0


def test_gap_trend_widening() -> None:
    # gap grows from ~0.1 to ~0.6 across 6 epochs
    history = [
        _m(1, 1.0, 1.1), _m(2, 0.9, 1.0), _m(3, 0.8, 0.95),
        _m(4, 0.7, 1.1), _m(5, 0.6, 1.15), _m(6, 0.5, 1.2),
    ]
    result = compute_generalization_gap(history)
    assert result.trend == "widening"


def test_gap_trend_narrowing() -> None:
    history = [
        _m(1, 0.5, 1.2), _m(2, 0.6, 1.15), _m(3, 0.7, 1.1),
        _m(4, 0.8, 0.95), _m(5, 0.9, 1.0), _m(6, 1.0, 1.05),
    ]
    result = compute_generalization_gap(history)
    assert result.trend == "narrowing"


def test_gap_rejects_empty_history() -> None:
    with pytest.raises(ValueError):
        compute_generalization_gap([])


# --- detect_plateau --------------------------------------------------------


def test_plateau_detected_on_flat_tail() -> None:
    history = [_m(1, 1.0, 2.0), _m(2, 0.8, 1.0), _m(3, 0.6, 0.5)]
    history += [_m(e, 0.5, 0.301) for e in (4, 5, 6, 7, 8)]  # 5 flat epochs = the window
    result = detect_plateau(history, metric="val_loss", window=5, range_threshold=0.02)
    assert result.plateaued is True
    assert result.observed_range is not None
    assert result.observed_range <= 0.02
    assert result.plateau_start_epoch is not None


def test_plateau_not_detected_while_still_decreasing() -> None:
    history = [_m(e, 1.0, 2.0 / e) for e in range(1, 8)]  # steadily decreasing
    result = detect_plateau(history, metric="val_loss", window=5, range_threshold=0.02)
    assert result.plateaued is False


def test_plateau_insufficient_data() -> None:
    history = [_m(1, 1.0, 1.0), _m(2, 0.9, 0.9)]
    result = detect_plateau(history, window=5)
    assert result.insufficient_data is True
    assert result.plateaued is False
    assert result.observed_range is None


def test_plateau_rejects_empty_history() -> None:
    with pytest.raises(ValueError):
        detect_plateau([])


# --- detect_instability -----------------------------------------------------


def test_instability_detects_spike() -> None:
    history = [_m(1, 1.0, 1.0), _m(2, 1.05, 1.0), _m(3, 3.0, 1.0), _m(4, 1.1, 1.0)]
    result = detect_instability(history, metric="train_loss", spike_relative_threshold=0.5)
    assert result.is_unstable is True
    assert 3 in result.spike_epochs


def test_instability_stable_sequence_not_flagged() -> None:
    history = [_m(e, 1.0 - e * 0.01, 1.0) for e in range(1, 8)]
    result = detect_instability(history, metric="train_loss")
    assert result.is_unstable is False
    assert result.spike_epochs == []


def test_instability_high_variance_without_single_spike() -> None:
    # Oscillates enough to exceed the CV threshold, but no single jump
    # exceeds the 50% spike threshold.
    values = [1.0, 1.4, 1.0, 1.4, 1.0, 1.4, 1.0]
    history = [_m(i + 1, v, 1.0) for i, v in enumerate(values)]
    result = detect_instability(history, metric="train_loss", cv_threshold=0.1)
    assert result.is_unstable is True
    assert result.coefficient_of_variation > 0.1


def test_instability_rejects_empty_history() -> None:
    with pytest.raises(ValueError):
        detect_instability([])


# --- select_best_epoch -------------------------------------------------------


def test_best_epoch_picks_lowest_val_loss() -> None:
    history = [_m(1, 1.0, 1.2), _m(2, 0.7, 0.6), _m(3, 0.5, 0.9)]
    result = select_best_epoch(history)
    assert result.epoch == 2
    assert result.val_loss == 0.6


def test_best_epoch_ties_broken_by_earliest() -> None:
    history = [_m(1, 1.0, 0.5), _m(2, 0.9, 0.5), _m(3, 0.8, 0.6)]
    result = select_best_epoch(history)
    assert result.epoch == 1


def test_best_epoch_rejects_empty_history() -> None:
    with pytest.raises(ValueError):
        select_best_epoch([])


# --- summarize_run / diagnostics.json --------------------------------------


def test_summarize_run_bundles_all_analyses() -> None:
    history = [_m(1, 1.0, 1.2), _m(2, 0.7, 0.6), _m(3, 0.5, 0.9)]
    diagnostics = summarize_run("run_test", history)
    assert diagnostics.run_id == "run_test"
    assert diagnostics.total_epochs == 3
    assert diagnostics.best_epoch.epoch == 2
    assert diagnostics.generalization_gap.epoch == 3


def test_write_and_load_diagnostics_roundtrip(tmp_path: Path) -> None:
    history = [_m(1, 1.0, 1.2), _m(2, 0.7, 0.6)]
    diagnostics = summarize_run("run_roundtrip", history)
    path = tmp_path / "diagnostics.json"

    write_diagnostics(diagnostics, path)
    with path.open() as f:
        raw = json.load(f)
    assert raw["run_id"] == "run_roundtrip"

    loaded = load_diagnostics(path)
    assert loaded == diagnostics


# --- ORM bridge --------------------------------------------------------------


def test_epoch_history_from_metric_rows_sorts_and_filters_nulls() -> None:
    rows = [
        Metric(
            epoch=2, train_loss=0.5, val_loss=0.6, train_acc=0.7,
            val_acc=0.6, lr=0.001, epoch_time_sec=1.0,
        ),
        Metric(
            epoch=1, train_loss=0.9, val_loss=1.0, train_acc=0.4,
            val_acc=0.3, lr=0.001, epoch_time_sec=1.0,
        ),
        Metric(
            epoch=3, train_loss=None, val_loss=0.4, train_acc=0.8,
            val_acc=0.7, lr=0.001, epoch_time_sec=1.0,
        ),
    ]
    history = epoch_history_from_metric_rows(rows)
    # epoch 3 dropped (null train_loss), remaining sorted ascending
    assert [m.epoch for m in history] == [1, 2]
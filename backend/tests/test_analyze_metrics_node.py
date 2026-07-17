from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.agent.nodes import analyze_metrics as analyze_metrics_module
from app.agent.state import AgentState
from app.tools.experiment_tool import RunNotFoundError
from app.tools.schemas import (
    BestEpochResult,
    ConfigDiffEntry,
    GeneralizationGapResult,
    InstabilityResult,
    PlateauResult,
    RunComparisonResult,
    RunConfigSummary,
    RunDiagnostics,
    RunSummaryView,
)


def _diagnostics(run_id: str, trend: str = "widening") -> RunDiagnostics:
    return RunDiagnostics(
        run_id=run_id,
        total_epochs=20,
        generalization_gap=GeneralizationGapResult(
            epoch=20, train_loss=0.1, val_loss=0.6, loss_gap=0.5, loss_gap_pct=500.0,
            train_acc=0.95, val_acc=0.6, accuracy_gap=0.35, trend=trend,  # type: ignore[arg-type]
        ),
        plateau=PlateauResult(
            metric="val_loss", window=5, threshold=0.02, plateaued=False,
            plateau_start_epoch=None, observed_range=0.1, insufficient_data=False,
        ),
        instability=InstabilityResult(
            metric="train_loss", spike_relative_threshold=0.5,
            coefficient_of_variation_threshold=0.3, is_unstable=False,
            spike_epochs=[], coefficient_of_variation=0.05,
        ),
        best_epoch=BestEpochResult(
            epoch=15, val_loss=0.55, train_loss=0.15, val_acc=0.62, train_acc=0.93
        ),
    )


def _run_summary(run_id: str) -> RunSummaryView:
    return RunSummaryView(
        run_id=run_id, experiment_name="exp_test", status="complete",
        created_at=datetime.now(UTC),
        config=RunConfigSummary(
            train_size=1500, val_size=1000, augmentation=False, dropout=0.0,
            optimizer="adam", lr=0.001, lr_scheduler="cosine", batch_size=64,
            weight_decay=0.0, epochs=20,
        ),
        diagnostics=_diagnostics(run_id),
    )


def _comparison(run_a: str, run_b: str) -> RunComparisonResult:
    return RunComparisonResult(
        run_a_id=run_a, run_b_id=run_b,
        run_a_diagnostics=_diagnostics(run_a),
        run_b_diagnostics=_diagnostics(run_b, trend="stable"),
        config_differences=[ConfigDiffEntry(field="dropout", run_a_value=0.0, run_b_value=0.5)],
    )


# --- diagnose_run ---------------------------------------------------------


def test_diagnose_run_calls_summarize_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        analyze_metrics_module.metrics_tool, "summarize_run",
        lambda run_id, db=None: _run_summary(run_id),
    )
    state: AgentState = {"request_type": "diagnose_run", "selected_run": "run_005"}

    result = analyze_metrics_module.analyze_metrics_node(state)

    assert result["run_summary"].run_id == "run_005"
    assert result["diagnostics"].run_id == "run_005"
    assert result["comparison"] is None
    assert "metrics_tool.summarize_run" in result["trace"][0].tools_called


def test_diagnose_run_missing_run_handled_gracefully(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_not_found(run_id: str, db: object = None) -> RunSummaryView:
        raise RunNotFoundError(f"No run found with run_id={run_id!r}")

    monkeypatch.setattr(analyze_metrics_module.metrics_tool, "summarize_run", raise_not_found)
    state: AgentState = {"request_type": "diagnose_run", "selected_run": "run_999"}

    result = analyze_metrics_module.analyze_metrics_node(state)

    assert result["diagnostics"] is None
    assert "run_999" in result["trace"][0].reasoning


def test_diagnose_run_no_completed_epochs_handled_gracefully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_value_error(run_id: str, db: object = None) -> RunSummaryView:
        raise ValueError("epoch_history must contain at least one epoch")

    monkeypatch.setattr(analyze_metrics_module.metrics_tool, "summarize_run", raise_value_error)
    state: AgentState = {"request_type": "diagnose_run", "selected_run": "run_010"}

    result = analyze_metrics_module.analyze_metrics_node(state)

    assert result["diagnostics"] is None
    assert "run_010" in result["trace"][0].reasoning


# --- compare_runs -----------------------------------------------------


def test_compare_runs_calls_compare_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        analyze_metrics_module.metrics_tool, "compare_runs",
        lambda a, b, db=None: _comparison(a, b),
    )
    state: AgentState = {
        "request_type": "compare_runs", "selected_run": "run_001", "comparison_run": "run_002",
    }

    result = analyze_metrics_module.analyze_metrics_node(state)

    assert result["comparison"].run_a_id == "run_001"
    assert result["diagnostics"].run_id == "run_001"  # derived from comparison.run_a_diagnostics
    assert "metrics_tool.compare_runs" in result["trace"][0].tools_called
    assert "dropout" in result["trace"][0].reasoning


def test_compare_runs_missing_run_handled_gracefully(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_not_found(a: str, b: str, db: object = None) -> RunComparisonResult:
        raise RunNotFoundError(f"No run found with run_id={b!r}")

    monkeypatch.setattr(analyze_metrics_module.metrics_tool, "compare_runs", raise_not_found)
    state: AgentState = {
        "request_type": "compare_runs", "selected_run": "run_001", "comparison_run": "run_999",
    }

    result = analyze_metrics_module.analyze_metrics_node(state)

    assert result["comparison"] is None
    assert result["diagnostics"] is None


# --- general_question / defensive fallbacks --------------------------------


def test_general_question_calls_no_tools() -> None:
    state: AgentState = {"request_type": "general_question"}
    result = analyze_metrics_module.analyze_metrics_node(state)

    assert result["diagnostics"] is None
    assert result["run_summary"] is None
    assert result["comparison"] is None
    assert result["trace"][0].tools_called == []


def test_compare_runs_with_missing_comparison_run_skips_analysis() -> None:
    state: AgentState = {"request_type": "compare_runs", "selected_run": "run_001"}
    result = analyze_metrics_module.analyze_metrics_node(state)

    assert result["comparison"] is None
    assert result["trace"][0].tools_called == []
    assert "no run was resolved" in result["trace"][0].reasoning
"""Deterministic analysis layer.

Independent of LangGraph, RAG, FastAPI, and any LLM. Shared by the
training pipeline (diagnostics.json), future agent tools, the evaluation
framework, and the frontend dashboard.
"""

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
from app.tools.schemas import (
    BestEpochResult,
    GeneralizationGapResult,
    InstabilityResult,
    PlateauResult,
    RunDiagnostics,
)

__all__ = [
    "compute_generalization_gap",
    "detect_plateau",
    "detect_instability",
    "select_best_epoch",
    "summarize_run",
    "write_diagnostics",
    "load_diagnostics",
    "epoch_history_from_metric_rows",
    "GeneralizationGapResult",
    "PlateauResult",
    "InstabilityResult",
    "BestEpochResult",
    "RunDiagnostics",
]
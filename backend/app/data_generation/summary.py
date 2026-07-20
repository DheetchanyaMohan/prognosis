"""summary.json generation.

This is a human/LLM-readable end-of-run summary — not the deterministic
diagnostics file (that's the next phase: app/tools/metrics_analysis.py +
diagnostics.json). summary.json's `description` field is written in plain
prose specifically because it later doubles as the text embedded for the
run_summaries RAG collection.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.data_generation.metrics_writer import EpochMetrics


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    total_epochs_completed: int
    best_epoch: int
    best_val_loss: float
    final_train_loss: float
    final_val_loss: float
    final_train_acc: float
    final_val_acc: float
    wall_clock_sec: float
    diverged: bool
    description: str


def build_summary(
    run_id: str,
    epoch_history: list[EpochMetrics],
    wall_clock_sec: float,
    diverged: bool,
) -> RunSummary:
    if not epoch_history:
        raise ValueError("Cannot build a summary from an empty epoch history")

    best = min(epoch_history, key=lambda m: m.val_loss)
    final = epoch_history[-1]

    status = (
        "diverged before completing the planned epoch budget"
        if diverged
        else "completed its full epoch budget"
    )
    description = (
        f"Run {run_id} {status}, finishing after {len(epoch_history)} epoch(s). "
        f"Best validation loss was {best.val_loss:.4f} at epoch {best.epoch}. "
        f"Final train/val loss: {final.train_loss:.4f}/{final.val_loss:.4f}, "
        f"final train/val accuracy: {final.train_acc:.4f}/{final.val_acc:.4f}."
    )

    return RunSummary(
        run_id=run_id,
        total_epochs_completed=len(epoch_history),
        best_epoch=best.epoch,
        best_val_loss=best.val_loss,
        final_train_loss=final.train_loss,
        final_val_loss=final.val_loss,
        final_train_acc=final.train_acc,
        final_val_acc=final.val_acc,
        wall_clock_sec=wall_clock_sec,
        diverged=diverged,
        description=description,
    )


def write_summary(summary: RunSummary, path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(summary), f, indent=2)
        f.write("\n")
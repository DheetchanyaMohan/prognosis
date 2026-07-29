"""Helpers for locating experiment artifacts on disk."""

from __future__ import annotations

from pathlib import Path

from app.models.run import Run
from app.tools.schemas import RunArtifactPaths


DATA_DIR = Path("data")


def get_run_artifact_paths(run: Run) -> RunArtifactPaths:
    """Build artifact paths dynamically instead of reading absolute paths
    stored in the database.
    """

    run_dir = (
        DATA_DIR
        / "experiments"
        / run.experiment.name
        / "runs"
        / run.run_name
    )

    return RunArtifactPaths(
        run_id=run.run_name,
        config_path=str(run_dir / "config.yaml"),
        metrics_path=str(run_dir / "metrics.csv"),
        log_path=str(run_dir / "training.log"),
        summary_path=str(run_dir / "summary.json"),
        diagnostics_path=str(run_dir / "diagnostics.json"),
    )
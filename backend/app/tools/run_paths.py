"""Single source of truth for where a run's artifact files live on disk.

No path is ever persisted in the database — every path is derived
fresh, in the current process, from (experiment_name, run_name) plus
settings.data_root. This is what makes artifact paths portable across
Windows, Linux, Docker, and Railway: the same two logical identifiers
resolve correctly on whatever machine is currently running the code,
instead of a path baked in on whichever machine originally created the
run.

Phase 1 of the path-portability refactor: this module now owns path
construction, but the ORM's path columns still exist and are simply
left unwritten/unread — see app/models/run.py for the removal, planned
as a separate migration-bearing change.
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.tools.schemas import RunArtifactPaths


def run_directory(experiment_name: str, run_name: str) -> Path:
    """The directory containing one run's artifacts."""
    return get_settings().data_root / "experiments" / experiment_name / "runs" / run_name


def build_run_artifact_paths(experiment_name: str, run_name: str) -> RunArtifactPaths:
    """The one function every layer should call instead of reading a
    stored path column."""
    run_dir = run_directory(experiment_name, run_name)
    return RunArtifactPaths(
        run_id=run_name,
        config_path=str(run_dir / "config.yaml"),
        metrics_path=str(run_dir / "metrics.csv"),
        log_path=str(run_dir / "training.log"),
        summary_path=str(run_dir / "summary.json"),
        diagnostics_path=str(run_dir / "diagnostics.json"),
    )


def confusion_matrix_path(experiment_name: str, run_name: str) -> Path:
    return run_directory(experiment_name, run_name) / "artifacts" / "confusion_matrix.png"
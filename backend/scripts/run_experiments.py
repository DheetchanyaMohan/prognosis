"""Executes one or all planned runs end-to-end.

Usage:
    python scripts/run_experiments.py run_001
    python scripts/run_experiments.py --all
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.config.loader import load_and_validate, load_run_config
from app.data_generation.run_experiment import execute_run
from app.db.session import SessionLocal
from app.tools import run_paths

EXPERIMENT_NAME = "exp_001_cifar10_subset_study"


def _config_path_for(run_id: str) -> Path:
    # config.yaml scaffolding still lives under the same convention;
    # only the *persisted* paths are gone, not the on-disk layout itself.
    return run_paths.run_directory(EXPERIMENT_NAME, run_id) / "config.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id", nargs="?", help="e.g. run_001")
    parser.add_argument("--all", action="store_true", help="run every config under runs root")
    args = parser.parse_args()

    if not args.all and not args.run_id:
        parser.error("provide a run_id or pass --all")

    if args.all:
        runs_root = run_paths.run_directory(EXPERIMENT_NAME, "").parent
        configs = load_and_validate(runs_root)
    else:
        config_path = _config_path_for(args.run_id)
        if not config_path.exists():
            sys.exit(f"No config found at {config_path}")
        configs = [load_run_config(config_path)]

    for config in configs:
        db = SessionLocal()
        try:
            print(f"Running {config.run_id}...")
            execute_run(config, db)
            print(f"  done -> {run_paths.run_directory(config.experiment_name, config.run_id)}")
        finally:
            db.close()


if __name__ == "__main__":
    main()
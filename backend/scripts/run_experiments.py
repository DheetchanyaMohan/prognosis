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

BACKEND_ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_NAME = "exp_001_cifar10_subset_study"
RUNS_ROOT = BACKEND_ROOT / "data" / "experiments" / EXPERIMENT_NAME / "runs"


def _run_dir_for(run_id: str) -> Path:
    return RUNS_ROOT / run_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id", nargs="?", help="e.g. run_001")
    parser.add_argument("--all", action="store_true", help="run every config under runs root")
    args = parser.parse_args()

    if not args.all and not args.run_id:
        parser.error("provide a run_id or pass --all")

    if args.all:
        configs = load_and_validate(RUNS_ROOT)  # fails loudly before any run starts
    else:
        config_path = _run_dir_for(args.run_id) / "config.yaml"
        if not config_path.exists():
            sys.exit(f"No config found at {config_path}")
        configs = [load_run_config(config_path)]

    for config in configs:
        run_dir = _run_dir_for(config.run_id)
        db = SessionLocal()
        try:
            print(f"Running {config.run_id}...")
            execute_run(config, run_dir, db)
            print(f"  done -> {run_dir}")
        finally:
            db.close()


if __name__ == "__main__":
    main()
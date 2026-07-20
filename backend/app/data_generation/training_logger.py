"""Structured per-run training logger.

Writes plain-text, timestamped lines to training.log — separate from the
application's root logger (app.core.logging) so each run's log is
self-contained and portable alongside its config.yaml / metrics.csv.
"""

from __future__ import annotations

import logging
from pathlib import Path


def build_run_logger(run_id: str, log_path: Path) -> logging.Logger:
    logger = logging.getLogger(f"run.{run_id}")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # keep run logs out of the app's root handler

    logger.handlers.clear()  # idempotent if called twice for the same run_id

    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    )
    logger.addHandler(handler)
    return logger
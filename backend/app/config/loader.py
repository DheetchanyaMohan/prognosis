"""YAML loading and validation for run configs.

`load_and_validate` is what the future training pipeline calls first,
before touching PyTorch — a bad config fails here, not mid-run.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

from app.config.schema import RunConfig


class ConfigValidationError(Exception):
    """Raised when one or more run configs fail validation as a set."""


def load_run_config(path: Path) -> RunConfig:
    """Load and validate a single config.yaml file."""
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return RunConfig.model_validate(raw)


def load_all_run_configs(runs_root: Path) -> list[RunConfig]:
    """Load every config.yaml found under runs_root/run_*/config.yaml, sorted by path."""
    config_paths = sorted(runs_root.glob("run_*/config.yaml"))
    return [load_run_config(p) for p in config_paths]


def validate_run_configs(configs: list[RunConfig]) -> None:
    """Validate properties of the config *set*, beyond per-file schema checks.

    Currently: run_id uniqueness. Individual field-level validation already
    happened inside RunConfig itself when each file was loaded.
    """
    ids = [c.run_id for c in configs]
    duplicates = sorted({run_id for run_id, count in Counter(ids).items() if count > 1})
    if duplicates:
        raise ConfigValidationError(f"Duplicate run_id(s) found across config set: {duplicates}")


def load_and_validate(runs_root: Path) -> list[RunConfig]:
    """Load every run config under runs_root and validate the set. Raises on any problem."""
    configs = load_all_run_configs(runs_root)
    validate_run_configs(configs)
    return configs

"""Generates the 15 planned run configs, their folder scaffolding, and the
eval-only ground-truth labels — all from one internal spec list (RUN_SPECS
below), so the mapping between a run and its known pathology can never
drift from what was actually configured.

The `pathology` field on each spec is internal to this script only. It is
never written into config.yaml — only into data/eval/ground_truth/, which
nothing in the training/agent/RAG path ever reads.

Run as:
    python scripts/generate_experiment_plan.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from app.config.loader import load_and_validate
from app.config.schema import DatasetConfig, ModelConfig, RunConfig, TrainingConfig

BACKEND_ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_NAME = "exp_001_cifar10_subset_study"
RUNS_ROOT = BACKEND_ROOT / "data" / "experiments" / EXPERIMENT_NAME / "runs"
GROUND_TRUTH_ROOT = BACKEND_ROOT / "data" / "eval" / "ground_truth"


@dataclass
class _RunSpec:
    run_id: str
    pathology: str  # internal only — never written to config.yaml
    description: str
    seed: int
    dataset: DatasetConfig
    model: ModelConfig
    training: TrainingConfig


def _training(**overrides: object) -> TrainingConfig:
    defaults: dict[str, object] = dict(
        optimizer="adam", lr=1e-3, lr_scheduler="cosine", batch_size=64,
        weight_decay=1e-4, epochs=20,
    )
    defaults.update(overrides)
    return TrainingConfig(**defaults)


def _dataset(**overrides: object) -> DatasetConfig:
    defaults: dict[str, object] = dict(train_size=5000, val_size=1000, augmentation=True)
    defaults.update(overrides)
    return DatasetConfig(**defaults)


RUN_SPECS: list[_RunSpec] = [
    _RunSpec("run_001", "healthy", "Baseline healthy run, seed 0", 0,
             _dataset(), ModelConfig(dropout=0.3), _training()),
    _RunSpec("run_002", "healthy", "Baseline healthy run, seed 1", 1,
             _dataset(), ModelConfig(dropout=0.3), _training()),
    _RunSpec("run_003", "healthy", "Baseline healthy run, seed 2", 2,
             _dataset(), ModelConfig(dropout=0.3), _training()),

    _RunSpec("run_004", "overfitting", "Mild overfitting: smaller subset, light regularization", 0,
             _dataset(train_size=3000), ModelConfig(dropout=0.1), _training(weight_decay=0.0)),
    _RunSpec("run_005", "overfitting",
             "Severe overfitting: small subset, no regularization, no augmentation", 0,
             _dataset(train_size=1500, augmentation=False), ModelConfig(dropout=0.0),
             _training(weight_decay=0.0)),
    _RunSpec("run_006", "overfitting", "Severe overfitting, alternate seed", 1,
             _dataset(train_size=1500, augmentation=False), ModelConfig(dropout=0.0),
             _training(weight_decay=0.0)),

    _RunSpec("run_007", "underfitting", "Mild underfitting: high dropout and weight decay", 0,
             _dataset(), ModelConfig(dropout=0.5), _training(lr=3e-4, weight_decay=1e-3)),
    _RunSpec("run_008", "underfitting",
             "Severe underfitting: very high dropout, weight decay, low lr", 0,
             _dataset(), ModelConfig(dropout=0.65), _training(lr=1e-4, weight_decay=1e-2)),

    _RunSpec("run_009", "lr_too_high", "Moderate LR-too-high instability", 0,
             _dataset(), ModelConfig(dropout=0.3), _training(lr=0.05, lr_scheduler="none")),
    _RunSpec("run_010", "lr_too_high", "Severe LR-too-high, likely divergence", 0,
             _dataset(), ModelConfig(dropout=0.3), _training(lr=0.1, lr_scheduler="none")),

    _RunSpec("run_011", "lr_too_low", "Moderate plateau from an overly small LR", 0,
             _dataset(), ModelConfig(dropout=0.3), _training(lr=5e-5, lr_scheduler="none")),
    _RunSpec("run_012", "lr_too_low", "Severe plateau, LR far too small to make progress", 0,
             _dataset(), ModelConfig(dropout=0.3), _training(lr=1e-5, lr_scheduler="none")),

    _RunSpec("run_013", "loss_spikes",
             "Moderate instability: high lr, small batch, no grad clipping", 0,
             _dataset(), ModelConfig(dropout=0.3),
             _training(lr=0.03, batch_size=8, lr_scheduler="none")),
    _RunSpec("run_014", "loss_spikes", "Severe instability, smaller batch still", 0,
             _dataset(), ModelConfig(dropout=0.3),
             _training(lr=0.05, batch_size=4, lr_scheduler="none")),

    _RunSpec("run_015", "healthy",
             "Healthy baseline with one changed hyperparameter (batch size) — "
             "for testing config-diff and similarity tools against run_001", 0,
             _dataset(), ModelConfig(dropout=0.3), _training(batch_size=128)),
]


def _build_run_config(spec: _RunSpec) -> RunConfig:
    return RunConfig(
        run_id=spec.run_id,
        experiment_name=EXPERIMENT_NAME,
        seed=spec.seed,
        description=spec.description,
        dataset=spec.dataset,
        model=spec.model,
        training=spec.training,
    )


def generate_configs() -> None:
    """Write config.yaml for every spec and scaffold each run's folder tree."""
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    for spec in RUN_SPECS:
        run_dir = RUNS_ROOT / spec.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "artifacts").mkdir(exist_ok=True)

        config = _build_run_config(spec)
        with (run_dir / "config.yaml").open("w", encoding="utf-8") as f:
            yaml.safe_dump(config.model_dump(), f, sort_keys=False)


def generate_ground_truth() -> None:
    """Write the eval-only ground-truth label for every spec, in its own directory tree."""
    GROUND_TRUTH_ROOT.mkdir(parents=True, exist_ok=True)
    for spec in RUN_SPECS:
        with (GROUND_TRUTH_ROOT / f"{spec.run_id}.json").open("w", encoding="utf-8") as f:
            json.dump({"run_id": spec.run_id, "induced_pathology": spec.pathology}, f, indent=2)
            f.write("\n")


def main() -> None:
    generate_configs()
    generate_ground_truth()
    configs = load_and_validate(RUNS_ROOT)  # fails loudly on any bad config, before any compute
    print(f"Generated and validated {len(configs)} run configs under {RUNS_ROOT}")
    print(f"Generated {len(RUN_SPECS)} ground-truth files under {GROUND_TRUTH_ROOT}")


if __name__ == "__main__":
    main()

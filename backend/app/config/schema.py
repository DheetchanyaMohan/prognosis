"""Pydantic schema for a single experiment run configuration.

config.yaml is the single source of truth for a run's hyperparameters.
This schema intentionally has no field for a ground-truth pathology
label — those live only in data/eval/ground_truth/, generated separately,
and are never part of anything a training run or the agent can read.
`extra="forbid"` on every model means a stray key (accidentally pasted
into a YAML file) fails validation instead of silently passing through.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

RUN_ID_PATTERN = re.compile(r"^run_\d{3}$")


class DatasetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    train_size: int = Field(
        ge=100, le=5000, description="Number of training images sampled from CIFAR-10"
    )
    val_size: int = Field(
        ge=100, le=1000, description="Number of validation images sampled from CIFAR-10"
    )
    augmentation: bool = Field(
        default=True, description="Whether standard flip/crop augmentation is applied"
    )


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dropout: float = Field(
        ge=0.0, le=0.9, description="Dropout probability before the final FC layer"
    )


class TrainingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    optimizer: Literal["adam", "sgd"] = "adam"
    lr: float = Field(gt=0.0, le=1.0)
    lr_scheduler: Literal["none", "cosine", "step"] = "none"
    batch_size: int = Field(gt=0, le=512)
    weight_decay: float = Field(ge=0.0, le=1.0)
    epochs: int = Field(
        default=20, ge=1, le=100, description="Fixed at 20 across the MVP run set for comparability"
    )
    gradient_clip_norm: float | None = Field(default=None, gt=0.0)
    early_stop_on_divergence: bool = Field(
        default=True,
        description="Stop training early if loss is NaN or exceeds divergence_loss_threshold",
    )
    divergence_loss_threshold: float = Field(default=100.0, gt=0.0)


class RunConfig(BaseModel):
    """Full configuration for a single training run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    experiment_name: str
    seed: int = Field(ge=0)
    description: str = Field(max_length=280)

    dataset: DatasetConfig
    model: ModelConfig
    training: TrainingConfig

    @model_validator(mode="after")
    def _validate_run_id_format(self) -> RunConfig:
        if not RUN_ID_PATTERN.match(self.run_id):
            raise ValueError(
                f"run_id {self.run_id!r} must match pattern 'run_XXX' (e.g. 'run_001')"
            )
        return self

    @model_validator(mode="after")
    def _validate_batch_size_fits_dataset(self) -> RunConfig:
        if self.training.batch_size > self.dataset.train_size:
            raise ValueError(
                f"training.batch_size ({self.training.batch_size}) cannot exceed "
                f"dataset.train_size ({self.dataset.train_size})"
            )
        return self

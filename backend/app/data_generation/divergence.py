"""Divergence guard.

Stops a training run early if the loss goes NaN/Inf or exceeds a sanity
threshold, instead of burning the full epoch budget on a corrupted run.
Controlled per-run via RunConfig.training.early_stop_on_divergence /
divergence_loss_threshold.
"""

from __future__ import annotations

import math


class DivergenceError(Exception):
    """Raised when a run's loss diverges and the guard is enabled."""


class DivergenceGuard:
    def __init__(self, enabled: bool, loss_threshold: float) -> None:
        self._enabled = enabled
        self._loss_threshold = loss_threshold

    def check(self, epoch: int, loss: float) -> None:
        """Raises DivergenceError if `loss` indicates the run has diverged."""
        if not self._enabled:
            return
        if math.isnan(loss) or math.isinf(loss):
            raise DivergenceError(f"Loss is NaN/Inf at epoch {epoch}")
        if loss > self._loss_threshold:
            raise DivergenceError(
                f"Loss {loss:.4f} exceeded divergence threshold "
                f"{self._loss_threshold} at epoch {epoch}"
            )
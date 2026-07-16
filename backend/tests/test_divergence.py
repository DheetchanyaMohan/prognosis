import math

import pytest

from app.data_generation.divergence import DivergenceError, DivergenceGuard


def test_guard_allows_normal_loss() -> None:
    guard = DivergenceGuard(enabled=True, loss_threshold=100.0)
    guard.check(epoch=1, loss=0.5)  # should not raise


def test_guard_raises_on_nan() -> None:
    guard = DivergenceGuard(enabled=True, loss_threshold=100.0)
    with pytest.raises(DivergenceError):
        guard.check(epoch=1, loss=math.nan)


def test_guard_raises_on_inf() -> None:
    guard = DivergenceGuard(enabled=True, loss_threshold=100.0)
    with pytest.raises(DivergenceError):
        guard.check(epoch=1, loss=math.inf)


def test_guard_raises_on_threshold_exceeded() -> None:
    guard = DivergenceGuard(enabled=True, loss_threshold=10.0)
    with pytest.raises(DivergenceError):
        guard.check(epoch=1, loss=11.0)


def test_guard_allows_loss_at_exactly_threshold() -> None:
    guard = DivergenceGuard(enabled=True, loss_threshold=10.0)
    guard.check(epoch=1, loss=10.0)  # strictly greater-than triggers, not equal


def test_disabled_guard_never_raises() -> None:
    guard = DivergenceGuard(enabled=False, loss_threshold=1.0)
    guard.check(epoch=1, loss=math.inf)  # should not raise
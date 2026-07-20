"""Deterministic seeding.

Called once, before any data loading or model construction, so a given
RunConfig always produces the same result (modulo CUDA kernel
nondeterminism, irrelevant for the small CPU/single-GPU runs here).
"""

from __future__ import annotations

import random

import numpy as np
import torch


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
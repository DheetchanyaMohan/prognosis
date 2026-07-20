"""SmallCNN — the fixed architecture used by every run in this experiment
set. Only training configuration varies between runs (see
app/config/schema.py); the architecture is held constant so config diffs
and hyperparameter comparisons stay meaningful.
"""

from __future__ import annotations

from typing import cast

import torch
from torch import nn


class SmallCNN(nn.Module):
    """3 conv blocks (conv-relu-pool) + 2 FC layers, ~600K params."""

    def __init__(self, num_classes: int = 10, dropout: float = 0.3) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),  # 32x32 -> 16x16
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),  # 16x16 -> 8x8
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),  # 8x8 -> 4x4
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 4 * 4, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(256, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        return cast(torch.Tensor, self.classifier(x))
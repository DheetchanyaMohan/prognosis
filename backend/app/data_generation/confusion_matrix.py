"""Confusion matrix generation for a run's validation set."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # headless rendering, no display backend needed
import matplotlib.pyplot as plt
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

CIFAR10_CLASSES = [
    "airplane", "automobile", "bird", "cat", "deer",
    "dog", "frog", "horse", "ship", "truck",
]


def compute_confusion_matrix(
    model: nn.Module,
    val_loader: DataLoader[Any],
    device: torch.device,
    num_classes: int = 10,
) -> np.ndarray:
    model.eval()
    matrix = np.zeros((num_classes, num_classes), dtype=np.int64)
    with torch.no_grad():
        for inputs, targets in val_loader:
            inputs = inputs.to(device)
            preds = model(inputs).argmax(dim=1).cpu().numpy()
            for actual, predicted in zip(targets.numpy(), preds, strict=True):
                matrix[actual, predicted] += 1
    return matrix


def save_confusion_matrix_image(
    matrix: np.ndarray,
    path: Path,
    class_names: list[str] | None = None,
) -> None:
    class_names = class_names or CIFAR10_CLASSES
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=45, ha="right")
    ax.set_yticklabels(class_names)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Validation Confusion Matrix")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
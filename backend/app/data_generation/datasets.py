"""CIFAR-10 subset loading.

Both the train and val subsets are sampled from torchvision's CIFAR-10
*training* split, not the official test set — this is a diagnostics demo
dataset, not a benchmark submission, and drawing both from one pool keeps
the sampling logic simple and fully seed-controlled.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader, Dataset, Subset
from torchvision import datasets, transforms

CIFAR10_MEAN = (0.4914, 0.4822, 0.4465)
CIFAR10_STD = (0.2470, 0.2435, 0.2616)

DATA_CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cifar10_cache"


def _base_transform() -> transforms.Compose:
    return transforms.Compose(
        [transforms.ToTensor(), transforms.Normalize(CIFAR10_MEAN, CIFAR10_STD)]
    )


def _augmented_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.RandomCrop(32, padding=4),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(CIFAR10_MEAN, CIFAR10_STD),
        ]
    )


def build_train_val_datasets(
    train_size: int,
    val_size: int,
    augmentation: bool,
    seed: int,
) -> tuple[Dataset[Any], Dataset[Any]]:
    """Deterministically sample disjoint train/val subsets from CIFAR-10.

    A given seed always produces the same index split, computed once as a
    single shuffle over the full pool and then sliced — so train and val
    are always disjoint, regardless of how train_size/val_size vary.
    """
    DATA_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    train_pool = datasets.CIFAR10(
        root=str(DATA_CACHE_DIR),
        train=True,
        download=True,
        transform=_augmented_transform() if augmentation else _base_transform(),
    )
    val_pool = datasets.CIFAR10(
        root=str(DATA_CACHE_DIR), train=True, download=True, transform=_base_transform()
    )

    pool_size = len(train_pool)
    if train_size + val_size > pool_size:
        raise ValueError(
            f"train_size + val_size ({train_size + val_size}) exceeds the "
            f"CIFAR-10 pool size ({pool_size})"
        )

    generator = torch.Generator().manual_seed(seed)
    shuffled_indices = torch.randperm(pool_size, generator=generator).tolist()

    train_indices = shuffled_indices[:train_size]
    val_indices = shuffled_indices[train_size : train_size + val_size]

    return Subset(train_pool, train_indices), Subset(val_pool, val_indices)


def build_dataloaders(
    train_dataset: Dataset[Any],
    val_dataset: Dataset[Any],
    batch_size: int,
    seed: int,
) -> tuple[DataLoader[Any], DataLoader[Any]]:
    generator = torch.Generator().manual_seed(seed)
    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, generator=generator
    )
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    return train_loader, val_loader
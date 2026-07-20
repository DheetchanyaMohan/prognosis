"""Configurable training loop.

`run_training` is a thin orchestrator wiring together the model,
optimizer, dataloaders, divergence guard, CSV writer, and structured
logger for a single RunConfig. It performs no diagnostics computation —
that is the next phase (app/tools/metrics_analysis.py), which will
consume the artifacts this module produces.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import torch
from torch import nn
from torch.utils.data import DataLoader

from app.config.schema import RunConfig
from app.data_generation.divergence import DivergenceError, DivergenceGuard
from app.data_generation.metrics_writer import EpochMetrics, MetricsCsvWriter


def _build_optimizer(model: nn.Module, config: RunConfig) -> torch.optim.Optimizer:
    if config.training.optimizer == "adam":
        return torch.optim.Adam(
            model.parameters(), lr=config.training.lr, weight_decay=config.training.weight_decay
        )
    return torch.optim.SGD(
        model.parameters(),
        lr=config.training.lr,
        weight_decay=config.training.weight_decay,
        momentum=0.9,
    )


def _build_scheduler(
    optimizer: torch.optim.Optimizer, config: RunConfig
) -> torch.optim.lr_scheduler.LRScheduler | None:
    if config.training.lr_scheduler == "cosine":
        return torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config.training.epochs)
    if config.training.lr_scheduler == "step":
        step_size = max(1, config.training.epochs // 3)
        return torch.optim.lr_scheduler.StepLR(optimizer, step_size=step_size, gamma=0.1)
    return None


def _run_epoch(
    model: nn.Module,
    loader: DataLoader[Any],
    criterion: nn.Module,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None,
    gradient_clip_norm: float | None,
) -> tuple[float, float]:
    """Runs one pass over `loader`. Trains if optimizer is given, else evaluates only."""
    is_train = optimizer is not None
    model.train(is_train)

    total_loss = 0.0
    correct = 0
    total = 0

    with torch.enable_grad() if is_train else torch.no_grad():
        for inputs, targets in loader:
            inputs, targets = inputs.to(device), targets.to(device)

            if optimizer is not None:
                optimizer.zero_grad()

            outputs = model(inputs)
            loss = criterion(outputs, targets)

            if optimizer is not None:
                loss.backward()
                if gradient_clip_norm is not None:
                    nn.utils.clip_grad_norm_(model.parameters(), gradient_clip_norm)
                optimizer.step()

            batch_size = targets.size(0)
            total_loss += loss.item() * batch_size
            correct += int((outputs.argmax(dim=1) == targets).sum().item())
            total += batch_size

    return total_loss / total, correct / total


@dataclass
class TrainingResult:
    epoch_history: list[EpochMetrics]
    diverged: bool
    wall_clock_sec: float


def run_training(
    model: nn.Module,
    train_loader: DataLoader[Any],
    val_loader: DataLoader[Any],
    config: RunConfig,
    device: torch.device,
    metrics_writer: MetricsCsvWriter,
    logger: logging.Logger,
) -> TrainingResult:
    optimizer = _build_optimizer(model, config)
    scheduler = _build_scheduler(optimizer, config)
    criterion = nn.CrossEntropyLoss()
    guard = DivergenceGuard(
        enabled=config.training.early_stop_on_divergence,
        loss_threshold=config.training.divergence_loss_threshold,
    )

    epoch_history: list[EpochMetrics] = []
    diverged = False
    run_start = time.monotonic()

    for epoch in range(1, config.training.epochs + 1):
        epoch_start = time.monotonic()

        train_loss, train_acc = _run_epoch(
            model, train_loader, criterion, device, optimizer, config.training.gradient_clip_norm
        )
        val_loss, val_acc = _run_epoch(model, val_loader, criterion, device, None, None)

        if scheduler is not None:
            scheduler.step()

        current_lr = float(optimizer.param_groups[0]["lr"])
        epoch_time = time.monotonic() - epoch_start

        logger.info(
            f"[epoch {epoch}] train_loss={train_loss:.4f} val_loss={val_loss:.4f} "
            f"train_acc={train_acc:.4f} val_acc={val_acc:.4f} lr={current_lr:.6f}"
        )
        if epoch_history and val_loss > epoch_history[-1].val_loss * 1.5:
            logger.warning(f"[epoch {epoch}] val_loss increased sharply vs previous epoch")

        metrics = EpochMetrics(
            epoch=epoch,
            train_loss=train_loss,
            val_loss=val_loss,
            train_acc=train_acc,
            val_acc=val_acc,
            lr=current_lr,
            epoch_time_sec=epoch_time,
        )
        metrics_writer.write(metrics)
        epoch_history.append(metrics)

        try:
            guard.check(epoch, train_loss)
        except DivergenceError as exc:
            logger.warning(f"Stopping early: {exc}")
            diverged = True
            break

    return TrainingResult(
        epoch_history=epoch_history,
        diverged=diverged,
        wall_clock_sec=time.monotonic() - run_start,
    )
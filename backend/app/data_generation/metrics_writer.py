"""CSV writer for per-epoch metrics.

Writes one row per completed epoch, incrementally rather than buffering
and writing once at the end — a run that stops early via the divergence
guard still leaves a valid, readable metrics.csv for whatever epochs did
complete.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, fields
from pathlib import Path


@dataclass(frozen=True)
class EpochMetrics:
    epoch: int
    train_loss: float
    val_loss: float
    train_acc: float
    val_acc: float
    lr: float
    epoch_time_sec: float


class MetricsCsvWriter:
    """Appends EpochMetrics rows to a CSV file, writing the header exactly once."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._fieldnames = [f.name for f in fields(EpochMetrics)]

    def write(self, metrics: EpochMetrics) -> None:
        write_header = not self._path.exists()
        with self._path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self._fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerow(asdict(metrics))
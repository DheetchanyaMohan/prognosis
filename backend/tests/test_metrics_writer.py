import csv
from pathlib import Path

from app.data_generation.metrics_writer import EpochMetrics, MetricsCsvWriter


def test_writes_header_once_and_appends_rows(tmp_path: Path) -> None:
    path = tmp_path / "metrics.csv"
    writer = MetricsCsvWriter(path)

    writer.write(EpochMetrics(1, 0.9, 1.0, 0.5, 0.4, 0.001, 1.2))
    writer.write(EpochMetrics(2, 0.7, 0.8, 0.6, 0.5, 0.001, 1.1))

    with path.open() as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    assert rows[0]["epoch"] == "1"
    assert rows[1]["epoch"] == "2"
    assert list(rows[0].keys()) == [
        "epoch", "train_loss", "val_loss", "train_acc", "val_acc", "lr", "epoch_time_sec",
    ]


def test_partial_write_survives_early_stop(tmp_path: Path) -> None:
    """A run that diverges after 3 epochs should leave a valid 3-row CSV,
    not a corrupted or empty file."""
    path = tmp_path / "metrics.csv"
    writer = MetricsCsvWriter(path)
    for epoch in range(1, 4):
        writer.write(EpochMetrics(epoch, 1.0, 1.0, 0.5, 0.5, 0.001, 1.0))

    with path.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3
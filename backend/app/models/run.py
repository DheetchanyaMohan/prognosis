"""Run ORM model.

Deliberately has no ground-truth pathology column: this table is queryable
by agent tools, so ground truth never enters it. Labels live only in
data/eval/ground_truth/, outside this schema entirely.

Phase 2: the five artifact-path columns (config_path, metrics_path,
log_path, summary_path, diagnostics_path) have been removed. Artifact
paths are computed at call time via app.tools.run_paths from
(experiment.name, run_name, settings.data_root) — nothing has read
these columns since Phase 1, and nothing writes them anymore either.
See app/db/migrations/versions/0002_drop_run_artifact_path_columns.py
for the corresponding schema migration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.experiment import Experiment
    from app.models.metric import Metric


class Run(IDMixin, TimestampMixin, Base):
    """A single training run belonging to an experiment."""

    __tablename__ = "runs"

    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_name: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="complete")

    experiment: Mapped[Experiment] = relationship(back_populates="runs")
    metrics: Mapped[list[Metric]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="Metric.epoch",
    )

    def __repr__(self) -> str:
        return (
            f"Run(id={self.id!r}, run_name={self.run_name!r}, "
            f"experiment_id={self.experiment_id!r})"
        )
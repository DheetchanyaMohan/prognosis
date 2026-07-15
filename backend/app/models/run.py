"""Run ORM model.

Deliberately has no ground-truth pathology column: this table is queryable
by agent tools, so ground truth never enters it. Labels live only in
data/eval/ground_truth/, outside this schema entirely.
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

    config_path: Mapped[str] = mapped_column(String(512), nullable=False)
    metrics_path: Mapped[str] = mapped_column(String(512), nullable=False)
    log_path: Mapped[str] = mapped_column(String(512), nullable=False)
    summary_path: Mapped[str] = mapped_column(String(512), nullable=False)
    diagnostics_path: Mapped[str] = mapped_column(String(512), nullable=False)

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

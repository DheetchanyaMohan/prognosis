"""Metric ORM model — one row per epoch per run."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import IDMixin

if TYPE_CHECKING:
    from app.models.run import Run


class Metric(IDMixin, Base):
    """A single epoch's metrics for a run.

    No TimestampMixin here — unlike Experiment/Run, a metric row's
    ordering is meaningful via `epoch`, not insertion time.
    """

    __tablename__ = "metrics"
    __table_args__ = (UniqueConstraint("run_id", "epoch", name="uq_metric_run_epoch"),)

    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    epoch: Mapped[int] = mapped_column(Integer, nullable=False)

    train_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    val_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    train_acc: Mapped[float | None] = mapped_column(Float, nullable=True)
    val_acc: Mapped[float | None] = mapped_column(Float, nullable=True)
    lr: Mapped[float | None] = mapped_column(Float, nullable=True)
    epoch_time_sec: Mapped[float | None] = mapped_column(Float, nullable=True)

    run: Mapped[Run] = relationship(back_populates="metrics")

    def __repr__(self) -> str:
        return f"Metric(run_id={self.run_id!r}, epoch={self.epoch!r})"

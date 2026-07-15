"""Experiment ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.run import Run


class Experiment(IDMixin, TimestampMixin, Base):
    """A named group of related training runs."""

    __tablename__ = "experiments"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    runs: Mapped[list[Run]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
        order_by="Run.created_at",
    )

    def __repr__(self) -> str:
        return f"Experiment(id={self.id!r}, name={self.name!r})"

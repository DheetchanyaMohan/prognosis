"""Shared model mixins.

Composed into concrete models alongside app.db.base.Base. Kept separate
from the declarative base itself so a model can opt out of a mixin
(Metric does not need TimestampMixin) without touching Base.
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class IDMixin:
    """Standard auto-incrementing integer primary key."""

    id: Mapped[int] = mapped_column(primary_key=True)


class TimestampMixin:
    """Server-side created_at timestamp, set once at insert."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

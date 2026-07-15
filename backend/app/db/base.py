"""SQLAlchemy declarative base.

All ORM models (added in a later phase) inherit from Base. Kept in its own
module, separate from session.py, so models can import Base without
triggering engine/session creation.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models in the application."""

"""Database initialization helpers.

Alembic (see app/db/migrations/) is the source of truth for schema changes
in real deployments. init_db() is a convenience for local development and
tests, where running full migrations is unnecessary overhead.
"""

import app.models  # noqa: F401  (registers models on Base.metadata)
from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    """Create all tables directly from the current models.

    Not used in production — production schema changes go through Alembic
    migrations so they're versioned and reviewable.
    """
    Base.metadata.create_all(bind=engine)

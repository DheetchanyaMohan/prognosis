"""Internal DB session and lookup helpers shared by the tool layer.

Not part of the public tool API — LangGraph nodes never import this
module directly. Its only job is to keep session-scoping and
not-found handling in one place so metrics_tool.py and experiment_tool.py
don't each duplicate it.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Run


class RunNotFoundError(Exception):
    """Raised when a requested run_id does not exist."""


class ExperimentNotFoundError(Exception):
    """Raised when a requested experiment_name does not exist."""


@contextmanager
def session_scope(db: Session | None) -> Iterator[Session]:
    """Yields `db` unchanged if provided; otherwise opens and closes a
    fresh session. This is what lets every tool function accept an
    optional `db` param without ever requiring a caller (a LangGraph
    node) to import SQLAlchemy or manage a session itself.
    """
    if db is not None:
        yield db
        return
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_run_or_raise(session: Session, run_id: str) -> Run:
    run = session.query(Run).filter(Run.run_name == run_id).one_or_none()
    if run is None:
        raise RunNotFoundError(f"No run found with run_id={run_id!r}")
    return run
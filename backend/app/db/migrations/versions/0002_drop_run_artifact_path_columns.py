"""drop obsolete run artifact-path columns

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-29

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = ("config_path", "metrics_path", "log_path", "summary_path", "diagnostics_path")


def upgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        for column in _COLUMNS:
            batch_op.drop_column(column)


def downgrade() -> None:
    # server_default="" (not nullable=False with no default) so this
    # actually works against a table that already has rows — matches
    # exactly what Phase 1's persistence.py wrote into these columns
    # before they were dropped, rather than an unenforceable NOT NULL
    # with nothing to backfill existing rows with.
    with op.batch_alter_table("runs") as batch_op:
        for column in _COLUMNS:
            batch_op.add_column(
                sa.Column(column, sa.String(length=512), nullable=False, server_default="")
            )
"""create experiments, runs, and metrics tables

Revision ID: 0001
Revises:
Create Date: 2026-07-11

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "experiments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "experiment_id",
            sa.Integer(),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("run_name", sa.String(length=255), nullable=False),
        sa.Column("config_path", sa.String(length=512), nullable=False),
        sa.Column("metrics_path", sa.String(length=512), nullable=False),
        sa.Column("log_path", sa.String(length=512), nullable=False),
        sa.Column("summary_path", sa.String(length=512), nullable=False),
        sa.Column("diagnostics_path", sa.String(length=512), nullable=False),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="complete"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_runs_experiment_id", "runs", ["experiment_id"])

    op.create_table(
        "metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "run_id",
            sa.Integer(),
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("epoch", sa.Integer(), nullable=False),
        sa.Column("train_loss", sa.Float(), nullable=True),
        sa.Column("val_loss", sa.Float(), nullable=True),
        sa.Column("train_acc", sa.Float(), nullable=True),
        sa.Column("val_acc", sa.Float(), nullable=True),
        sa.Column("lr", sa.Float(), nullable=True),
        sa.Column("epoch_time_sec", sa.Float(), nullable=True),
        sa.UniqueConstraint("run_id", "epoch", name="uq_metric_run_epoch"),
    )
    op.create_index("ix_metrics_run_id", "metrics", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_metrics_run_id", table_name="metrics")
    op.drop_table("metrics")
    op.drop_index("ix_runs_experiment_id", table_name="runs")
    op.drop_table("runs")
    op.drop_table("experiments")

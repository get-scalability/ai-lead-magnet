"""initial schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-05-05 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "a1b2c3d4e5f6"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lead_magnet_run",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email_hash", sa.String(64), nullable=False),
        sa.Column("tool_slug", sa.String(64), nullable=False),
        sa.Column("run_period", sa.String(10), nullable=False),
        sa.Column("run_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email_hash", "tool_slug", "run_period", name="uq_run_per_period"),
    )
    op.create_index("ix_lead_magnet_run_email_hash", "lead_magnet_run", ["email_hash"])

    op.create_table(
        "lead_magnet_result",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "public_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tool_slug", sa.String(64), nullable=False),
        sa.Column("input_data", postgresql.JSONB(), nullable=False),
        sa.Column("output_data", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("ix_lead_magnet_result_public_id", "lead_magnet_result", ["public_id"])


def downgrade() -> None:
    op.drop_table("lead_magnet_result")
    op.drop_table("lead_magnet_run")

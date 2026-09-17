"""Align CREATE_WORK_LOG persistence with Dynamic Form V3.1.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-16
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Persist work-log contract fields and allow optional plot/activity."""

    op.add_column(
        "cultivation_logs",
        sa.Column(
            "result_status",
            sa.String(length=20),
            nullable=True,
        ),
    )

    op.add_column(
        "cultivation_logs",
        sa.Column(
            "material_batch_text",
            sa.Text(),
            nullable=True,
        ),
    )

    op.alter_column(
        "cultivation_logs",
        "lot_code",
        existing_type=sa.String(length=50),
        nullable=True,
    )

    op.alter_column(
        "cultivation_logs",
        "activity_code",
        existing_type=sa.String(length=50),
        nullable=True,
    )


def downgrade() -> None:
    """
    Restore the pre-V3.1 schema.

    Downgrade assumes no row contains NULL lot_code/activity_code.
    """

    op.alter_column(
        "cultivation_logs",
        "activity_code",
        existing_type=sa.String(length=50),
        nullable=False,
    )

    op.alter_column(
        "cultivation_logs",
        "lot_code",
        existing_type=sa.String(length=50),
        nullable=False,
    )

    op.drop_column(
        "cultivation_logs",
        "material_batch_text",
    )

    op.drop_column(
        "cultivation_logs",
        "result_status",
    )

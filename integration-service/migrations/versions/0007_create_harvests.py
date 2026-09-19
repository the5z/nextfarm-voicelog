"""Create harvests table.

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "harvests",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "client_record_id",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "plot_code",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "crop_id",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "quantity",
            sa.Numeric(
                precision=14,
                scale=3,
            ),
            nullable=False,
        ),
        sa.Column(
            "unit_code",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "harvest_date_text",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "photo",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "note",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "confirmed",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id"
        ),
        sa.UniqueConstraint(
            "client_record_id",
            name=(
                "uq_harvests_client_record_id"
            ),
        ),
    )

    op.create_index(
        op.f(
            "ix_harvests_client_record_id"
        ),
        "harvests",
        ["client_record_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_harvests_plot_code"
        ),
        "harvests",
        ["plot_code"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_harvests_crop_id"
        ),
        "harvests",
        ["crop_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_harvests_unit_code"
        ),
        "harvests",
        ["unit_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f(
            "ix_harvests_unit_code"
        ),
        table_name="harvests",
    )

    op.drop_index(
        op.f(
            "ix_harvests_crop_id"
        ),
        table_name="harvests",
    )

    op.drop_index(
        op.f(
            "ix_harvests_plot_code"
        ),
        table_name="harvests",
    )

    op.drop_index(
        op.f(
            "ix_harvests_client_record_id"
        ),
        table_name="harvests",
    )

    op.drop_table(
        "harvests"
    )
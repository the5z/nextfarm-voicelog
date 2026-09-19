"""Create plots table.

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "plots",
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
            "plot_name_or_code",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "region_id",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "boundary_required",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "owner_text",
            sa.String(length=200),
            nullable=True,
        ),
        sa.Column(
            "current_crop_id",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "location_hint_text",
            sa.String(length=300),
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
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "client_record_id",
            name="uq_plots_client_record_id",
        ),
        sa.UniqueConstraint(
            "plot_code",
            name="uq_plots_plot_code",
        ),
    )

    for column in [
        "client_record_id",
        "plot_code",
        "plot_name_or_code",
        "region_id",
        "current_crop_id",
    ]:
        op.create_index(
            op.f(
                f"ix_plots_{column}"
            ),
            "plots",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "current_crop_id",
        "region_id",
        "plot_name_or_code",
        "plot_code",
        "client_record_id",
    ]:
        op.drop_index(
            op.f(
                f"ix_plots_{column}"
            ),
            table_name="plots",
        )

    op.drop_table("plots")
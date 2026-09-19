"""Create seasons table.

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "seasons",
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
            "season_id",
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
            "planting_date_text",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "season_name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "expected_harvest_date_text",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "plant_count",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "expected_yield",
            sa.Numeric(14, 3),
            nullable=True,
        ),
        sa.Column(
            "expected_yield_unit_code",
            sa.String(length=20),
            nullable=True,
        ),
        sa.Column(
            "process_template_text",
            sa.String(length=200),
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
            name="uq_seasons_client_record_id",
        ),
        sa.UniqueConstraint(
            "season_id",
            name="uq_seasons_season_id",
        ),
    )

    for column in [
        "client_record_id",
        "season_id",
        "plot_code",
        "crop_id",
        "season_name",
    ]:
        op.create_index(
            op.f(
                f"ix_seasons_{column}"
            ),
            "seasons",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "season_name",
        "crop_id",
        "plot_code",
        "season_id",
        "client_record_id",
    ]:
        op.drop_index(
            op.f(
                f"ix_seasons_{column}"
            ),
            table_name="seasons",
        )

    op.drop_table(
        "seasons"
    )
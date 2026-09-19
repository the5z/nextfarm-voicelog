"""Create crop types table.

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "crop_types",
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
            "crop_id",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "crop_name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "crop_group_text",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "crop_code_suggestion",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "days_to_harvest",
            sa.Integer(),
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
            name=(
                "uq_crop_types_client_record_id"
            ),
        ),
        sa.UniqueConstraint(
            "crop_id",
            name="uq_crop_types_crop_id",
        ),
    )

    for column in [
        "client_record_id",
        "crop_id",
        "crop_name",
    ]:
        op.create_index(
            op.f(
                f"ix_crop_types_{column}"
            ),
            "crop_types",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in [
        "crop_name",
        "crop_id",
        "client_record_id",
    ]:
        op.drop_index(
            op.f(
                f"ix_crop_types_{column}"
            ),
            table_name="crop_types",
        )

    op.drop_table(
        "crop_types"
    )
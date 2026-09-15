"""Add NextFarm context fields to cultivation logs.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Thêm context NextFarm, nullable để giữ tương thích record cũ."""

    columns = [
        ("tenant_id", "ix_cultivation_logs_tenant_id"),
        ("user_id", "ix_cultivation_logs_user_id"),
        ("season_id", "ix_cultivation_logs_season_id"),
        ("plot_id", "ix_cultivation_logs_plot_id"),
        ("task_id", "ix_cultivation_logs_task_id"),
    ]

    for column_name, index_name in columns:
        op.add_column(
            "cultivation_logs",
            sa.Column(
                column_name,
                sa.String(length=100),
                nullable=True,
            ),
        )
        op.create_index(
            index_name,
            "cultivation_logs",
            [column_name],
            unique=False,
        )


def downgrade() -> None:
    """Xóa các context fields."""

    for column_name, index_name in reversed([
        ("tenant_id", "ix_cultivation_logs_tenant_id"),
        ("user_id", "ix_cultivation_logs_user_id"),
        ("season_id", "ix_cultivation_logs_season_id"),
        ("plot_id", "ix_cultivation_logs_plot_id"),
        ("task_id", "ix_cultivation_logs_task_id"),
    ]):
        op.drop_index(
            index_name,
            table_name="cultivation_logs",
        )
        op.drop_column(
            "cultivation_logs",
            column_name,
        )

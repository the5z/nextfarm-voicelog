"""Create integration history table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-14
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Tạo bảng lưu lịch sử xử lý của Integration Service.
    """

    op.create_table(
        "integration_history",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "client_record_id",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "request_payload",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "response_payload",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "http_status",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_integration_history",
        ),
    )

    op.create_index(
        "ix_integration_history_event_type",
        "integration_history",
        ["event_type"],
        unique=False,
    )

    op.create_index(
        "ix_integration_history_client_record_id",
        "integration_history",
        ["client_record_id"],
        unique=False,
    )

    op.create_index(
        "ix_integration_history_status",
        "integration_history",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """
    Xóa bảng lịch sử Integration.
    """

    op.drop_index(
        "ix_integration_history_status",
        table_name="integration_history",
    )

    op.drop_index(
        "ix_integration_history_client_record_id",
        table_name="integration_history",
    )

    op.drop_index(
        "ix_integration_history_event_type",
        table_name="integration_history",
    )

    op.drop_table(
        "integration_history"
    )
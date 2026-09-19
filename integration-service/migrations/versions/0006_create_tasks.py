"""Create tasks table.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tasks",
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
            "task_name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "task_type_text",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "due_time_text",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "assignee_text",
            sa.String(length=200),
            nullable=True,
        ),
        sa.Column(
            "photo_required",
            sa.Boolean(),
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
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "client_record_id",
            name="uq_tasks_client_record_id",
        ),
    )

    op.create_index(
        op.f(
            "ix_tasks_client_record_id"
        ),
        "tasks",
        ["client_record_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_tasks_season_id"
        ),
        "tasks",
        ["season_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f(
            "ix_tasks_season_id"
        ),
        table_name="tasks",
    )

    op.drop_index(
        op.f(
            "ix_tasks_client_record_id"
        ),
        table_name="tasks",
    )

    op.drop_table("tasks")
"""Create issue reports table.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-18
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "issue_reports",

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
            "issue_type",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "severity",
            sa.String(length=20),
            nullable=False,
        ),

        sa.Column(
            "description",
            sa.Text(),
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
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),

        sa.UniqueConstraint(
            "client_record_id",
            name=(
                "uq_issue_reports_"
                "client_record_id"
            ),
        ),
    )

    op.create_index(
        op.f(
            "ix_issue_reports_"
            "client_record_id"
        ),
        "issue_reports",
        ["client_record_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_issue_reports_plot_code"
        ),
        "issue_reports",
        ["plot_code"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_issue_reports_issue_type"
        ),
        "issue_reports",
        ["issue_type"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_issue_reports_severity"
        ),
        "issue_reports",
        ["severity"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f(
            "ix_issue_reports_severity"
        ),
        table_name="issue_reports",
    )

    op.drop_index(
        op.f(
            "ix_issue_reports_issue_type"
        ),
        table_name="issue_reports",
    )

    op.drop_index(
        op.f(
            "ix_issue_reports_plot_code"
        ),
        table_name="issue_reports",
    )

    op.drop_index(
        op.f(
            "ix_issue_reports_"
            "client_record_id"
        ),
        table_name="issue_reports",
    )

    op.drop_table(
        "issue_reports"
    )
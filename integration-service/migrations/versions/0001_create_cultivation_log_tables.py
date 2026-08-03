"""Create cultivation log tables.

Revision ID: 0001
Revises:
Create Date: 2026-08-03
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Tạo bảng nhật ký canh tác và bảng vật tư đi kèm.
    """

    op.create_table(
        "cultivation_logs",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "schema_version",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "client_record_id",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "transcript",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "lot_code",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "activity_code",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "performed_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "performer_code",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "source",
            sa.String(length=20),
            nullable=False,
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
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_cultivation_logs",
        ),
        sa.UniqueConstraint(
            "client_record_id",
            name="uq_cultivation_logs_client_record_id",
        ),
    )

    op.create_index(
        "ix_cultivation_logs_client_record_id",
        "cultivation_logs",
        ["client_record_id"],
        unique=False,
    )

    op.create_index(
        "ix_cultivation_logs_lot_code",
        "cultivation_logs",
        ["lot_code"],
        unique=False,
    )

    op.create_index(
        "ix_cultivation_logs_activity_code",
        "cultivation_logs",
        ["activity_code"],
        unique=False,
    )

    op.create_index(
        "ix_cultivation_logs_performer_code",
        "cultivation_logs",
        ["performer_code"],
        unique=False,
    )

    op.create_table(
        "cultivation_log_materials",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "log_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "material_code",
            sa.String(length=50),
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
        sa.ForeignKeyConstraint(
            ["log_id"],
            ["cultivation_logs.id"],
            name="fk_cultivation_log_materials_log_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_cultivation_log_materials",
        ),
    )

    op.create_index(
        "ix_cultivation_log_materials_log_id",
        "cultivation_log_materials",
        ["log_id"],
        unique=False,
    )

    op.create_index(
        "ix_cultivation_log_materials_material_code",
        "cultivation_log_materials",
        ["material_code"],
        unique=False,
    )


def downgrade() -> None:
    """
    Xóa các bảng theo thứ tự ngược với lúc tạo.
    """

    op.drop_index(
        "ix_cultivation_log_materials_material_code",
        table_name="cultivation_log_materials",
    )

    op.drop_index(
        "ix_cultivation_log_materials_log_id",
        table_name="cultivation_log_materials",
    )

    op.drop_table(
        "cultivation_log_materials"
    )

    op.drop_index(
        "ix_cultivation_logs_performer_code",
        table_name="cultivation_logs",
    )

    op.drop_index(
        "ix_cultivation_logs_activity_code",
        table_name="cultivation_logs",
    )

    op.drop_index(
        "ix_cultivation_logs_lot_code",
        table_name="cultivation_logs",
    )

    op.drop_index(
        "ix_cultivation_logs_client_record_id",
        table_name="cultivation_logs",
    )

    op.drop_table(
        "cultivation_logs"
    )
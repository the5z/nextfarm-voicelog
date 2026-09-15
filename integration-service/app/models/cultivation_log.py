from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CultivationLogModel(Base):
    """Bảng lưu nhật ký canh tác."""

    __tablename__ = "cultivation_logs"

    __table_args__ = (
        UniqueConstraint(
            "client_record_id",
            name="uq_cultivation_logs_client_record_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    schema_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="1.0",
    )

    client_record_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    transcript: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    tenant_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    user_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    season_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    plot_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    task_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    lot_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    activity_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    performer_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="voice",
    )

    confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="saved",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    materials: Mapped[list["CultivationLogMaterialModel"]] = relationship(
        back_populates="log",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CultivationLogMaterialModel(Base):
    """Bảng lưu các vật tư thuộc một nhật ký."""

    __tablename__ = "cultivation_log_materials"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    log_id: Mapped[int] = mapped_column(
        ForeignKey(
            "cultivation_logs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    material_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )

    unit_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    log: Mapped["CultivationLogModel"] = relationship(
        back_populates="materials",
    )
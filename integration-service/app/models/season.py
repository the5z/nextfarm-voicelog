from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SeasonModel(Base):
    """Bảng lưu mùa vụ được tạo bởi CREATE_SEASON."""

    __tablename__ = "seasons"

    __table_args__ = (
        UniqueConstraint(
            "client_record_id",
            name="uq_seasons_client_record_id",
        ),
        UniqueConstraint(
            "season_id",
            name="uq_seasons_season_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    client_record_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    season_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    plot_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    crop_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    planting_date_text: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    season_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    expected_harvest_date_text: Mapped[
        str | None
    ] = mapped_column(
        String(100),
        nullable=True,
    )

    plant_count: Mapped[int | None] = mapped_column(
        Integer(),
        nullable=True,
    )

    expected_yield: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(14, 3),
        nullable=True,
    )

    expected_yield_unit_code: Mapped[
        str | None
    ] = mapped_column(
        String(20),
        nullable=True,
    )

    process_template_text: Mapped[
        str | None
    ] = mapped_column(
        String(200),
        nullable=True,
    )

    confirmed: Mapped[bool] = mapped_column(
        Boolean(),
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
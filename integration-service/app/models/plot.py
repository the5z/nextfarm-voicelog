from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PlotModel(Base):
    """Thửa đất được tạo bởi CREATE_PLOT."""

    __tablename__ = "plots"

    __table_args__ = (
        UniqueConstraint(
            "client_record_id",
            name="uq_plots_client_record_id",
        ),
        UniqueConstraint(
            "plot_code",
            name="uq_plots_plot_code",
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

    plot_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    plot_name_or_code: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    region_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    boundary_required: Mapped[bool] = mapped_column(
        Boolean(),
        nullable=False,
    )

    owner_text: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    current_crop_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    location_hint_text: Mapped[
        str | None
    ] = mapped_column(
        String(300),
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
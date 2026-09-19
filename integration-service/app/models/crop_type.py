from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CropTypeModel(Base):
    """
    Bảng lưu loại cây trồng được tạo bởi
    CREATE_CROP_TYPE.
    """

    __tablename__ = "crop_types"

    __table_args__ = (
        UniqueConstraint(
            "client_record_id",
            name="uq_crop_types_client_record_id",
        ),
        UniqueConstraint(
            "crop_id",
            name="uq_crop_types_crop_id",
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

    crop_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    crop_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    crop_group_text: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    crop_code_suggestion: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    days_to_harvest: Mapped[int | None] = mapped_column(
        Integer(),
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
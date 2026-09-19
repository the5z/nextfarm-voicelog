from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TaskModel(Base):
    """
    Bảng lưu CREATE_TASK.

    season_id là canonical ID đã resolve.
    Các field *_text chưa có canonical source
    được giữ nguyên sau khi người dùng xác nhận.
    """

    __tablename__ = "tasks"

    __table_args__ = (
        UniqueConstraint(
            "client_record_id",
            name="uq_tasks_client_record_id",
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

    task_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    task_type_text: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    due_time_text: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    assignee_text: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    photo_required: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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
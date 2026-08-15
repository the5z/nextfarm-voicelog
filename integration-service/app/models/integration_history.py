from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Integer,
    JSON,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class IntegrationHistoryModel(Base):
    """
    Lịch sử các sự kiện quan trọng của Integration Service.
    """

    __tablename__ = "integration_history"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    client_record_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    request_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    response_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    http_status: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
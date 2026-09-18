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


class IssueReportModel(Base):
    """
    Bảng lưu báo cáo sự cố theo
    CREATE_ISSUE_REPORT.
    """

    __tablename__ = "issue_reports"

    __table_args__ = (
        UniqueConstraint(
            "client_record_id",
            name="uq_issue_reports_client_record_id",
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

    issue_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    photo: Mapped[str | None] = mapped_column(
        Text,
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
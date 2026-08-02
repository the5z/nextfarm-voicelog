from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.responses import IssueItem


class SyncLogsRequest(BaseModel):
    """Yêu cầu đồng bộ nhiều nhật ký từ một thiết bị."""

    device_id: str = Field(
        min_length=1,
        max_length=100,
        description="Mã định danh của thiết bị gửi dữ liệu",
    )

    synced_at: datetime | None = Field(
        default=None,
        description="Thời điểm thiết bị bắt đầu đồng bộ",
    )

    # Dùng dict thay vì CultivationLogInput để từng bản ghi
    # được kiểm tra độc lập. Một bản ghi sai sẽ không làm
    # toàn bộ request bị HTTP 422.
    records: list[dict[str, Any]] = Field(
        min_length=1,
        max_length=100,
        description="Danh sách nhật ký cần đồng bộ",
    )


class SyncRecordResult(BaseModel):
    """Kết quả xử lý một bản ghi trong lô đồng bộ."""

    client_record_id: str | None = None

    status: Literal[
        "saved",
        "already_exists",
        "failed",
    ]

    log_id: int | None = None

    errors: list[IssueItem] = Field(default_factory=list)


class SyncSummary(BaseModel):
    """Thống kê kết quả đồng bộ."""

    total: int
    saved: int
    duplicated: int
    failed: int


class SyncLogsResponse(BaseModel):
    """Phản hồi của API đồng bộ."""

    success: bool
    device_id: str
    summary: SyncSummary
    results: list[SyncRecordResult]
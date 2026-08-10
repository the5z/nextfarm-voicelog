from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class SyncLogsRequest(BaseModel):
    """
    Dữ liệu đồng bộ nhật ký từ một thiết bị.

    records được giữ ở dạng dictionary để từng bản ghi có thể
    được kiểm tra độc lập trong sync_service.py.

    Nhờ đó, một bản ghi lỗi không làm FastAPI từ chối toàn bộ
    request với mã lỗi 422.
    """

    device_id: str = Field(
        min_length=1,
        max_length=200,
        description="Mã định danh của thiết bị gửi dữ liệu",
    )

    synced_at: datetime = Field(
        description="Thời điểm thiết bị bắt đầu đồng bộ",
    )

    records: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Danh sách nhật ký cần đồng bộ",
    )


class SyncIssue(BaseModel):
    """
    Chi tiết một lỗi xảy ra khi đồng bộ bản ghi.
    """

    field: str = Field(
        description="Tên trường dữ liệu xảy ra lỗi",
    )

    code: str = Field(
        description="Mã lỗi dùng cho frontend xử lý",
    )

    message: str = Field(
        description="Nội dung mô tả lỗi",
    )


class SyncRecordResult(BaseModel):
    """
    Kết quả đồng bộ của một bản ghi riêng lẻ.
    """

    client_record_id: str = Field(
        description=(
            "Mã bản ghi do thiết bị tạo hoặc mã tạm "
            "khi bản ghi thiếu client_record_id"
        ),
    )

    success: bool = Field(
        description=(
            "True nếu bản ghi đã được lưu hoặc đã tồn tại; "
            "False nếu bản ghi đồng bộ thất bại"
        ),
    )

    status: Literal[
        "saved",
        "already_exists",
        "failed",
    ] = Field(
        description="Trạng thái xử lý của bản ghi",
    )

    data: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Dữ liệu đã lưu; bằng null khi bản ghi thất bại"
        ),
    )

    errors: list[SyncIssue] = Field(
        default_factory=list,
        description=(
            "Danh sách lỗi; rỗng khi bản ghi thành công"
        ),
    )


class SyncSummary(BaseModel):
    """
    Thống kê kết quả của một lần đồng bộ.
    """

    total: int = Field(
        ge=0,
        description="Tổng số bản ghi được gửi lên",
    )

    saved: int = Field(
        ge=0,
        description="Số bản ghi vừa được lưu mới",
    )

    duplicated: int = Field(
        ge=0,
        description="Số bản ghi đã tồn tại từ trước",
    )

    failed: int = Field(
        ge=0,
        description="Số bản ghi đồng bộ thất bại",
    )


class SyncLogsResponse(BaseModel):
    """
    Kết quả chung của API đồng bộ nhật ký.
    """

    success: bool = Field(
        description=(
            "True khi không có bản ghi thất bại; "
            "False khi có ít nhất một bản ghi lỗi"
        ),
    )

    device_id: str = Field(
        description="Mã thiết bị đã gửi dữ liệu",
    )

    synced_at: datetime = Field(
        description="Thời điểm đồng bộ từ request",
    )

    summary: SyncSummary = Field(
        description="Thống kê kết quả đồng bộ",
    )

    results: list[SyncRecordResult] = Field(
        default_factory=list,
        description="Kết quả xử lý chi tiết từng bản ghi",
    )
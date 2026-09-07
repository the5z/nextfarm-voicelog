from typing import Any, Literal

from pydantic import BaseModel, Field


class IssueItem(BaseModel):
    """
    Một lỗi hoặc cảnh báo liên quan
    đến dữ liệu nhật ký.
    """

    field: str
    code: str
    message: str

    # Chỉ warning thực sự cần
    # người dùng xác nhận mới bật True.
    requires_confirmation: bool = False


class ValidationResponse(BaseModel):
    """
    Kết quả business validation
    trước khi lưu nhật ký.
    """

    valid: bool

    errors: list[IssueItem] = Field(
        default_factory=list
    )

    warnings: list[IssueItem] = Field(
        default_factory=list
    )

    # Version của canonical
    # business-rule catalog.
    rule_version: str | None = None

    # Không đồng nghĩa với "có warning".
    # Chỉ True khi có warning cần
    # human acknowledgement.
    requires_confirmation: bool = False

    normalized_data: dict[str, Any]


class SaveLogResponse(BaseModel):
    """Kết quả lưu hoặc cập nhật một nhật ký."""

    success: bool

    status: Literal[
        "saved",
        "already_exists",
        "updated",
    ]

    data: dict[str, Any]

class ListLogsResponse(BaseModel):
    """
    Danh sách nhật ký đã lưu.
    """

    success: bool

    data: list[
        dict[str, Any]
    ]


class GetLogResponse(BaseModel):
    """
    Chi tiết một nhật ký đã lưu.
    """

    success: bool

    data: dict[str, Any]
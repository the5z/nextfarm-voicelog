from typing import Any, Literal

from pydantic import BaseModel, Field


class IssueItem(BaseModel):
    """Một lỗi hoặc cảnh báo liên quan đến dữ liệu nhật ký."""

    field: str
    code: str
    message: str


class ValidationResponse(BaseModel):
    """Kết quả kiểm tra dữ liệu trước khi lưu."""

    valid: bool
    errors: list[IssueItem] = Field(default_factory=list)
    warnings: list[IssueItem] = Field(default_factory=list)
    normalized_data: dict[str, Any]


class SaveLogResponse(BaseModel):
    """Kết quả lưu một nhật ký."""

    success: bool
    status: Literal["saved", "already_exists"]
    data: dict[str, Any]


class ListLogsResponse(BaseModel):
    """Danh sách nhật ký đã lưu."""

    success: bool
    data: list[dict[str, Any]]
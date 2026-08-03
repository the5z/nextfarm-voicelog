from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class NextFarmSubmitResponse(BaseModel):
    """
    Kết quả gửi một nhật ký đã lưu sang NextFarm.
    """

    success: bool = Field(
        description="Kết quả chung của thao tác gửi",
    )

    client_record_id: str = Field(
        description="Mã bản ghi do thiết bị tạo",
    )

    mode: Literal["mock", "live"] = Field(
        description="Chế độ tích hợp NextFarm",
    )

    status: str = Field(
        description="Trạng thái NextFarm trả về",
    )

    status_code: int = Field(
        description="Mã trạng thái từ NextFarm hoặc mock",
    )

    mapped_payload: dict[str, Any] = Field(
        description=(
            "JSON sau khi chuyển từ định dạng nội bộ "
            "sang định dạng NextFarm"
        ),
    )

    nextfarm_response: dict[str, Any] = Field(
        description="Phản hồi đầy đủ từ NextFarm client",
    )
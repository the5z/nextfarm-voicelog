from typing import Optional

from pydantic import BaseModel, Field


class MaterialData(BaseModel):
    """
    Dữ liệu vật tư được AI trích xuất từ câu nói.
    """

    material_text: Optional[str] = Field(
        default=None,
        description=(
            "Tên vật tư dạng dễ hiểu, "
            "ví dụ: NPK, Nước, Cám."
        ),
    )

    quantity: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "Số lượng vật tư được sử dụng."
        ),
    )

    unit_text: Optional[str] = Field(
        default=None,
        description=(
            "Đơn vị dạng văn bản, "
            "ví dụ: kg, lít, ml, bao, chai."
        ),
    )


class ActivityData(BaseModel):
    """
    Dữ liệu nhật ký nông nghiệp được AI trích xuất
    từ bản ghi âm.

    Contract này chỉ chứa dữ liệu dạng text dễ hiểu.
    Việc resolve sang business code vẫn do
    Integration Service xử lý.
    """

    activity_text: Optional[str] = Field(
        default=None,
        description=(
            "Tên hoạt động dạng dễ hiểu, ví dụ: "
            "Bón phân, Phun thuốc, Tưới nước, "
            "Làm cỏ, Thu hoạch."
        ),
    )

    lot_text: Optional[str] = Field(
        default=None,
        description=(
            "Tên hoặc mã lô dạng văn bản, "
            "ví dụ: Lô A, Lô B."
        ),
    )

    materials: list[MaterialData] = Field(
        default_factory=list,
        description=(
            "Danh sách vật tư, số lượng "
            "và đơn vị được sử dụng."
        ),
    )

    time_text: Optional[str] = Field(
        default=None,
        description=(
            "Thời gian dạng HH:MM, "
            "ví dụ: 07:00."
        ),
    )

    missing_fields: list[str] = Field(
        default_factory=list,
        description=(
            "Danh sách các trường còn thiếu "
            "hoặc chưa đủ thông tin."
        ),
    )

    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Các cảnh báo về dữ liệu "
            "không rõ ràng hoặc chưa chắc chắn."
        ),
    )

    requires_confirmation: bool = Field(
        default=False,
        description=(
            "True khi cần người dùng xác nhận "
            "hoặc bổ sung thông tin trước khi "
            "tiếp tục xử lý nghiệp vụ."
        ),
    )
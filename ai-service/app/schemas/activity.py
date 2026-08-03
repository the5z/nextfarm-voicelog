from typing import Optional

from pydantic import BaseModel, Field


class ActivityData(BaseModel):
    """
    Dữ liệu công việc nông nghiệp được AI trích xuất từ bản ghi âm.

    Khớp với giao diện:
    - Lô
    - Công việc
    - Vật tư
    - Số lượng
    - Đơn vị
    - Thời gian
    """

    lot: Optional[str] = Field(
        default=None,
        description="Tên hoặc mã lô, ví dụ: Lô A, Lô B.",
    )

    work: Optional[str] = Field(
        default=None,
        description=(
            "Công việc được thực hiện, ví dụ: "
            "Cho bò ăn, tưới cây xoài, bón phân."
        ),
    )

    material: Optional[str] = Field(
        default=None,
        description=(
            "Vật tư sử dụng, ví dụ: "
            "Cám, nước, phân NPK, thuốc bảo vệ thực vật."
        ),
    )

    quantity: Optional[float] = Field(
        default=None,
        ge=0,
        description="Số lượng vật tư được sử dụng.",
    )

    unit: Optional[str] = Field(
        default=None,
        description=(
            "Đơn vị chuẩn hóa: kg, g, liter, ml, "
            "bag, bottle, piece hoặc other."
        ),
    )

    time: Optional[str] = Field(
        default=None,
        description="Thời gian thực hiện theo định dạng HH:MM.",
    )
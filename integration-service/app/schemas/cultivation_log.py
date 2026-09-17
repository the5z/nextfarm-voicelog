from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.schemas.nextfarm import NextFarmContext

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


WorkLogResultStatus = Literal[
    "completed",
    "partial",
    "failed",
]


class MaterialInput(BaseModel):
    material_code: str = Field(
        min_length=1,
        max_length=50,
    )

    quantity: Decimal = Field(
        gt=0
    )

    unit_code: str = Field(
        min_length=1,
        max_length=20,
    )

    @field_validator(
        "material_code",
        "unit_code",
        mode="before",
    )
    @classmethod
    def normalize_material_codes(
        cls,
        value: object,
    ) -> object:
        """
        Chỉ normalize canonical code.

        Không kiểm tra code có tồn tại
        trong master data tại schema layer.

        Membership validation thuộc
        Business Validation Service.
        """

        if isinstance(
            value,
            str,
        ):
            return (
                value
                .strip()
                .upper()
            )

        return value


class CultivationLogInput(BaseModel):
    schema_version: Literal[
        "1.0"
    ] = "1.0"

    client_record_id: str = Field(
        min_length=1,
        max_length=100,
    )

    transcript: str | None = None

    result_status: WorkLogResultStatus | None = None

    # Context NextFarm được lưu riêng, không suy diễn từ lot/activity.
    # Optional để không phá các record cũ; live submit sẽ yêu cầu đầy đủ.
    context: NextFarmContext | None = None

    lot_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    activity_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    materials: list[
        MaterialInput
    ] = Field(
        default_factory=list
    )

    performed_at: datetime

    performer_code: str | None = None

    material_batch_text: str | None = None

    notes: str | None = None

    source: Literal[
        "voice",
        "manual",
        "sync",
    ] = "voice"

    confirmed: bool = False

    @field_validator(
        "lot_code",
        "activity_code",
        mode="before",
    )
    @classmethod
    def normalize_codes(
        cls,
        value: object,
    ) -> object:
        """
        Normalize code trước khi
        Pydantic kiểm tra length.

        Việc code có tồn tại trong
        master data hay không do
        Business Validation Service
        quyết định.
        """

        if isinstance(
            value,
            str,
        ):
            return (
                value
                .strip()
                .upper()
            )

        return value
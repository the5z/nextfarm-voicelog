from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ALLOWED_UNITS = {"KG", "G", "L", "ML", "BAG", "BOTTLE"}


class MaterialInput(BaseModel):
    material_code: str = Field(min_length=1, max_length=50)
    quantity: Decimal = Field(gt=0)
    unit_code: str = Field(min_length=1, max_length=20)

    @field_validator("material_code")
    @classmethod
    def normalize_material_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("unit_code")
    @classmethod
    def validate_unit_code(cls, value: str) -> str:
        normalized = value.strip().upper()

        if normalized not in ALLOWED_UNITS:
            raise ValueError(
                f"Đơn vị không hợp lệ. Đơn vị hỗ trợ: {sorted(ALLOWED_UNITS)}"
            )

        return normalized
class CultivationLogInput(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    client_record_id: str = Field(min_length=1, max_length=100)

    transcript: str | None = None
    lot_code: str = Field(min_length=1, max_length=50)
    activity_code: str = Field(min_length=1, max_length=50)
    materials: list[MaterialInput] = []

    performed_at: datetime
    performer_code: str | None = None
    notes: str | None = None
    source: Literal["voice", "manual", "sync"] = "voice"
    confirmed: bool = False

    @field_validator("lot_code", "activity_code")
    @classmethod
    def normalize_codes(cls, value: str) -> str:
        return value.strip().upper()
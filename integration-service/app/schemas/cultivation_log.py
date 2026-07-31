from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class MaterialInput(BaseModel):
    material_code: str = Field(min_length=1, max_length=50)
    quantity: Decimal = Field(gt=0)
    unit_code: str = Field(min_length=1, max_length=20)

    @field_validator("material_code", "unit_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()


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
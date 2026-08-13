from typing import Literal

from pydantic import BaseModel, Field


MasterDataType = Literal[
    "activity",
    "unit",
    "lot",
    "material",
]

MatchType = Literal[
    "exact",
    "alias",
    "fuzzy",
    "ambiguous",
    "none",
]


class MasterDataItem(BaseModel):
    code: str
    name: str
    aliases: list[str] = Field(default_factory=list)


class ResolveMasterDataRequest(BaseModel):
    data_type: MasterDataType
    text: str = Field(
        min_length=1,
        max_length=200,
    )


class ResolveMasterDataResponse(BaseModel):
    matched: bool
    code: str | None = None
    name: str | None = None

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    match_type: MatchType

    # Cụm từ trong master data/alias mà resolver đã match vào.
    matched_text: str | None = None

    requires_confirmation: bool

    # Text đầu vào sau khi normalize.
    normalized_text: str

    message: str


class ResolveCultivationMaterialInput(BaseModel):
    material_text: str | None = Field(
        default=None,
        max_length=200,
    )

    quantity: float | None = Field(
        default=None,
        gt=0,
    )

    unit_text: str | None = Field(
        default=None,
        max_length=100,
    )


class ResolveCultivationRequest(BaseModel):
    activity_text: str | None = Field(
        default=None,
        max_length=200,
    )

    lot_text: str | None = Field(
        default=None,
        max_length=200,
    )

    materials: list[ResolveCultivationMaterialInput] = Field(
        default_factory=list
    )

    # Integration không tự đổi time_text thành performed_at.
    # Flutter/user vẫn phải xác nhận thời gian sau cùng.
    time_text: str | None = Field(
        default=None,
        max_length=100,
    )


class ResolvedCultivationMaterial(BaseModel):
    material: ResolveMasterDataResponse
    quantity: float | None = None
    unit: ResolveMasterDataResponse


class ResolveCultivationResponse(BaseModel):
    activity: ResolveMasterDataResponse
    lot: ResolveMasterDataResponse

    materials: list[ResolvedCultivationMaterial] = Field(
        default_factory=list
    )

    # Giữ lại để Flutter hiển thị/xác nhận.
    time_text: str | None = None

    # True nếu có ít nhất một field cần người dùng xác nhận.
    requires_confirmation: bool
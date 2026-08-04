from typing import Literal

from pydantic import BaseModel, Field


MasterDataType = Literal[
    "activity",
    "unit",
    "lot",
    "material",
]


class MasterDataItem(BaseModel):
    code: str
    name: str
    aliases: list[str]


class ResolveMasterDataRequest(BaseModel):
    data_type: MasterDataType
    text: str = Field(
        min_length=1,
        max_length=100,
        description="Từ hoặc cụm từ cần chuẩn hóa",
    )


class ResolveMasterDataResponse(BaseModel):
    matched: bool
    code: str | None
    name: str | None
    confidence: float = Field(
        ge=0,
        le=1,
    )
    requires_confirmation: bool
    normalized_text: str
    message: str
from typing import Literal

from pydantic import BaseModel, Field


RegionMatchType = Literal[
    "exact",
    "alias",
    "fuzzy",
    "none",
]


class RegionMasterDataItem(BaseModel):
    region_id: str = Field(
        min_length=1,
        max_length=100,
    )

    name: str = Field(
        min_length=1,
        max_length=200,
    )

    aliases: list[str] = Field(
        default_factory=list,
    )


class ResolveRegionRequest(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=200,
    )


class ResolveRegionResponse(BaseModel):
    matched: bool

    region_id: str | None = None
    name: str | None = None

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    match_type: RegionMatchType

    matched_text: str | None = None

    requires_confirmation: bool

    normalized_text: str

    message: str
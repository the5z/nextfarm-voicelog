from typing import Literal

from pydantic import BaseModel, Field, field_validator


SeasonMatchType = Literal[
    "exact",
    "alias",
    "fuzzy",
    "none",
]


class SeasonMasterDataItem(BaseModel):
    season_id: str = Field(
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

    @field_validator(
        "season_id",
        "name",
        mode="before",
    )
    @classmethod
    def strip_required_text(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator("aliases")
    @classmethod
    def strip_aliases(
        cls,
        value: list[str],
    ) -> list[str]:
        return [
            alias.strip()
            for alias in value
            if alias.strip()
        ]


class ResolveSeasonRequest(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=200,
    )

    @field_validator(
        "text",
        mode="before",
    )
    @classmethod
    def strip_text(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            return value.strip()

        return value


class ResolveSeasonResponse(BaseModel):
    matched: bool

    season_id: str | None = None

    name: str | None = None

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    match_type: SeasonMatchType

    matched_text: str | None = None

    requires_confirmation: bool

    normalized_text: str

    message: str
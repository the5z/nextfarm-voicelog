from typing import Any, Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class PlotCreateRequest(BaseModel):
    client_record_id: str = Field(
        min_length=1,
        max_length=100,
    )

    plot_name_or_code: str = Field(
        min_length=1,
        max_length=200,
    )

    region_text: str = Field(
        min_length=1,
        max_length=200,
    )

    boundary_required: bool

    owner_text: str | None = None

    current_crop_text: str | None = None

    location_hint_text: str | None = None

    confirmed: bool = False

    @field_validator(
        "client_record_id",
        "plot_name_or_code",
        "region_text",
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

    @field_validator(
        "owner_text",
        "current_crop_text",
        "location_hint_text",
        mode="before",
    )
    @classmethod
    def strip_optional_text(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            value = value.strip()

            if not value:
                return None

        return value


class PlotInput(BaseModel):
    client_record_id: str
    plot_name_or_code: str
    region_id: str
    boundary_required: bool

    owner_text: str | None = None
    current_crop_id: str | None = None
    location_hint_text: str | None = None

    confirmed: bool = False


class PlotSaveResponse(BaseModel):
    success: bool

    status: Literal[
        "saved",
        "already_exists",
        "updated",
    ]

    data: dict[str, Any]


class PlotGetResponse(BaseModel):
    success: bool
    data: dict[str, Any]


class PlotListResponse(BaseModel):
    success: bool
    data: list[dict[str, Any]]
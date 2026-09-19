from typing import Any, Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class SeasonCreateRequest(BaseModel):
    client_record_id: str = Field(
        min_length=1,
        max_length=100,
    )

    plot_text: str = Field(
        min_length=1,
        max_length=200,
    )

    crop_text: str = Field(
        min_length=1,
        max_length=200,
    )

    planting_date_text: str = Field(
        min_length=1,
        max_length=100,
    )

    season_name: str = Field(
        min_length=1,
        max_length=200,
    )

    expected_harvest_date_text: (
        str | None
    ) = None

    plant_count: int | None = Field(
        default=None,
        gt=0,
    )

    expected_yield: float | None = Field(
        default=None,
        gt=0,
    )

    expected_yield_unit_text: (
        str | None
    ) = None

    process_template_text: (
        str | None
    ) = None

    confirmed: bool = False

    @field_validator(
        "client_record_id",
        "plot_text",
        "crop_text",
        "planting_date_text",
        "season_name",
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
        "expected_harvest_date_text",
        "expected_yield_unit_text",
        "process_template_text",
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


class SeasonInput(BaseModel):
    client_record_id: str

    plot_code: str
    crop_id: str

    planting_date_text: str
    season_name: str

    expected_harvest_date_text: (
        str | None
    ) = None

    plant_count: int | None = None

    expected_yield: float | None = None

    expected_yield_unit_code: (
        str | None
    ) = None

    process_template_text: (
        str | None
    ) = None

    confirmed: bool = False


class SeasonSaveResponse(BaseModel):
    success: bool

    status: Literal[
        "saved",
        "already_exists",
        "updated",
    ]

    data: dict[str, Any]


class SeasonGetResponse(BaseModel):
    success: bool
    data: dict[str, Any]


class SeasonListResponse(BaseModel):
    success: bool
    data: list[dict[str, Any]]
from typing import Any, Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class HarvestCreateRequest(BaseModel):
    """
    Structured data đầu vào của CREATE_HARVEST.

    Integration không đọc transcript
    và không thực hiện AI extraction.
    """

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

    quantity: float = Field(
        gt=0,
    )

    unit_text: str = Field(
        min_length=1,
        max_length=100,
    )

    harvest_date_text: str = Field(
        min_length=1,
        max_length=100,
    )

    photo: str | None = None

    note: str | None = None

    confirmed: bool = False

    @field_validator(
        "client_record_id",
        "plot_text",
        "crop_text",
        "unit_text",
        "harvest_date_text",
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
        "photo",
        "note",
        mode="before",
    )
    @classmethod
    def strip_optional_text(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            normalized = value.strip()

            if not normalized:
                return None

            return normalized

        return value


class HarvestInput(BaseModel):
    """
    Dữ liệu canonical sau khi Integration
    đã resolve và validate.
    """

    client_record_id: str = Field(
        min_length=1,
        max_length=100,
    )

    plot_code: str = Field(
        min_length=1,
        max_length=50,
    )

    crop_id: str = Field(
        min_length=1,
        max_length=100,
    )

    quantity: float = Field(
        gt=0,
    )

    unit_code: str = Field(
        min_length=1,
        max_length=20,
    )

    harvest_date_text: str = Field(
        min_length=1,
        max_length=100,
    )

    photo: str | None = None

    note: str | None = None

    confirmed: bool = False

    @field_validator(
        "plot_code",
        "unit_code",
        mode="before",
    )
    @classmethod
    def normalize_code(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            return (
                value
                .strip()
                .upper()
            )

        return value


class HarvestSaveResponse(BaseModel):
    success: bool

    status: Literal[
        "saved",
        "already_exists",
        "updated",
    ]

    data: dict[str, Any]


class HarvestGetResponse(BaseModel):
    success: bool

    data: dict[str, Any]


class HarvestListResponse(BaseModel):
    success: bool

    data: list[
        dict[str, Any]
    ]
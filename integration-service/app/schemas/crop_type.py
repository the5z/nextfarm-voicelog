from typing import Any, Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class CropTypeCreateRequest(BaseModel):
    client_record_id: str = Field(
        min_length=1,
        max_length=100,
    )

    crop_name: str = Field(
        min_length=1,
        max_length=200,
    )

    crop_group_text: str = Field(
        min_length=1,
        max_length=200,
    )

    crop_code_suggestion: str = Field(
        min_length=1,
        max_length=200,
    )

    days_to_harvest: int | None = Field(
        default=None,
        gt=0,
    )

    confirmed: bool = False

    @field_validator(
        "client_record_id",
        "crop_name",
        "crop_group_text",
        "crop_code_suggestion",
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


class CropTypeInput(BaseModel):
    client_record_id: str = Field(
        min_length=1,
        max_length=100,
    )

    crop_name: str = Field(
        min_length=1,
        max_length=200,
    )

    crop_group_text: str = Field(
        min_length=1,
        max_length=200,
    )

    crop_code_suggestion: str = Field(
        min_length=1,
        max_length=200,
    )

    days_to_harvest: int | None = Field(
        default=None,
        gt=0,
    )

    confirmed: bool = False


class CropTypeSaveResponse(BaseModel):
    success: bool

    status: Literal[
        "saved",
        "already_exists",
        "updated",
    ]

    data: dict[str, Any]


class CropTypeGetResponse(BaseModel):
    success: bool
    data: dict[str, Any]


class CropTypeListResponse(BaseModel):
    success: bool
    data: list[dict[str, Any]]
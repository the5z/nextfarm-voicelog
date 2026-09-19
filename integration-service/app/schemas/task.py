from typing import Any, Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class TaskCreateRequest(BaseModel):
    client_record_id: str = Field(
        min_length=1,
        max_length=100,
    )

    season_text: str = Field(
        min_length=1,
        max_length=200,
    )

    task_name: str = Field(
        min_length=1,
        max_length=200,
    )

    task_type_text: str = Field(
        min_length=1,
        max_length=200,
    )

    due_time_text: str = Field(
        min_length=1,
        max_length=100,
    )

    assignee_text: str | None = Field(
        default=None,
        max_length=200,
    )

    photo_required: bool | None = None

    note: str | None = None

    confirmed: bool = False

    @field_validator(
        "client_record_id",
        "season_text",
        "task_name",
        "task_type_text",
        "due_time_text",
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
        "assignee_text",
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


class TaskInput(BaseModel):
    client_record_id: str = Field(
        min_length=1,
        max_length=100,
    )

    season_id: str = Field(
        min_length=1,
        max_length=100,
    )

    task_name: str = Field(
        min_length=1,
        max_length=200,
    )

    task_type_text: str = Field(
        min_length=1,
        max_length=200,
    )

    due_time_text: str = Field(
        min_length=1,
        max_length=100,
    )

    assignee_text: str | None = Field(
        default=None,
        max_length=200,
    )

    photo_required: bool | None = None

    note: str | None = None

    confirmed: bool = False


class TaskSaveResponse(BaseModel):
    success: bool

    status: Literal[
        "saved",
        "already_exists",
        "updated",
    ]

    data: dict[str, Any]


class TaskGetResponse(BaseModel):
    success: bool
    data: dict[str, Any]


class TaskListResponse(BaseModel):
    success: bool
    data: list[dict[str, Any]]
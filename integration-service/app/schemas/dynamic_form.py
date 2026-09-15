from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


WorkLogResultStatus = Literal[
    "completed",
    "partial",
    "failed",
]


WarningCode = Literal[
    "AMBIGUOUS_UNIT",
    "LOW_CONFIDENCE",
    "UNKNOWN_MASTER_DATA",
    "CONFLICTING_VALUE",
    "INVALID_FORMAT",
    "BUSINESS_RULE_WARNING",
    "NAME_NOT_MATCHED",
]


class DynamicFormWarning(BaseModel):
    field: str = Field(
        min_length=1,
    )

    code: WarningCode

    message: str = Field(
        min_length=1,
    )


class DynamicWorkLogMaterial(BaseModel):
    material_text: str | None = None

    quantity: Decimal | None = Field(
        default=None,
        gt=0,
    )

    unit_text: str | None = None


class DynamicWorkLogFields(BaseModel):
    result_status: WorkLogResultStatus

    plot_text: str | None = None

    activity_text: str | None = None

    performed_time_text: str | None = None

    materials: list[
        DynamicWorkLogMaterial
    ] = Field(
        default_factory=list,
    )

    photo_required: bool = False

    material_batch_text: str | None = None

    note: str | None = None


class DynamicCreateWorkLogResponse(BaseModel):
    contract_version: Literal[
        "3.1"
    ] = "3.1"

    operation: Literal[
        "CREATE_WORK_LOG"
    ] = "CREATE_WORK_LOG"

    template_id: Literal[
        "work_log"
    ] = "work_log"

    fields: DynamicWorkLogFields

    missing_fields: list[str] = Field(
        default_factory=list,
    )

    warnings: list[
        DynamicFormWarning
    ] = Field(
        default_factory=list,
    )

    field_confidence: dict[
        str,
        float,
    ] = Field(
        default_factory=dict,
    )

    requires_confirmation: bool = False

    next_question: str | None = None
class DynamicFormContext(BaseModel):
    current_plot_text: str | None = None

    current_season_text: str | None = None

    current_crop_text: str | None = None

    today: str | None = None


class DynamicCreateWorkLogRequest(BaseModel):
    contract_version: Literal[
        "3.1"
    ] = "3.1"

    operation: Literal[
        "CREATE_WORK_LOG"
    ]

    template_id: Literal[
        "work_log"
    ]

    transcript: str | None = None

    current_fields: DynamicWorkLogFields | None = None

    context: DynamicFormContext = Field(
        default_factory=DynamicFormContext,
    )
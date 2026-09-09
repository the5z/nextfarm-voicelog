from typing import Literal

from pydantic import BaseModel, Field


OperationType = Literal[
    "CREATE_CROP_TYPE",
    "CREATE_SEASON",
    "CREATE_PLOT",
    "CREATE_TASK",
    "CREATE_WORK_LOG",
    "CREATE_ISSUE_REPORT",
    "CREATE_HARVEST",
]


class DynamicFormWarning(BaseModel):
    field: str | None = None
    code: str
    message: str


class MaterialData(BaseModel):
    material_text: str | None = None
    quantity: float | None = Field(default=None, gt=0)
    unit_text: str | None = None


class CropTypeFields(BaseModel):
    crop_name: str | None = None
    crop_group_text: str | None = None
    crop_code_suggestion: str | None = None
    days_to_harvest: int | None = Field(default=None, gt=0)


class SeasonFields(BaseModel):
    plot_text: str | None = None
    crop_text: str | None = None
    planting_date_text: str | None = None
    season_name: str | None = None

    expected_harvest_date_text: str | None = None
    plant_count: int | None = Field(default=None, gt=0)
    expected_yield: float | None = Field(default=None, gt=0)
    expected_yield_unit_text: str | None = None
    process_template_text: str | None = None


class PlotFields(BaseModel):
    plot_name_or_code: str | None = None
    region_text: str | None = None
    boundary_required: bool | None = None

    owner_text: str | None = None
    current_crop_text: str | None = None
    location_hint_text: str | None = None


class TaskFields(BaseModel):
    season_text: str | None = None
    task_name: str | None = None
    task_type_text: str | None = None
    due_time_text: str | None = None

    assignee_text: str | None = None
    photo_required: bool | None = None
    note: str | None = None


class WorkLogFields(BaseModel):
    result_status: Literal[
        "completed",
        "partial",
        "failed",
    ] | None = None

    plot_text: str | None = None
    activity_text: str | None = None
    performed_time_text: str | None = None

    materials: list[MaterialData] = Field(default_factory=list)

    photo_required: bool | None = None
    material_batch_text: str | None = None
    note: str | None = None


class IssueReportFields(BaseModel):
    plot_text: str | None = None
    issue_type_text: str | None = None
    severity_text: str | None = None
    description: str | None = None

    photo_required: bool | None = None
    note: str | None = None


class HarvestFields(BaseModel):
    plot_text: str | None = None
    crop_text: str | None = None
    quantity: float | None = Field(default=None, gt=0)
    unit_text: str | None = None
    harvest_date_text: str | None = None

    photo_required: bool | None = None
    note: str | None = None


class BaseDynamicFormResponse(BaseModel):
    contract_version: Literal["3.1"] = "3.1"

    missing_fields: list[str] = Field(default_factory=list)

    warnings: list[DynamicFormWarning] = Field(
        default_factory=list
    )

    field_confidence: dict[str, float | None] = Field(
        default_factory=dict
    )

    requires_confirmation: bool = False

    next_question: str | None = None


class CropTypeResponse(BaseDynamicFormResponse):
    operation: Literal["CREATE_CROP_TYPE"] = "CREATE_CROP_TYPE"
    template_id: Literal["crop_type"] = "crop_type"
    fields: CropTypeFields = Field(default_factory=CropTypeFields)


class SeasonResponse(BaseDynamicFormResponse):
    operation: Literal["CREATE_SEASON"] = "CREATE_SEASON"
    template_id: Literal["season"] = "season"
    fields: SeasonFields = Field(default_factory=SeasonFields)


class PlotResponse(BaseDynamicFormResponse):
    operation: Literal["CREATE_PLOT"] = "CREATE_PLOT"
    template_id: Literal["plot"] = "plot"
    fields: PlotFields = Field(default_factory=PlotFields)


class TaskResponse(BaseDynamicFormResponse):
    operation: Literal["CREATE_TASK"] = "CREATE_TASK"
    template_id: Literal["task"] = "task"
    fields: TaskFields = Field(default_factory=TaskFields)


class WorkLogResponse(BaseDynamicFormResponse):
    operation: Literal["CREATE_WORK_LOG"] = "CREATE_WORK_LOG"
    template_id: Literal["work_log"] = "work_log"
    fields: WorkLogFields = Field(default_factory=WorkLogFields)


class IssueReportResponse(BaseDynamicFormResponse):
    operation: Literal[
        "CREATE_ISSUE_REPORT"
    ] = "CREATE_ISSUE_REPORT"

    template_id: Literal["issue_report"] = "issue_report"

    fields: IssueReportFields = Field(
        default_factory=IssueReportFields
    )


class HarvestResponse(BaseDynamicFormResponse):
    operation: Literal["CREATE_HARVEST"] = "CREATE_HARVEST"
    template_id: Literal["harvest"] = "harvest"
    fields: HarvestFields = Field(default_factory=HarvestFields)


DynamicFormResponse = (
    CropTypeResponse
    | SeasonResponse
    | PlotResponse
    | TaskResponse
    | WorkLogResponse
    | IssueReportResponse
    | HarvestResponse
)


RESPONSE_MODEL_BY_OPERATION = {
    "CREATE_CROP_TYPE": CropTypeResponse,
    "CREATE_SEASON": SeasonResponse,
    "CREATE_PLOT": PlotResponse,
    "CREATE_TASK": TaskResponse,
    "CREATE_WORK_LOG": WorkLogResponse,
    "CREATE_ISSUE_REPORT": IssueReportResponse,
    "CREATE_HARVEST": HarvestResponse,
}
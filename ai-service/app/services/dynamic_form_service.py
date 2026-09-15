import json
from typing import Any

from google import genai
from google.genai.errors import APIError

from app.core.config import settings
from app.prompts.dynamic_form_prompt import build_dynamic_form_prompt
from app.schemas.dynamic_form import (
    DynamicFormResponse,
    RESPONSE_MODEL_BY_OPERATION,
)


client = genai.Client(api_key=settings.GEMINI_API_KEY)


REQUIRED_FIELDS_BY_OPERATION: dict[str, list[str]] = {
    "CREATE_CROP_TYPE": [
        "crop_name",
        "crop_group_text",
        "crop_code_suggestion",
    ],
    "CREATE_SEASON": [
        "plot_text",
        "crop_text",
        "planting_date_text",
        "season_name",
    ],
    "CREATE_PLOT": [
        "plot_name_or_code",
        "region_text",
        "boundary_required",
    ],
    "CREATE_TASK": [
        "season_text",
        "task_name",
        "task_type_text",
        "due_time_text",
    ],
    "CREATE_WORK_LOG": [
        "result_status",
    ],
    "CREATE_ISSUE_REPORT": [
        "plot_text",
        "issue_type_text",
        "severity_text",
        "description",
    ],
    "CREATE_HARVEST": [
        "plot_text",
        "crop_text",
        "quantity",
        "unit_text",
        "harvest_date_text",
    ],
}


QUESTION_BY_FIELD: dict[str, dict[str, str]] = {
    "CREATE_CROP_TYPE": {
        "crop_name": (
            "Tên loại cây trồng là gì?"
        ),
        "crop_group_text": (
            "Loại cây trồng này thuộc nhóm nào?"
        ),
        "crop_code_suggestion": (
            "Mã gợi ý cho loại cây trồng này là gì?"
        ),
    },
    "CREATE_SEASON": {
        "plot_text": (
            "Vụ này thuộc lô nào?"
        ),
        "crop_text": (
            "Vụ này trồng cây gì?"
        ),
        "planting_date_text": (
            "Ngày gieo trồng hoặc xuống giống là ngày nào?"
        ),
        "season_name": (
            "Tên vụ là gì?"
        ),
    },
    "CREATE_PLOT": {
        "plot_name_or_code": (
            "Tên hoặc mã lô là gì?"
        ),
        "region_text": (
            "Lô này thuộc khu vực nào?"
        ),
        "boundary_required": (
            "Bạn cần vẽ ranh giới lô trên bản đồ để tiếp tục."
        ),
    },
    "CREATE_TASK": {
        "season_text": (
            "Công việc này thuộc vụ nào?"
        ),
        "task_name": (
            "Tên công việc là gì?"
        ),
        "task_type_text": (
            "Loại công việc là gì?"
        ),
        "due_time_text": (
            "Hạn hoàn thành công việc là khi nào?"
        ),
    },
    "CREATE_WORK_LOG": {
        "result_status": (
            "Kết quả công việc là đã hoàn thành, "
            "hoàn thành một phần hay thất bại?"
        ),
    },
    "CREATE_ISSUE_REPORT": {
        "plot_text": (
            "Sự cố xảy ra ở lô nào?"
        ),
        "issue_type_text": (
            "Loại sự cố hoặc vấn đề là gì?"
        ),
        "severity_text": (
            "Mức độ của vấn đề là nhẹ, trung bình hay nặng?"
        ),
        "description": (
            "Bạn mô tả tình trạng hiện tại như thế nào?"
        ),
    },
    "CREATE_HARVEST": {
        "plot_text": (
            "Thu hoạch ở lô nào?"
        ),
        "crop_text": (
            "Bạn thu hoạch loại cây gì?"
        ),
        "quantity": (
            "Số lượng thu hoạch là bao nhiêu?"
        ),
        "unit_text": (
            "Đơn vị của số lượng thu hoạch là gì?"
        ),
        "harvest_date_text": (
            "Ngày thu hoạch là ngày nào?"
        ),
    },
}


def _is_missing(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    return False


def _build_next_question(
    operation: str,
    missing_fields: list[str],
) -> str | None:
    """
    Build exactly one logical follow-up question.

    The backend, not Gemini, controls which missing
    information is requested next.
    """

    if not missing_fields:
        return None

    first_missing = missing_fields[0]

    # ---------------------------------------------------------
    # Work log material fields
    # ---------------------------------------------------------
    if (
        operation == "CREATE_WORK_LOG"
        and first_missing.startswith("materials[")
    ):
        if first_missing.endswith(".material_text"):
            return (
                "Bạn đã sử dụng vật tư gì?"
            )

        if first_missing.endswith(".quantity"):
            unit_field = first_missing.replace(
                ".quantity",
                ".unit_text",
            )

            if unit_field in missing_fields:
                return (
                    "Bạn đã sử dụng vật tư này với "
                    "số lượng và đơn vị bao nhiêu?"
                )

            return (
                "Bạn đã sử dụng số lượng bao nhiêu?"
            )

        if first_missing.endswith(".unit_text"):
            return (
                "Đơn vị của số lượng vật tư là gì?"
            )

    # ---------------------------------------------------------
    # Harvest quantity + unit form one logical group.
    # ---------------------------------------------------------
    if (
        operation == "CREATE_HARVEST"
        and first_missing == "quantity"
        and "unit_text" in missing_fields
    ):
        return (
            "Số lượng thu hoạch và đơn vị là bao nhiêu?"
        )

    questions = QUESTION_BY_FIELD.get(
        operation,
        {},
    )

    return questions.get(
        first_missing,
        "Bạn vui lòng bổ sung thông tin còn thiếu.",
    )


def _normalize_missing_fields(
    operation: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Recalculate missing_fields deterministically.

    Gemini is responsible for extracting values.
    The backend is responsible for making the final response
    internally consistent.
    """

    fields = data.get("fields") or {}
    missing_fields: list[str] = []

    for field_name in REQUIRED_FIELDS_BY_OPERATION.get(
        operation,
        [],
    ):
        if _is_missing(fields.get(field_name)):
            missing_fields.append(field_name)

    # CREATE_WORK_LOG has nested material requirements.
    if operation == "CREATE_WORK_LOG":
        materials = fields.get("materials") or []

        for index, material in enumerate(materials):
            if not isinstance(material, dict):
                continue

            if _is_missing(material.get("material_text")):
                missing_fields.append(
                    f"materials[{index}].material_text"
                )

            if _is_missing(material.get("quantity")):
                missing_fields.append(
                    f"materials[{index}].quantity"
                )

            if _is_missing(material.get("unit_text")):
                missing_fields.append(
                    f"materials[{index}].unit_text"
                )

    data["missing_fields"] = missing_fields

    warnings = data.get("warnings") or []

    if missing_fields:
        data["requires_confirmation"] = True
        data["next_question"] = _build_next_question(
            operation=operation,
            missing_fields=missing_fields,
        )

    elif warnings:
        data["requires_confirmation"] = True
        data["next_question"] = (
            "Có thông tin chưa chắc chắn. "
            "Bạn vui lòng kiểm tra và xác nhận lại."
        )

    else:
        data["requires_confirmation"] = False
        data["next_question"] = None

    return data


def _build_gemini_schema(
    operation: str,
) -> dict[str, Any]:
    response_model = RESPONSE_MODEL_BY_OPERATION[operation]

    schema = response_model.model_json_schema()

    # Gemini Developer API does not support
    # additionalProperties in this usage.
    #
    # field_confidence is represented as a fixed object
    # whose keys are the known fields for the selected operation.
    fields_schema = schema["$defs"]

    template_id = schema["properties"]["template_id"]["const"]

    field_def_name = {
        "crop_type": "CropTypeFields",
        "season": "SeasonFields",
        "plot": "PlotFields",
        "task": "TaskFields",
        "work_log": "WorkLogFields",
        "issue_report": "IssueReportFields",
        "harvest": "HarvestFields",
    }[template_id]

    field_names = list(
        fields_schema[field_def_name]["properties"].keys()
    )

    confidence_properties = {
        field_name: {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        }
        for field_name in field_names
    }

    schema["properties"]["field_confidence"] = {
        "type": "object",
        "properties": confidence_properties,
    }

    def clean_schema(
        value: Any,
    ) -> Any:
        if isinstance(value, dict):
            cleaned: dict[str, Any] = {}

            for key, item in value.items():
                if key == "additionalProperties":
                    continue

                if key in {
                    "title",
                    "default",
                }:
                    continue

                cleaned[key] = clean_schema(item)

            return cleaned

        if isinstance(value, list):
            return [
                clean_schema(item)
                for item in value
            ]

        return value

    return clean_schema(schema)


def extract_dynamic_form(
    operation: str,
    transcript: str,
    current_fields: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> DynamicFormResponse:
    response_model = RESPONSE_MODEL_BY_OPERATION.get(
        operation
    )

    if response_model is None:
        raise ValueError(
            f"Unsupported operation: {operation}"
        )

    prompt = build_dynamic_form_prompt(
        operation=operation,
        transcript=transcript,
        current_fields=current_fields,
        context=context,
    )

    gemini_schema = _build_gemini_schema(
        operation
    )

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": gemini_schema,
                "temperature": 0,
            },
        )

        if not response.text:
            raise ValueError(
                "Gemini returned no structured dynamic form data."
            )

        data = json.loads(
            response.text
        )

        data["contract_version"] = "3.1"

        data = _normalize_missing_fields(
            operation=operation,
            data=data,
        )

        return response_model.model_validate(
            data
        )

    except APIError as exc:
        raise RuntimeError(
            (
                "Gemini API error while extracting "
                f"dynamic form: {exc}"
            )
        ) from exc
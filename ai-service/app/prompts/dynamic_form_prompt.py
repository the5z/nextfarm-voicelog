import json
from typing import Any


OPERATION_RULES: dict[str, dict[str, Any]] = {
    "CREATE_CROP_TYPE": {
        "template_id": "crop_type",
        "required_fields": [
            "crop_name",
            "crop_group_text",
            "crop_code_suggestion",
        ],
        "optional_fields": [
            "days_to_harvest",
        ],
    },
    "CREATE_SEASON": {
        "template_id": "season",
        "required_fields": [
            "plot_text",
            "crop_text",
            "planting_date_text",
            "season_name",
        ],
        "optional_fields": [
            "expected_harvest_date_text",
            "plant_count",
            "expected_yield",
            "expected_yield_unit_text",
            "process_template_text",
        ],
    },
    "CREATE_PLOT": {
        "template_id": "plot",
        "required_fields": [
            "plot_name_or_code",
            "region_text",
            "boundary_required",
        ],
        "optional_fields": [
            "owner_text",
            "current_crop_text",
            "location_hint_text",
        ],
    },
    "CREATE_TASK": {
        "template_id": "task",
        "required_fields": [
            "season_text",
            "task_name",
            "task_type_text",
            "due_time_text",
        ],
        "optional_fields": [
            "assignee_text",
            "photo_required",
            "note",
        ],
    },
    "CREATE_WORK_LOG": {
        "template_id": "work_log",
        "required_fields": [
            "result_status",
        ],
        "optional_fields": [
            "plot_text",
            "activity_text",
            "performed_time_text",
            "materials",
            "photo_required",
            "material_batch_text",
            "note",
        ],
        "special_rules": [
            (
                "If materials are mentioned, each material must contain "
                "material_text, quantity, and unit_text."
            ),
            (
                "result_status must be one of: completed, partial, failed."
            ),
        ],
    },
    "CREATE_ISSUE_REPORT": {
        "template_id": "issue_report",
        "required_fields": [
            "plot_text",
            "issue_type_text",
            "severity_text",
            "description",
        ],
        "optional_fields": [
            "photo_required",
            "note",
        ],
    },
    "CREATE_HARVEST": {
        "template_id": "harvest",
        "required_fields": [
            "plot_text",
            "crop_text",
            "quantity",
            "unit_text",
            "harvest_date_text",
        ],
        "optional_fields": [
            "photo_required",
            "note",
        ],
    },
}


def build_dynamic_form_prompt(
    operation: str,
    transcript: str,
    current_fields: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> str:
    if operation not in OPERATION_RULES:
        raise ValueError(f"Unsupported operation: {operation}")

    rules = OPERATION_RULES[operation]

    current_fields = current_fields or {}
    context = context or {}

    required_fields = rules["required_fields"]
    optional_fields = rules["optional_fields"]
    special_rules = rules.get("special_rules", [])

    return f"""
You are the structured extraction engine for NextFarm VoiceLog.

Your task is to extract information from Vietnamese user speech
for exactly one selected business operation.

SELECTED OPERATION:
{operation}

TEMPLATE:
{rules["template_id"]}

REQUIRED FIELDS:
{json.dumps(required_fields, ensure_ascii=False)}

OPTIONAL FIELDS:
{json.dumps(optional_fields, ensure_ascii=False)}

SPECIAL RULES:
{json.dumps(special_rules, ensure_ascii=False)}

CURRENT FORM DATA:
{json.dumps(current_fields, ensure_ascii=False)}

AVAILABLE CONTEXT:
{json.dumps(context, ensure_ascii=False)}

NEW USER TRANSCRIPT:
{transcript}

STRICT RULES:

1. Only extract fields belonging to the selected operation.

2. Do not change the operation or template.

3. Preserve reliable values already present in CURRENT FORM DATA.

4. Update an existing value only when the new transcript clearly
   provides a correction or replacement.

5. You may use AVAILABLE CONTEXT only when it is clearly relevant.

6. Never invent missing information.

7. Never invent business codes, database IDs, or master-data codes.

8. Keep business values human-readable.
   Examples:
   - "Thửa B3"
   - "Dâu tây"
   - "NPK"
   - "kg"

9. For a required field with no reliable value:
   - leave its value null
   - include its exact field path in missing_fields

10. Optional fields may remain null and must not be placed in
    missing_fields.

11. If a value is ambiguous or unreliable:
    - do not guess
    - add a structured warning
    - set requires_confirmation to true

12. For ambiguous local units such as:
    - xị
    - công
    - sào
    do not automatically convert them unless explicit business
    context provides an unambiguous conversion.

13. For CREATE_WORK_LOG:
    if a material is mentioned, each material item must contain:
    - material_text
    - quantity
    - unit_text

    If one of those values is missing, add the exact nested field
    path to missing_fields, for example:
    materials[0].unit_text

14. For CREATE_WORK_LOG, result_status must be one of:
    - completed
    - partial
    - failed

15. For dates and times:
    preserve a clear human-readable interpretation.
    Do not invent a date when neither the transcript nor context
    supports it.

16. field_confidence must describe confidence for extracted fields.
    Use null for fields with no value.

17. requires_confirmation must be true when:
    - missing_fields is not empty
    - warnings is not empty
    - or an extracted value clearly needs user confirmation

18. next_question:
    - ask about only ONE missing required field
    - prefer the first important missing required field
    - keep the question short and natural in Vietnamese
    - return null if no additional question is required

19. Do not add explanations outside the structured response.

20. The structured response must follow the response schema supplied
    by the application.
""".strip()
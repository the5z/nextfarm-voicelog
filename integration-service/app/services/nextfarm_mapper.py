from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping


ACTIVITY_NAMES: dict[str, str] = {
    "BON_PHAN": "Bón phân",
    "PHUN_THUOC": "Phun thuốc",
    "TUOI_NUOC": "Tưới nước",
    "LAM_CO": "Làm cỏ",
    "THU_HOACH": "Thu hoạch",
}


def format_number(value: Any) -> str:
    """
    Chuyển số lượng thành chuỗi dễ đọc.

    Ví dụ:
        20       -> "20"
        20.0     -> "20"
        20.500   -> "20.5"
        Decimal  -> chuỗi tương ứng
    """

    if isinstance(value, Decimal):
        normalized_value = value.normalize()

        if normalized_value == normalized_value.to_integral():
            return str(int(normalized_value))

        return format(normalized_value, "f").rstrip("0").rstrip(".")

    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))

        return str(value).rstrip("0").rstrip(".")

    return str(value)


def normalize_datetime(value: Any) -> str:
    """
    Chuẩn hóa thời gian thành chuỗi ISO 8601.

    Hàm chấp nhận:
        - datetime
        - chuỗi ISO 8601

    Nếu giá trị không hợp lệ sẽ phát sinh ValueError.
    """

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, str):
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError(
                "performed_at không được để trống"
            )

        try:
            datetime.fromisoformat(
                normalized_value.replace(
                    "Z",
                    "+00:00",
                )
            )
        except ValueError as error:
            raise ValueError(
                "performed_at phải là thời gian ISO 8601 hợp lệ"
            ) from error

        return normalized_value

    raise ValueError(
        "performed_at phải là datetime hoặc chuỗi ISO 8601"
    )


def build_material_description(
    material: Mapping[str, Any],
) -> str:
    """
    Tạo mô tả cho một vật tư.

    Ví dụ:
        NPK - 20 KG
    """

    material_code = str(
        material.get(
            "material_code",
            "",
        )
    ).strip()

    unit_code = str(
        material.get(
            "unit_code",
            "",
        )
    ).strip()

    quantity = material.get("quantity")

    if not material_code:
        material_code = "Vật tư chưa xác định"

    if quantity is None:
        quantity_text = "Chưa rõ số lượng"
    else:
        quantity_text = format_number(quantity)

    parts = [
        material_code,
        quantity_text,
    ]

    if unit_code:
        parts.append(unit_code)

    return " - ".join(parts)


def build_description(
    cultivation_log: Mapping[str, Any],
) -> str:
    """
    Tạo phần mô tả nhật ký gửi sang NextFarm mô phỏng.
    """

    description_parts: list[str] = []

    transcript = cultivation_log.get("transcript")

    if isinstance(transcript, str) and transcript.strip():
        description_parts.append(
            f"Nội dung ghi âm: {transcript.strip()}"
        )

    materials = cultivation_log.get(
        "materials",
        [],
    )

    if isinstance(materials, list) and materials:
        material_lines = [
            build_material_description(material)
            for material in materials
            if isinstance(material, Mapping)
        ]

        if material_lines:
            description_parts.append(
                "Vật tư:\n- "
                + "\n- ".join(material_lines)
            )

    notes = cultivation_log.get("notes")

    if isinstance(notes, str) and notes.strip():
        description_parts.append(
            f"Ghi chú: {notes.strip()}"
        )

    client_record_id = cultivation_log.get(
        "client_record_id"
    )

    if client_record_id:
        description_parts.append(
            f"Mã bản ghi thiết bị: {client_record_id}"
        )

    if not description_parts:
        return "Nhật ký canh tác được tạo từ NextFarm VoiceLog"

    return "\n\n".join(description_parts)


def resolve_mapping_value(
    source_code: str | None,
    mapping: Mapping[str, Any] | None,
) -> Any:
    """Resolve một mã nội bộ sang ID external nếu có mapping.

    Hàm này vẫn giữ fallback cho mock/backward compatibility. Live mode
    phải kiểm tra context và mapping ở service layer trước khi gửi.
    """

    if not source_code:
        return None

    if mapping is None:
        return source_code

    return mapping.get(source_code, source_code)


def map_cultivation_log_to_nextfarm(
    cultivation_log: Mapping[str, Any],
    *,
    activity_mapping: Mapping[str, Any] | None = None,
    lot_mapping: Mapping[str, Any] | None = None,
    performer_mapping: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Chuyển nhật ký nội bộ sang payload NextFarm.

    Context NextFarm được lấy từ ``cultivation_log["context"]``.
    Không suy ra season từ lot hoặc task từ activity.

    Mapping arguments cũ vẫn được giữ cho activity/lot/performer để
    hỗ trợ môi trường mock/test cho tới khi adapter thật có resolver riêng.
    """

    activity_code = str(
        cultivation_log.get("activity_code", "")
    ).strip()
    lot_code = str(
        cultivation_log.get("lot_code", "")
    ).strip()
    performer_value = cultivation_log.get("performer_code")
    performer_code = (
        str(performer_value).strip()
        if performer_value is not None
        else None
    )
    client_record_id = str(
        cultivation_log.get("client_record_id", "")
    ).strip()

    if not client_record_id:
        raise ValueError("Thiếu client_record_id")
    if not activity_code:
        raise ValueError("Thiếu activity_code")
    if not lot_code:
        raise ValueError("Thiếu lot_code")

    performed_at = normalize_datetime(
        cultivation_log.get("performed_at")
    )
    activity_name = ACTIVITY_NAMES.get(
        activity_code,
        activity_code.replace("_", " ").title(),
    )

    context = cultivation_log.get("context")
    if not isinstance(context, Mapping):
        context = None

    location = resolve_mapping_value(lot_code, lot_mapping)
    category_task_id = resolve_mapping_value(
        activity_code, activity_mapping
    )
    assigned_to = resolve_mapping_value(
        performer_code, performer_mapping
    )

    nextfarm_payload: dict[str, Any] = {
        "name": activity_name,
        "start": performed_at,
        "end": performed_at,
        "description": build_description(cultivation_log),
        "images": [],
        "location": (
            context.get("plot_id")
            if context is not None and context.get("plot_id")
            else location
        ),
        "assigned_to": (
            context.get("user_id")
            if context is not None and context.get("user_id")
            else assigned_to
        ),
        "category_task_id": (
            context.get("task_id")
            if context is not None and context.get("task_id")
            else category_task_id
        ),
        "season_id": (
            context.get("season_id")
            if context is not None
            else None
        ),
        "metadata": {
            "schema_version": cultivation_log.get("schema_version", "1.0"),
            "client_record_id": client_record_id,
            "source": cultivation_log.get("source", "voice"),
            "integration_source": "nextfarm-voicelog",
            "tenant_id": (
                context.get("tenant_id")
                if context is not None
                else None
            ),
            "context": dict(context) if context is not None else None,
        },
    }

    return nextfarm_payload
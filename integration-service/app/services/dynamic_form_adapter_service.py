from __future__ import annotations

from datetime import datetime
from typing import Literal

from app.schemas.cultivation_log import (
    CultivationLogInput,
    MaterialInput,
)
from app.schemas.dynamic_form import (
    DynamicCreateWorkLogRequest,
)
from app.schemas.nextfarm import (
    NextFarmContext,
)
from app.services.normalization_service import (
    resolve_master_data,
)


ResolutionCode = Literal[
    "MISSING_REQUIRED_FIELD",
    "NAME_NOT_MATCHED",
    "UNKNOWN_MASTER_DATA",
    "AMBIGUOUS_UNIT",
]


class DynamicFormCanonicalResolutionError(
    ValueError
):
    """
    Lỗi khi Integration không thể chuyển
    human-readable text (text người đọc được)
    thành canonical code (mã chuẩn).

    Đây là lỗi của Integration resolution
    (đối chiếu dữ liệu), không phải AI extraction
    (trích xuất AI).
    """

    def __init__(
        self,
        *,
        field: str,
        code: ResolutionCode,
        message: str,
    ) -> None:
        super().__init__(message)

        self.field = field
        self.code = code
        self.message = message


def _resolve_required_code(
    *,
    data_type: str,
    value: str | None,
    field: str,
) -> str:
    """
    Resolve text thành canonical code.

    Không đọc transcript.
    Không tự đoán.
    Không fallback sang field khác.
    """

    normalized_value = str(
        value or ""
    ).strip()

    if not normalized_value:
        raise DynamicFormCanonicalResolutionError(
            field=field,
            code="MISSING_REQUIRED_FIELD",
            message=(
                f"Thiếu giá trị bắt buộc "
                f"cho '{field}'."
            ),
        )

    result = resolve_master_data(
        data_type,
        normalized_value,
    )

    match_type = result.get(
        "match_type"
    )

    # Đơn vị mơ hồ như "xị" không được
    # tự động chuyển sang một unit code.
    if (
        data_type == "unit"
        and match_type == "ambiguous"
    ):
        raise DynamicFormCanonicalResolutionError(
            field=field,
            code="AMBIGUOUS_UNIT",
            message=(
                f"Đơn vị '{normalized_value}' "
                "còn mơ hồ và chưa thể "
                "chuyển thành mã chuẩn."
            ),
        )

    matched = bool(
        result.get("matched")
    )

    canonical_code = result.get(
        "code"
    )

    if (
        not matched
        or not canonical_code
    ):
        error_code: ResolutionCode = (
            "NAME_NOT_MATCHED"
            if data_type
            in {
                "activity",
                "lot",
            }
            else "UNKNOWN_MASTER_DATA"
        )

        raise DynamicFormCanonicalResolutionError(
            field=field,
            code=error_code,
            message=(
                f"Không thể ánh xạ "
                f"'{normalized_value}' "
                f"tại '{field}' "
                "sang mã chuẩn."
            ),
        )

    return (
        str(canonical_code)
        .strip()
        .upper()
    )


def _resolve_optional_code(
    *,
    data_type: str,
    value: str | None,
    field: str,
) -> str | None:
    if not str(value or "").strip():
        return None

    return _resolve_required_code(
        data_type=data_type,
        value=value,
        field=field,
    )


def build_cultivation_log_input(
    request: DynamicCreateWorkLogRequest,
    *,
    client_record_id: str,
    performed_at: datetime,
    context: NextFarmContext | None = None,
    confirmed: bool = False,
) -> CultivationLogInput:
    """
    Chuyển CREATE_WORK_LOG Dynamic Form V3.1
    sang CultivationLogInput canonical
    (dữ liệu nhật ký chuẩn).

    Boundary (ranh giới trách nhiệm):

    - KHÔNG parse transcript.
    - KHÔNG thực hiện NLP.
    - KHÔNG tính AI confidence.
    - KHÔNG suy diễn NextFarm context.
    - CHỈ resolve structured *_text
      sang canonical code.
    """

    fields = request.current_fields

    if fields is None:
        raise DynamicFormCanonicalResolutionError(
            field="current_fields",
            code="MISSING_REQUIRED_FIELD",
            message=(
                "CREATE_WORK_LOG chưa có "
                "current_fields."
            ),
        )

    activity_code = (
        _resolve_optional_code(
            data_type="activity",
            value=fields.activity_text,
            field="activity_text",
        )
    )

    lot_code = (
        _resolve_optional_code(
            data_type="lot",
            value=fields.plot_text,
            field="plot_text",
        )
    )

    materials: list[
        MaterialInput
    ] = []

    for index, material in enumerate(
        fields.materials
    ):
        material_field = (
            f"materials[{index}]"
        )

        material_code = (
            _resolve_required_code(
                data_type="material",
                value=material.material_text,
                field=(
                    f"{material_field}"
                    ".material_text"
                ),
            )
        )

        if material.quantity is None:
            raise (
                DynamicFormCanonicalResolutionError(
                    field=(
                        f"{material_field}"
                        ".quantity"
                    ),
                    code=(
                        "MISSING_REQUIRED_FIELD"
                    ),
                    message=(
                        "Thiếu quantity tại "
                        f"{material_field}."
                    ),
                )
            )

        unit_code = (
            _resolve_required_code(
                data_type="unit",
                value=material.unit_text,
                field=(
                    f"{material_field}"
                    ".unit_text"
                ),
            )
        )

        materials.append(
            MaterialInput(
                material_code=material_code,
                quantity=material.quantity,
                unit_code=unit_code,
            )
        )

    return CultivationLogInput(
        client_record_id=client_record_id,

        # Transcript chỉ được giữ để audit/history
        # (đối chiếu/lịch sử).
        # Adapter tuyệt đối không parse nó.
        transcript=request.transcript,

        result_status=fields.result_status,

        # NextFarmContext phải do caller truyền
        # bằng canonical IDs.
        # Không suy từ DynamicFormContext text.
        context=context,

        lot_code=lot_code,
        activity_code=activity_code,
        materials=materials,
        performed_at=performed_at,
        performer_code=None,
        material_batch_text=fields.material_batch_text,
        notes=fields.note,
        source="voice",
        confirmed=confirmed,
    )
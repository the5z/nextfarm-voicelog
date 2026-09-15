from __future__ import annotations

from decimal import Decimal
import re
from typing import Any

from app.data.activity_requirements import (
    get_activity_requirement,
)
from app.data.master_data import (
    ACTIVITIES,
    LOTS,
    MATERIALS,
)
from app.schemas.cultivation_log import (
    CultivationLogInput,
    MaterialInput,
)
from app.schemas.dynamic_form import (
    DynamicCreateWorkLogRequest,
    DynamicCreateWorkLogResponse,
    DynamicFormWarning,
    DynamicWorkLogFields,
    DynamicWorkLogMaterial,
)
from app.schemas.nextfarm import NextFarmContext
from app.services.business_validation_service import (
    validate_business_rules,
)
from app.services.normalization_service import (
    normalize_text,
    resolve_master_data,
)


def dynamic_work_log_to_cultivation_log(
    request: DynamicCreateWorkLogRequest,
    *,
    client_record_id: str,
    performed_at,
    context=None,
    confirmed: bool = False,
) -> CultivationLogInput:
    """
    Chuyển Dynamic Form V3.1 CREATE_WORK_LOG
    sang contract nội bộ CultivationLogInput v1.0.

    V3.1 dùng human-readable *_text.
    Integration chịu trách nhiệm resolve
    thành canonical code trước khi gọi adapter này.

    Hàm này KHÔNG tự resolve master data.
    """

    fields = request.current_fields

    if fields is None:
        raise ValueError(
            "CREATE_WORK_LOG chưa có current_fields."
        )

    if not fields.plot_text:
        raise ValueError(
            "CREATE_WORK_LOG thiếu plot_text."
        )

    if not fields.activity_text:
        raise ValueError(
            "CREATE_WORK_LOG thiếu activity_text."
        )

    materials: list[
        MaterialInput
    ] = []

    for index, material in enumerate(
        fields.materials
    ):
        if not material.material_text:
            raise ValueError(
                (
                    "Thiếu material_text tại "
                    f"materials[{index}]."
                )
            )

        if material.quantity is None:
            raise ValueError(
                (
                    "Thiếu quantity tại "
                    f"materials[{index}]."
                )
            )

        if not material.unit_text:
            raise ValueError(
                (
                    "Thiếu unit_text tại "
                    f"materials[{index}]."
                )
            )

        materials.append(
            MaterialInput(
                material_code=(
                    material.material_text
                ),
                quantity=(
                    material.quantity
                ),
                unit_code=(
                    material.unit_text
                ),
            )
        )

    if context is None:
        dynamic_context = request.context

        if (
            dynamic_context.current_plot_text
            and dynamic_context.current_season_text
        ):
            raise ValueError(
                "Dynamic Form context hiện tại chỉ chứa "
                "text context, chưa đủ canonical NextFarm IDs."
            )

        context = None

    return CultivationLogInput(
        client_record_id=client_record_id,
        transcript=request.transcript,
        context=context,
        lot_code=fields.plot_text,
        activity_code=fields.activity_text,
        materials=materials,
        performed_at=performed_at,
        performer_code=None,
        notes=fields.note,
        source="voice",
        confirmed=confirmed,
    )


# =========================================================
# TASK 3: VALIDATION & MULTI-TURN CLARIFICATION SERVICE
# =========================================================


def _parse_quantity_and_unit(
    text: str,
) -> tuple[Decimal | None, str | None]:
    """
    Trích xuất số lượng và đơn vị từ văn bản.
    """
    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*([^\d\s]+)?",
        text,
    )
    if not match:
        return None, None

    qty_str = match.group(1).replace(",", ".")
    try:
        qty = Decimal(qty_str)
        if qty <= 0:
            qty = None
    except Exception:
        qty = None

    unit = match.group(2).strip() if match.group(2) else None
    return qty, unit


def _extract_activity_from_text(text: str) -> str | None:
    norm = normalize_text(text)
    for record in ACTIVITIES:
        candidates = [record["name"], *record.get("aliases", [])]
        for candidate in candidates:
            cand_norm = normalize_text(candidate)
            if cand_norm and cand_norm in norm:
                return record["name"]
    return None


def _extract_plot_from_text(text: str) -> str | None:
    norm = normalize_text(text)
    for record in LOTS:
        candidates = [record["name"], *record.get("aliases", [])]
        for candidate in candidates:
            cand_norm = normalize_text(candidate)
            if cand_norm and cand_norm in norm:
                return record["name"]
    match = re.search(r"lô\s*([a-zA-Z0-9]+)", text, re.IGNORECASE)
    if match:
        return f"Lô {match.group(1).upper()}"
    return None


def _extract_material_from_text(text: str) -> str | None:
    norm = normalize_text(text)
    for record in MATERIALS:
        candidates = [record["name"], *record.get("aliases", [])]
        for candidate in candidates:
            cand_norm = normalize_text(candidate)
            if cand_norm and cand_norm in norm:
                return record["name"]
    return None

def _material_index_from_field(
    field: str | None,
) -> int | None:
    """
    Lấy index vật tư từ field dạng:

    materials[0].material_text
    materials[1].quantity
    materials[2].unit_text
    """

    if not field:
        return None

    match = re.fullmatch(
        r"materials\[(\d+)\]\."
        r"(material_text|quantity|unit_text)",
        field,
    )

    if not match:
        return None

    return int(match.group(1))


def _merge_transcript_into_fields(
    transcript: str,
    fields: DynamicWorkLogFields,
    expected_field: str | None = None,
) -> list[DynamicFormWarning]:
    """
    Cập nhật current_fields dựa trên transcript mới.
    Bảo tồn thông tin cũ. Kiểm tra mâu thuẫn (CONFLICTING_VALUE).
    """
    warnings: list[DynamicFormWarning] = []
    text = transcript.strip()
    if not text:
        return warnings

    # 1. Activity
    extracted_act = _extract_activity_from_text(text)
    if extracted_act:
        if fields.activity_text and normalize_text(fields.activity_text) != normalize_text(extracted_act):
            warnings.append(
                DynamicFormWarning(
                    field="activity_text",
                    code="CONFLICTING_VALUE",
                    message=(
                        f"Phát hiện mâu thuẫn công việc giữa "
                        f"'{fields.activity_text}' và '{extracted_act}'."
                    ),
                )
            )
        else:
            fields.activity_text = extracted_act

    # 2. Plot
    extracted_plot = _extract_plot_from_text(text)
    if extracted_plot:
        if fields.plot_text and normalize_text(fields.plot_text) != normalize_text(extracted_plot):
            warnings.append(
                DynamicFormWarning(
                    field="plot_text",
                    code="CONFLICTING_VALUE",
                    message=(
                        f"Phát hiện mâu thuẫn lô giữa "
                        f"'{fields.plot_text}' và '{extracted_plot}'."
                    ),
                )
            )
        else:
            fields.plot_text = extracted_plot

    # 3. Materials
    extracted_mat = _extract_material_from_text(
        text
    )

    qty, unit = _parse_quantity_and_unit(
        text
    )

    # Nếu có số nhưng không có đơn vị, chỉ coi là
    # quantity khi cả câu thực sự chỉ là một con số.
    #
    # "20"            -> quantity = 20
    # "20 kg"         -> quantity = 20, unit = kg
    # "ABC Super 999" -> 999 không phải quantity
    quantity_only = bool(
        re.fullmatch(
            r"\s*[-+]?\d+(?:[.,]\d+)?\s*",
            text,
        )
    )

    if (
        qty is not None
        and unit is None
        and not quantity_only
    ):
        qty = None


    # =========================================================
    # Xác định material nào đang được làm rõ
    # =========================================================

    expected_material_index = (
        _material_index_from_field(
            expected_field
        )
    )

    target_index: int | None = None


    # Chưa có material nào:
    # vẫn cho phép parse một câu đầy đủ như
    # "NPK 20 kg".
    if not fields.materials:
        if (
            extracted_mat is not None
            or qty is not None
            or unit is not None
        ):
            fields.materials.append(
                DynamicWorkLogMaterial(
                    material_text=extracted_mat,
                    quantity=qty,
                    unit_text=unit,
                )
            )

        return warnings


    # Chatbot đang hỏi rõ material[index].
    if expected_material_index is not None:
        while (
            len(fields.materials)
            <= expected_material_index
        ):
            fields.materials.append(
                DynamicWorkLogMaterial()
            )

        target_index = (
            expected_material_index
        )


    # Chỉ có đúng 1 material thì có thể chọn nó
    # mà không gây mơ hồ.
    elif len(fields.materials) == 1:
        target_index = 0


    # Có nhiều material nhưng không biết user đang
    # nói material nào -> KHÔNG tự đoán.
    else:
        return warnings


    target_mat = fields.materials[
        target_index
    ]


    # =========================================================
    # material_text
    # =========================================================

    if extracted_mat:
        if (
            target_mat.material_text
            and normalize_text(
                target_mat.material_text
            )
            != normalize_text(
                extracted_mat
            )
        ):
            warnings.append(
                DynamicFormWarning(
                    field=(
                        f"materials[{target_index}]"
                        ".material_text"
                    ),
                    code="CONFLICTING_VALUE",
                    message=(
                        "Phát hiện mâu thuẫn vật tư "
                        f"giữa '{target_mat.material_text}' "
                        f"và '{extracted_mat}'."
                    ),
                )
            )

        else:
            target_mat.material_text = (
                extracted_mat
            )


    # =========================================================
    # quantity
    # =========================================================

    if qty is not None:
        if (
            target_mat.quantity is not None
            and target_mat.quantity != qty
        ):
            warnings.append(
                DynamicFormWarning(
                    field=(
                        f"materials[{target_index}]"
                        ".quantity"
                    ),
                    code="CONFLICTING_VALUE",
                    message=(
                        "Phát hiện mâu thuẫn số lượng "
                        f"giữa '{target_mat.quantity}' "
                        f"và '{qty}'."
                    ),
                )
            )

        else:
            target_mat.quantity = qty


    # =========================================================
    # unit
    # =========================================================

    if unit is not None:
        if (
            target_mat.unit_text
            and normalize_text(
                target_mat.unit_text
            )
            != normalize_text(unit)
        ):
            warnings.append(
                DynamicFormWarning(
                    field=(
                        f"materials[{target_index}]"
                        ".unit_text"
                    ),
                    code="CONFLICTING_VALUE",
                    message=(
                        "Phát hiện mâu thuẫn đơn vị "
                        f"giữa '{target_mat.unit_text}' "
                        f"và '{unit}'."
                    ),
                )
            )

        else:
            target_mat.unit_text = unit

    return warnings


def _detect_missing_fields(fields: DynamicWorkLogFields) -> list[str]:
    """
    Phát hiện các trường bắt buộc còn thiếu theo quy tắc CREATE_WORK_LOG.
    """
    missing: list[str] = []

    if not fields.activity_text or not fields.activity_text.strip():
        missing.append("activity_text")

    if not fields.plot_text or not fields.plot_text.strip():
        missing.append("plot_text")

    act_code = None
    if fields.activity_text:
        res = resolve_master_data("activity", fields.activity_text)
        act_code = res.get("code")

    req = get_activity_requirement(act_code) if act_code else None
    materials_required = req["materials_required"] if req else None

    if materials_required is True and not fields.materials:
        missing.append("materials[0].material_text")
    elif fields.materials:
        for index, mat in enumerate(fields.materials):
            if not mat.material_text or not mat.material_text.strip():
                missing.append(f"materials[{index}].material_text")
            elif mat.quantity is None:
                missing.append(f"materials[{index}].quantity")
            elif not mat.unit_text or not mat.unit_text.strip():
                missing.append(f"materials[{index}].unit_text")

    return missing

def _validate_ambiguous_units(
    fields: DynamicWorkLogFields,
) -> tuple[
    list[DynamicFormWarning],
    list[str],
]:
    """
    Kiểm tra đơn vị mơ hồ.

    Không tự động quy đổi các đơn vị như
    'xị', 'công', 'sào' sang unit chuẩn.
    """

    warnings: list[DynamicFormWarning] = []
    unresolved_fields: list[str] = []

    for index, material in enumerate(
        fields.materials
    ):
        if not material.unit_text:
            continue

        result = resolve_master_data(
            "unit",
            material.unit_text,
        )

        if result.get("match_type") != "ambiguous":
            continue

        field = (
            f"materials[{index}].unit_text"
        )

        warnings.append(
            DynamicFormWarning(
                field=field,
                code="AMBIGUOUS_UNIT",
                message=(
                    f"Đơn vị "
                    f"'{material.unit_text}' "
                    "có ý nghĩa không thống nhất. "
                    "Cần người dùng cung cấp "
                    "đơn vị chuẩn."
                ),
            )
        )

        unresolved_fields.append(field)

    return warnings, unresolved_fields

def _build_next_question(
    missing_fields: list[str],
    warnings: list[
        DynamicFormWarning
    ] | None = None,
) -> str | None:
    """
    Chỉ hỏi MỘT thông tin cần làm rõ
    trong mỗi lượt.
    """

    warnings = warnings or []

    # =====================================================
    # 1. CONFLICT
    # =====================================================

    for warning in warnings:
        if (
            warning.code
            == "CONFLICTING_VALUE"
        ):
            return (
                "Thông tin mới bạn vừa cung cấp "
                "khác với thông tin trước đó. "
                "Bạn vui lòng xác nhận giá trị "
                "nào là đúng."
            )

    # =====================================================
    # 2. AMBIGUOUS UNIT
    # =====================================================

    for warning in warnings:
        if (
            warning.code
            == "AMBIGUOUS_UNIT"
        ):
            return (
                "Đơn vị này còn mơ hồ. "
                "Bạn vui lòng cho biết "
                "đơn vị chuẩn, ví dụ kg, "
                "lít, ml, bao hoặc chai."
            )

    # =====================================================
    # 3. UNKNOWN MASTER DATA
    # =====================================================

    for warning in warnings:
        if warning.code in {
            "UNKNOWN_MASTER_DATA",
            "NAME_NOT_MATCHED",
        }:
            if warning.field == (
                "activity_text"
            ):
                return (
                    "Tôi chưa nhận diện được "
                    "công việc này. "
                    "Bạn vui lòng nói lại "
                    "tên công việc."
                )

            if warning.field == (
                "plot_text"
            ):
                return (
                    "Tôi chưa nhận diện được "
                    "lô này. "
                    "Bạn vui lòng cho biết "
                    "lại tên lô."
                )

            if warning.field.endswith(
                ".material_text"
            ):
                return (
                    "Tôi chưa nhận diện được "
                    "vật tư này. "
                    "Bạn vui lòng cho biết "
                    "lại tên vật tư."
                )

            if warning.field.endswith(
                ".unit_text"
            ):
                return (
                    "Tôi chưa nhận diện được "
                    "đơn vị này. "
                    "Bạn vui lòng cho biết "
                    "đơn vị chuẩn."
                )

    # =====================================================
    # 4. LOW CONFIDENCE
    # =====================================================

    for warning in warnings:
        if (
            warning.code
            == "LOW_CONFIDENCE"
        ):
            return (
                "Thông tin này chưa đủ "
                "độ tin cậy. "
                "Bạn vui lòng xác nhận "
                "lại giúp tôi."
            )

    # =====================================================
    # 5. MISSING FIELD
    # =====================================================

    if not missing_fields:
        return None

    field = missing_fields[0]

    if field == "activity_text":
        return (
            "Bạn đã thực hiện công việc gì?"
        )

    if field == "plot_text":
        return (
            "Bạn thực hiện công việc "
            "ở lô nào?"
        )

    if field.endswith(
        ".material_text"
    ):
        return (
            "Bạn đã sử dụng vật tư nào?"
        )

    if field.endswith(
        ".quantity"
    ):
        return (
            "Bạn đã sử dụng bao nhiêu?"
        )

    if field.endswith(
        ".unit_text"
    ):
        return (
            "Đơn vị của số lượng này là gì?"
        )

    return (
        "Bạn vui lòng bổ sung "
        "thông tin còn thiếu."
    )

def _build_confirmation_question(
    fields: DynamicWorkLogFields,
) -> str:
    """
    Tạo bản tóm tắt cuối để người dùng xác nhận.

    Không lặp lại dữ liệu ở từng lượt;
    chỉ tóm tắt khi đã đủ thông tin.
    """

    parts: list[str] = []

    if fields.activity_text:
        parts.append(
            f"công việc {fields.activity_text}"
        )

    if fields.plot_text:
        parts.append(
            f"tại {fields.plot_text}"
        )

    material_parts: list[str] = []

    for material in fields.materials:
        detail: list[str] = []

        if material.material_text:
            detail.append(
                material.material_text
            )

        if material.quantity is not None:
            detail.append(
                str(material.quantity)
            )

        if material.unit_text:
            detail.append(
                material.unit_text
            )

        if detail:
            material_parts.append(
                " ".join(detail)
            )

    if material_parts:
        parts.append(
            "vật tư "
            + ", ".join(material_parts)
        )

    summary = ", ".join(parts)

    return (
        f"Thông tin hiện tại: {summary}. "
        "Bạn xác nhận lưu nhật ký này không?"
    )

def _capture_raw_answer_for_expected_field(
    transcript: str,
    fields: DynamicWorkLogFields,
    missing_before_merge: list[str],
) -> None:
    """
    Khi chatbot vừa hỏi một field cụ thể nhưng câu trả lời
    không match master data, vẫn giữ raw text để Integration
    có thể báo UNKNOWN_MASTER_DATA / NAME_NOT_MATCHED.

    Không tự đoán sang giá trị khác.
    """

    text = transcript.strip()

    if not text or not missing_before_merge:
        return

    expected_field = missing_before_merge[0]

    if (
        expected_field == "activity_text"
        and not fields.activity_text
    ):
        fields.activity_text = text
        return

    if (
        expected_field == "plot_text"
        and not fields.plot_text
    ):
        fields.plot_text = text
        return

    if expected_field.endswith(
        ".unit_text"
    ):
        match = re.search(
            r"materials\[(\d+)\]",
            expected_field,
        )

        if not match:
            return

        index = int(match.group(1))

        if index >= len(fields.materials):
            return

        # Chatbot đang hỏi đúng unit_text,
        # nên câu trả lời "kg", "lít", "xị"...
        # được giữ nguyên để bước validation
        # (xác thực) phía sau xử lý.
        if not fields.materials[index].unit_text:
            fields.materials[index].unit_text = text

        return
    if expected_field.endswith(
        ".material_text"
    ):
        qty, unit = _parse_quantity_and_unit(
            text
        )

        # Nếu câu trả lời chỉ là số lượng / đơn vị,
        # ví dụ "20", "20 kg", "20 xị",
        # thì không được coi là tên vật tư.
        #
        # Nhưng tên vật tư có chứa số như
        # "ABC Super 999" vẫn phải được giữ nguyên
        # để báo UNKNOWN_MASTER_DATA.
        if qty is not None:
            text_without_number = re.sub(
                r"[-+]?\d+(?:[.,]\d+)?",
                " ",
                text,
                count=1,
            )

            remainder = " ".join(
                text_without_number.split()
            )

            # Ví dụ: "20"
            if not remainder:
                return

            unit_result = resolve_master_data(
                "unit",
                remainder,
            )

            # Ví dụ:
            # "20 kg" -> remainder = "kg"
            # "20 xị" -> remainder = "xị"
            if (
                unit_result.get("matched")
                or unit_result.get(
                    "match_type"
                ) == "ambiguous"
            ):
                return

        elif unit is not None:
            return

        match = re.search(
            r"materials\[(\d+)\]",
            expected_field,
        )

        if not match:
            return

        index = int(match.group(1))

        while len(fields.materials) <= index:
            fields.materials.append(
                DynamicWorkLogMaterial()
            )

        if not fields.materials[
            index
        ].material_text:
            fields.materials[
                index
            ].material_text = text

def _validate_master_data_fields(
    fields: DynamicWorkLogFields,
) -> tuple[
    list[DynamicFormWarning],
    list[str],
    dict[str, float],
]:
    """
    Kiểm tra các field dạng text với master data.

    Trả về:
    - warnings
    - unresolved_fields: field chưa giải quyết được
    - field_confidence: độ tin cậy của từng field
    """

    warnings: list[
        DynamicFormWarning
    ] = []

    unresolved_fields: list[str] = []

    field_confidence: dict[
        str,
        float,
    ] = {}

    checks: list[
        tuple[str, str, str]
    ] = []

    if fields.activity_text:
        checks.append(
            (
                "activity_text",
                "activity",
                fields.activity_text,
            )
        )

    if fields.plot_text:
        checks.append(
            (
                "plot_text",
                "lot",
                fields.plot_text,
            )
        )

    for index, material in enumerate(
        fields.materials
    ):
        if material.material_text:
            checks.append(
                (
                    (
                        f"materials[{index}]"
                        ".material_text"
                    ),
                    "material",
                    material.material_text,
                )
            )

        if material.quantity is not None:
            field_confidence[
                f"materials[{index}].quantity"
            ] = 1.0

        if material.unit_text:
            checks.append(
                (
                    (
                        f"materials[{index}]"
                        ".unit_text"
                    ),
                    "unit",
                    material.unit_text,
                )
            )

    for (
        field,
        data_type,
        value,
    ) in checks:
        result = resolve_master_data(
            data_type,
            value,
        )

        confidence = float(
            result.get(
                "confidence",
                0.0,
            )
            or 0.0
        )

        field_confidence[field] = confidence

        match_type = result.get(
            "match_type"
        )

        # AMBIGUOUS_UNIT đã được Step 3A xử lý.
        if match_type == "ambiguous":
            continue

        if not result.get("matched"):
            if data_type in {
                "activity",
                "lot",
            }:
                code = "NAME_NOT_MATCHED"
            else:
                code = "UNKNOWN_MASTER_DATA"

            warnings.append(
                DynamicFormWarning(
                    field=field,
                    code=code,
                    message=(
                        f"Không tìm thấy "
                        f"'{value}' trong "
                        "master data hiện tại."
                    ),
                )
            )

            unresolved_fields.append(
                field
            )

            continue

        # Theo Dynamic Form V3.1:
        # 0.60 <= confidence < 0.85
        # cần warning/review.
        if confidence < 0.85:
            warnings.append(
                DynamicFormWarning(
                    field=field,
                    code="LOW_CONFIDENCE",
                    message=(
                        f"Giá trị '{value}' "
                        "được nhận diện với "
                        f"độ tin cậy "
                        f"{confidence:.2f}. "
                        "Cần người dùng "
                        "xác nhận."
                    ),
                )
            )
    return (
        warnings,
        unresolved_fields,
        field_confidence,
    )
def _build_business_rule_warnings(
    fields: DynamicWorkLogFields,
) -> list[DynamicFormWarning]:
    """
    Sinh cảnh báo từ rule catalog hiện tại.

    Không tự suy đoán thêm business rule.
    """

    if not fields.activity_text:
        return []

    result = resolve_master_data(
        "activity",
        fields.activity_text,
    )

    activity_code = result.get(
        "code"
    )

    if not activity_code:
        return []

    requirement = get_activity_requirement(
        activity_code
    )

    if requirement is None:
        return []

    rule_status = requirement[
        "rule_status"
    ]

    # review_confirmed đã được enforce bởi
    # _detect_missing_fields().
    if rule_status == "review_confirmed":
        return []

    return [
        DynamicFormWarning(
            field="activity_text",
            code="BUSINESS_RULE_WARNING",
            message=(
                "Quy tắc nghiệp vụ cho "
                f"hoạt động "
                f"'{fields.activity_text}' "
                "chưa được duyệt hoàn toàn. "
                "Cần người dùng xác nhận "
                "trước khi lưu."
            ),
        )
    ]

def process_dynamic_create_work_log(
    request: DynamicCreateWorkLogRequest,
) -> DynamicCreateWorkLogResponse:
    """
    Validation & Clarification
    (xác thực và làm rõ)
    cho CREATE_WORK_LOG.

    Flow:
    1. giữ current_fields
    2. merge transcript mới
    3. kiểm tra missing fields
    4. kiểm tra ambiguous unit
    5. kiểm tra master data
    6. kiểm tra confidence
    7. kiểm tra business warning
    8. hỏi đúng một vấn đề mỗi lượt
    9. nếu đủ dữ liệu -> yêu cầu xác nhận cuối
    """

    fields = (
        request.current_fields.model_copy(
            deep=True
        )
        if request.current_fields
        is not None
        else DynamicWorkLogFields(
            result_status="completed",
        )
    )

    warnings: list[
        DynamicFormWarning
    ] = []

    # =====================================================
    # 1. Missing trước khi merge
    # =====================================================

    missing_before_merge = (
        _detect_missing_fields(fields)
    )

    expected_field = (
        missing_before_merge[0]
        if missing_before_merge
        else None
    )
    # =====================================================
    # 2. Merge transcript
    # =====================================================

    if request.transcript:
        warnings.extend(
            _merge_transcript_into_fields(
                request.transcript,
                fields,
                expected_field=expected_field,
            )
        )

        _capture_raw_answer_for_expected_field(
            request.transcript,
            fields,
            missing_before_merge,
        )

    # =====================================================
    # 3. Missing sau merge
    # =====================================================

    missing_fields = (
        _detect_missing_fields(fields)
    )

    # =====================================================
    # 4. Ambiguous unit
    # =====================================================

    (
        unit_warnings,
        ambiguous_fields,
    ) = _validate_ambiguous_units(
        fields
    )

    warnings.extend(
        unit_warnings
    )

    # =====================================================
    # 5. Master data + confidence
    # =====================================================

    (
        master_warnings,
        unresolved_fields,
        field_confidence,
    ) = _validate_master_data_fields(
        fields
    )

    warnings.extend(
        master_warnings
    )

    # =====================================================
    # 6. Business rule warnings
    # =====================================================

    warnings.extend(
        _build_business_rule_warnings(
            fields
        )
    )

    # =====================================================
    # 7. unresolved cũng được coi là cần làm rõ
    # =====================================================

    for field in [
        *ambiguous_fields,
        *unresolved_fields,
    ]:
        if field not in missing_fields:
            missing_fields.append(
                field
            )

    # =====================================================
    # 8. Chọn câu hỏi tiếp theo
    # =====================================================

    clarification_codes = {
        "AMBIGUOUS_UNIT",
        "LOW_CONFIDENCE",
        "UNKNOWN_MASTER_DATA",
        "CONFLICTING_VALUE",
        "NAME_NOT_MATCHED",
    }

    has_clarification_warning = any(
        warning.code
        in clarification_codes
        for warning in warnings
    )

    if (
        missing_fields
        or has_clarification_warning
    ):
        next_question = (
            _build_next_question(
                missing_fields,
                warnings,
            )
        )

        requires_confirmation = True

    else:
        # Đã đủ dữ liệu.
        # Không tự lưu ngay.
        next_question = (
            _build_confirmation_question(
                fields
            )
        )

        requires_confirmation = True

    return DynamicCreateWorkLogResponse(
        fields=fields,
        missing_fields=missing_fields,
        warnings=warnings,
        field_confidence=field_confidence,
        requires_confirmation=(
            requires_confirmation
        ),
        next_question=next_question,
    )
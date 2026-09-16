from app.data.activity_requirements import (
    RULE_CATALOG_VERSION,
    get_activity_requirement,
)
from app.data.master_data import (
    ACTIVITIES,
    LOTS,
    MATERIALS,
    UNITS,
    MasterDataRecord,
)
from app.schemas.cultivation_log import (
    CultivationLogInput,
)


def _known_codes(
    records: list[MasterDataRecord],
) -> set[str]:
    return {
        str(item["code"])
        .strip()
        .upper()
        for item in records
    }


def _find_name_by_code(
    records: list[MasterDataRecord],
    code: str,
) -> str | None:
    normalized_code = (
        str(code or "")
        .strip()
        .upper()
    )

    for item in records:
        item_code = (
            str(item["code"])
            .strip()
            .upper()
        )

        if item_code == normalized_code:
            return str(item["name"])

    return None


KNOWN_ACTIVITY_CODES = _known_codes(ACTIVITIES)
KNOWN_LOT_CODES = _known_codes(LOTS)
KNOWN_MATERIAL_CODES = _known_codes(MATERIALS)
KNOWN_UNIT_CODES = _known_codes(UNITS)


def validate_business_rules(
    payload: CultivationLogInput,
) -> dict[str, object]:
    """
    Canonical business validation cho cultivation logs.

    CREATE_WORK_LOG V3.1 cho phép thiếu activity/plot. Integration chỉ
    kiểm tra membership khi canonical code thực sự được cung cấp.
    """

    errors: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []

    activity_code = (
        str(payload.activity_code or "")
        .strip()
        .upper()
    )

    lot_code = (
        str(payload.lot_code or "")
        .strip()
        .upper()
    )

    # Optional theo CREATE_WORK_LOG V3.1: chỉ validate nếu có giá trị.
    if (
        activity_code
        and activity_code not in KNOWN_ACTIVITY_CODES
    ):
        errors.append(
            {
                "field": "activity_code",
                "code": "UNKNOWN_ACTIVITY",
                "message": (
                    f"Activity code '{activity_code}' "
                    "không tồn tại trong master data hiện tại."
                ),
                "requires_confirmation": False,
            }
        )

    if (
        lot_code
        and lot_code not in KNOWN_LOT_CODES
    ):
        errors.append(
            {
                "field": "lot_code",
                "code": "UNKNOWN_LOT",
                "message": (
                    f"Lot code '{lot_code}' "
                    "không tồn tại trong master data hiện tại."
                ),
                "requires_confirmation": False,
            }
        )

    requirement = (
        get_activity_requirement(activity_code)
        if activity_code
        else None
    )

    if (
        requirement is not None
        and requirement["rule_status"] == "review_confirmed"
        and requirement["materials_required"] is True
        and not payload.materials
    ):
        activity_name = (
            _find_name_by_code(
                ACTIVITIES,
                activity_code,
            )
            or activity_code
        )

        errors.append(
            {
                "field": "materials",
                "code": "MATERIAL_REQUIRED_FOR_ACTIVITY",
                "message": (
                    f"Hoạt động '{activity_name}' "
                    "bắt buộc phải có ít nhất một vật tư "
                    "theo rule catalog hiện tại."
                ),
                "requires_confirmation": False,
            }
        )

    for index, material in enumerate(payload.materials):
        material_code = (
            str(material.material_code or "")
            .strip()
            .upper()
        )

        unit_code = (
            str(material.unit_code or "")
            .strip()
            .upper()
        )

        if material_code not in KNOWN_MATERIAL_CODES:
            errors.append(
                {
                    "field": f"materials[{index}].material_code",
                    "code": "UNKNOWN_MATERIAL",
                    "message": (
                        f"Material code '{material_code}' "
                        "không tồn tại trong master data hiện tại."
                    ),
                    "requires_confirmation": False,
                }
            )

        if unit_code not in KNOWN_UNIT_CODES:
            errors.append(
                {
                    "field": f"materials[{index}].unit_code",
                    "code": "UNKNOWN_UNIT",
                    "message": (
                        f"Unit code '{unit_code}' "
                        "không tồn tại trong master data hiện tại."
                    ),
                    "requires_confirmation": False,
                }
            )

    if not payload.confirmed:
        warnings.append(
            {
                "field": "confirmed",
                "code": "UNCONFIRMED_RECORD",
                "message": (
                    "Nhật ký chưa được người dùng xác nhận."
                ),
                "requires_confirmation": True,
            }
        )

    requires_confirmation = any(
        bool(issue.get("requires_confirmation"))
        for issue in warnings
    )

    return {
        "rule_version": RULE_CATALOG_VERSION,
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "requires_confirmation": requires_confirmation,
    }

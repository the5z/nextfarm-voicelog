from app.schemas.activity import ActivityData


MATERIAL_REQUIRED_ACTIVITIES = {
    "bón phân",
    "bon phan",
    "phun thuốc",
    "phun thuoc",
    "xịt thuốc",
    "xit thuoc",
    "cho bò ăn",
    "cho bo an",
    "cho gia súc ăn",
    "cho gia suc an",
}


def _normalize_text(
    value: str | None,
) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
    )


def _requires_material(
    activity_text: str | None,
) -> bool:
    normalized_activity = _normalize_text(
        activity_text
    )

    if not normalized_activity:
        return False

    return any(
        activity in normalized_activity
        for activity in MATERIAL_REQUIRED_ACTIVITIES
    )


def apply_confidence_rules(
    data: ActivityData,
) -> ActivityData:
    """
    Apply deterministic safety rules after Gemini extraction.

    This layer does not guess missing business data.
    It only makes the confirmation state internally consistent.
    """

    missing_fields = list(
        data.missing_fields
    )

    warnings = list(
        data.warnings
    )

    if data.activity_text is None:
        if "activity_text" not in missing_fields:
            missing_fields.append(
                "activity_text"
            )

    if data.lot_text is None:
        if "lot_text" not in missing_fields:
            missing_fields.append(
                "lot_text"
            )

    for material in data.materials:
        if material.material_text is None:
            field = "materials.material_text"

            if field not in missing_fields:
                missing_fields.append(
                    field
                )

        if (
            material.material_text is not None
            and material.quantity is None
        ):
            field = "materials.quantity"

            if field not in missing_fields:
                missing_fields.append(
                    field
                )

        if (
            material.material_text is not None
            and material.unit_text is None
        ):
            field = "materials.unit_text"

            if field not in missing_fields:
                missing_fields.append(
                    field
                )

        if (
            material.unit_text
            and material.unit_text.lower()
            in {
                "xị",
                "công",
                "sào",
            }
        ):
            warning = (
                f"Đơn vị '{material.unit_text}' "
                "cần được xác nhận."
            )

            if warning not in warnings:
                warnings.append(
                    warning
                )

    if data.time_text is None:
        if "time_text" not in missing_fields:
            missing_fields.append(
                "time_text"
            )

    requires_confirmation = bool(
        missing_fields
        or warnings
        or data.requires_confirmation
    )

    return data.model_copy(
        update={
            "missing_fields": missing_fields,
            "warnings": warnings,
            "requires_confirmation": (
                requires_confirmation
            ),
        }
    )
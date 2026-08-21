import re

from app.schemas.activity import (
    ActivityData,
    MaterialData,
)


def normalize_time_text(
    message: str,
) -> str | None:
    text = message.strip().lower()

    match = re.search(
        r"(\d{1,2})(?::|h| giờ)?(?:\s*(\d{1,2}))?",
        text,
    )

    if not match:
        return None

    hour = int(match.group(1))
    minute = int(
        match.group(2) or 0
    )

    if not 0 <= hour <= 23:
        return None

    if not 0 <= minute <= 59:
        return None

    return f"{hour:02d}:{minute:02d}"


def parse_quantity_and_unit(
    message: str,
) -> tuple[float | None, str | None]:
    text = message.strip()

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*([^\d\s]+)?",
        text,
    )

    if not match:
        return None, None

    quantity_text = (
        match.group(1)
        .replace(",", ".")
    )

    try:
        quantity = float(
            quantity_text
        )
    except ValueError:
        quantity = None

    unit = (
        match.group(2).strip()
        if match.group(2)
        else None
    )

    return quantity, unit


def apply_message_to_activity(
    activity: ActivityData,
    expected_field: str | None,
    message: str,
) -> ActivityData:
    text = message.strip()

    if not text:
        return activity

    if expected_field == "activity_text":
        return activity.model_copy(
            update={
                "activity_text": text,
            }
        )

    if expected_field == "lot_text":
        return activity.model_copy(
            update={
                "lot_text": text,
            }
        )

    if expected_field == "time_text":
        time_text = normalize_time_text(
            text
        )

        if time_text is None:
            return activity

        return activity.model_copy(
            update={
                "time_text": time_text,
            }
        )

    materials = list(
        activity.materials
    )

    if not materials:
        materials = [
            MaterialData()
        ]

    first_material = materials[0]

    if expected_field == (
        "materials.material_text"
    ):
        materials[0] = (
            first_material.model_copy(
                update={
                    "material_text": text,
                }
            )
        )

        return activity.model_copy(
            update={
                "materials": materials,
            }
        )

    if expected_field == (
        "materials.quantity"
    ):
        quantity, unit = (
            parse_quantity_and_unit(
                text
            )
        )

        if quantity is None:
            return activity

        material_update = {
            "quantity": quantity,
        }

        if unit is not None:
            material_update[
                "unit_text"
            ] = unit

        materials[0] = (
            first_material.model_copy(
                update=material_update
            )
        )

        return activity.model_copy(
            update={
                "materials": materials,
            }
        )

    if expected_field == (
        "materials.unit_text"
    ):
        materials[0] = (
            first_material.model_copy(
                update={
                    "unit_text": text,
                }
            )
        )

        return activity.model_copy(
            update={
                "materials": materials,
            }
        )

    return activity
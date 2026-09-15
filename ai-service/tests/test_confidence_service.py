from app.schemas.activity import ActivityData, MaterialData
from app.services.confidence_service import apply_confidence_rules


def test_missing_time_requires_confirmation():
    data = ActivityData(
        activity_text="Bón phân",
        lot_text="Lô A",
        materials=[],
        time_text=None,
    )

    result = apply_confidence_rules(data)

    assert "time_text" in result.missing_fields
    assert result.requires_confirmation is True


def test_missing_lot_requires_confirmation():
    data = ActivityData(
        activity_text="Làm cỏ",
        lot_text=None,
        materials=[],
        time_text="10:00",
    )

    result = apply_confidence_rules(data)

    assert "lot_text" in result.missing_fields
    assert result.requires_confirmation is True


def test_ambiguous_unit_adds_warning():
    data = ActivityData(
        activity_text="Bón phân",
        lot_text="Lô B",
        materials=[
            MaterialData(
                material_text="Phân",
                quantity=2,
                unit_text="xị",
            )
        ],
        time_text="06:00",
    )

    result = apply_confidence_rules(data)

    assert (
        "Đơn vị 'xị' cần được xác nhận."
        in result.warnings
    )
    assert result.requires_confirmation is True


def test_missing_material_quantity_requires_confirmation():
    data = ActivityData(
        activity_text="Bón phân",
        lot_text="Lô A",
        materials=[
            MaterialData(
                material_text="NPK",
                quantity=None,
                unit_text="kg",
            )
        ],
        time_text="07:00",
    )

    result = apply_confidence_rules(data)

    assert (
        "materials.quantity"
        in result.missing_fields
    )
    assert result.requires_confirmation is True


def test_missing_material_unit_requires_confirmation():
    data = ActivityData(
        activity_text="Bón phân",
        lot_text="Lô A",
        materials=[
            MaterialData(
                material_text="NPK",
                quantity=20,
                unit_text=None,
            )
        ],
        time_text="07:00",
    )

    result = apply_confidence_rules(data)

    assert (
        "materials.unit_text"
        in result.missing_fields
    )
    assert result.requires_confirmation is True


def test_complete_record_does_not_require_confirmation():
    data = ActivityData(
        activity_text="Bón phân",
        lot_text="Lô A",
        materials=[
            MaterialData(
                material_text="NPK",
                quantity=20,
                unit_text="kg",
            )
        ],
        time_text="07:00",
    )

    result = apply_confidence_rules(data)

    assert result.missing_fields == []
    assert result.warnings == []
    assert result.requires_confirmation is False
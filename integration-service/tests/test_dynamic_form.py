from datetime import datetime
from decimal import Decimal
from urllib import request

from app.schemas.dynamic_form import (
    DynamicCreateWorkLogRequest,
    DynamicWorkLogFields,
    DynamicWorkLogMaterial,
)
from app.services.dynamic_form_service import (
    dynamic_work_log_to_cultivation_log,
)
from app.schemas.nextfarm import NextFarmContext
from app.services.dynamic_form_service import (
    dynamic_work_log_to_cultivation_log,
    process_dynamic_create_work_log,
)

def test_create_work_log_maps_multiple_materials():
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript=(
            "Bón 20kg NPK và 5kg urê "
            "cho lô A lúc 7 giờ sáng"
        ),
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            plot_text="LO_A",
            activity_text="BON_PHAN",
            performed_time_text="7 giờ sáng",
            materials=[
                DynamicWorkLogMaterial(
                    material_text="NPK",
                    quantity=Decimal("20"),
                    unit_text="KG",
                ),
                DynamicWorkLogMaterial(
                    material_text="URE",
                    quantity=Decimal("5"),
                    unit_text="KG",
                ),
            ],
        ),
    )

    result = dynamic_work_log_to_cultivation_log(
        request,
        client_record_id="test-dynamic-001",
        performed_at=datetime.fromisoformat(
            "2026-09-10T07:00:00+07:00"
        ),
        context=NextFarmContext(
            tenant_id="TENANT_001",
            user_id="USER_001",
            season_id="SEASON_001",
            plot_id="PLOT_A",
            task_id="TASK_001",
        ),
        confirmed=True,
    )
    assert result.activity_code == "BON_PHAN"

    assert result.lot_code == "LO_A"

    assert len(result.materials) == 2

    assert (
        result.materials[0].material_code
        == "NPK"
    )

    assert (
        result.materials[0].quantity
        == Decimal("20")
    )

    assert (
        result.materials[1].material_code
        == "URE"
    )

    assert (
        result.materials[1].quantity
        == Decimal("5")
    )


def test_create_work_log_rejects_incomplete_material():
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            plot_text="LO_A",
            activity_text="BON_PHAN",
            materials=[
                DynamicWorkLogMaterial(
                    material_text="NPK",
                    quantity=Decimal("20"),
                    unit_text=None,
                ),
            ],
        ),
    )

    try:
        dynamic_work_log_to_cultivation_log(
            request,
            client_record_id="test-dynamic-002",
            performed_at=datetime.fromisoformat(
                "2026-09-10T07:00:00+07:00"
            ),
        )

    except ValueError as error:
        assert (
            "materials[0]"
            in str(error)
        )

    else:
        raise AssertionError(
            "Expected incomplete material "
            "to be rejected."
        )

def test_dynamic_form_asks_for_missing_material_only():
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript=None,
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            plot_text="Lô A",
            activity_text="Bón phân",
            materials=[],
        ),
    )

    result = process_dynamic_create_work_log(
        request
    )

    assert result.missing_fields == [
        "materials[0].material_text"
    ]

    assert result.next_question == (
        "Bạn đã sử dụng vật tư nào?"
    )

    assert result.fields.plot_text == "Lô A"
    assert result.fields.activity_text == "Bón phân"

def test_dynamic_form_asks_one_missing_field_at_a_time():
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript=None,
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            plot_text=None,
            activity_text=None,
            materials=[],
        ),
    )

    result = process_dynamic_create_work_log(
        request
    )

    assert result.missing_fields == [
        "activity_text",
        "plot_text",
    ]

    assert result.next_question == (
        "Bạn đã thực hiện công việc gì?"
    )

def test_dynamic_form_preserves_existing_fields():
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript="NPK",
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            plot_text="Lô A",
            activity_text="Bón phân",
            materials=[],
        ),
    )

    result = process_dynamic_create_work_log(
        request
    )

    assert result.fields.plot_text == "Lô A"
    assert result.fields.activity_text == "Bón phân"

    assert len(result.fields.materials) == 1

    assert (
        result.fields.materials[0].material_text
        == "Phân NPK"
    )

def test_dynamic_form_preserves_fields_across_multiple_turns():
    # =========================================================
    # TURN 1
    # Người dùng chỉ nói công việc + lô.
    # =========================================================

    turn_1_request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript="Bón phân cho lô A",
        current_fields=DynamicWorkLogFields(
            result_status="completed",
        ),
    )

    turn_1 = process_dynamic_create_work_log(
        turn_1_request
    )

    assert turn_1.fields.activity_text == "Bón phân"
    assert turn_1.fields.plot_text == "Lô A"

    # Không được lấy nguyên transcript làm tên vật tư.
    assert turn_1.fields.materials == []

    assert turn_1.missing_fields == [
        "materials[0].material_text"
    ]

    assert turn_1.next_question == (
        "Bạn đã sử dụng vật tư nào?"
    )

    # =========================================================
    # TURN 2
    # Người dùng trả lời vật tư.
    # =========================================================

    turn_2_request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript="NPK",
        current_fields=turn_1.fields,
    )

    turn_2 = process_dynamic_create_work_log(
        turn_2_request
    )

    # Field cũ phải được giữ nguyên.
    assert turn_2.fields.activity_text == "Bón phân"
    assert turn_2.fields.plot_text == "Lô A"

    assert len(turn_2.fields.materials) == 1

    assert (
        turn_2.fields.materials[0].material_text
        == "Phân NPK"
    )

    assert turn_2.fields.materials[0].quantity is None
    assert turn_2.fields.materials[0].unit_text is None

    assert turn_2.missing_fields == [
        "materials[0].quantity"
    ]

    assert turn_2.next_question == (
        "Bạn đã sử dụng bao nhiêu?"
    )

    # =========================================================
    # TURN 3
    # Người dùng trả lời số lượng + đơn vị.
    # =========================================================

    turn_3_request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript="20 kg",
        current_fields=turn_2.fields,
    )

    turn_3 = process_dynamic_create_work_log(
        turn_3_request
    )

    # Các field từ turn 1 và turn 2 vẫn phải còn nguyên.
    assert turn_3.fields.activity_text == "Bón phân"
    assert turn_3.fields.plot_text == "Lô A"

    assert len(turn_3.fields.materials) == 1

    material = turn_3.fields.materials[0]

    assert material.material_text == "Phân NPK"
    assert material.quantity == Decimal("20")
    assert material.unit_text == "kg"

    # Đã đủ dữ liệu yêu cầu.
    assert turn_3.missing_fields == []

    assert turn_3.requires_confirmation is True

    assert (
        "Bạn xác nhận lưu nhật ký này không?"
        in turn_3.next_question
    )

def test_dynamic_form_does_not_erase_existing_fields_on_follow_up():
    existing_fields = DynamicWorkLogFields(
        result_status="completed",
        activity_text="Bón phân",
        plot_text="Lô A",
        materials=[
            DynamicWorkLogMaterial(
                material_text="Phân NPK",
                quantity=None,
                unit_text=None,
            )
        ],
    )

    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript="20 kg",
        current_fields=existing_fields,
    )

    result = process_dynamic_create_work_log(
        request
    )

    assert result.fields.activity_text == "Bón phân"
    assert result.fields.plot_text == "Lô A"

    material = result.fields.materials[0]

    assert material.material_text == "Phân NPK"
    assert material.quantity == Decimal("20")
    assert material.unit_text == "kg"

def test_dynamic_form_asks_for_standard_unit_when_ambiguous():
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript="xị",
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            activity_text="Bón phân",
            plot_text="Lô A",
            materials=[
                DynamicWorkLogMaterial(
                    material_text="Phân NPK",
                    quantity=Decimal("20"),
                    unit_text=None,
                )
            ],
        ),
    )

    result = process_dynamic_create_work_log(
        request
    )

    assert len(result.warnings) == 1

    warning = result.warnings[0]

    assert warning.code == "AMBIGUOUS_UNIT"
    assert (
        warning.field
        == "materials[0].unit_text"
    )

    assert (
        "materials[0].unit_text"
        in result.missing_fields
    )

    assert result.requires_confirmation is True

    assert result.next_question == (
        "Đơn vị này còn mơ hồ. "
        "Bạn vui lòng cho biết đơn vị chuẩn, "
        "ví dụ kg, lít, ml, bao hoặc chai."
    )

def test_dynamic_form_accepts_known_unit_without_warning():
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript="kg",
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            activity_text="Bón phân",
            plot_text="Lô A",
            materials=[
                DynamicWorkLogMaterial(
                    material_text="Phân NPK",
                    quantity=Decimal("20"),
                    unit_text=None,
                )
            ],
        ),
    )

    result = process_dynamic_create_work_log(
        request
    )

    assert (
        result.fields.materials[0].unit_text
        == "kg"
    )

    assert result.warnings == []
    assert result.missing_fields == []
    assert result.requires_confirmation is True

    assert (
        "Bạn xác nhận lưu nhật ký này không?"
        in result.next_question
    )

def test_dynamic_form_rejects_unknown_material_without_fallback():
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript="ABC Super 999",
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            activity_text="Bón phân",
            plot_text="Lô A",
            materials=[],
        ),
    )

    result = (
        process_dynamic_create_work_log(
            request
        )
    )

    assert len(
        result.fields.materials
    ) == 1

    assert (
        result.fields
        .materials[0]
        .material_text
        == "ABC Super 999"
    )

    assert any(
        warning.code
        == "UNKNOWN_MASTER_DATA"
        for warning
        in result.warnings
    )

    assert (
        "materials[0].material_text"
        in result.missing_fields
    )

    # Không được tự đổi thành vật tư khác.
    assert (
        result.fields
        .materials[0]
        .material_text
        != "Phân NPK"
    )

    assert (
        "chưa nhận diện được vật tư"
        in result.next_question
    )

def test_dynamic_form_conflict_does_not_overwrite_existing_value():
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript="Lô B",
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            activity_text="Tưới nước",
            plot_text="Lô A",
            materials=[],
        ),
    )

    result = (
        process_dynamic_create_work_log(
            request
        )
    )

    # Giá trị cũ phải được giữ.
    assert (
        result.fields.plot_text
        == "Lô A"
    )

    assert any(
        warning.code
        == "CONFLICTING_VALUE"
        for warning
        in result.warnings
    )

    assert (
        "khác với thông tin trước đó"
        in result.next_question
    )

    assert (
        result.requires_confirmation
        is True
    )

def test_dynamic_form_low_confidence_requires_confirmation(
    monkeypatch,
):
    from app.services import (
        dynamic_form_service,
    )

    original_resolver = (
        dynamic_form_service
        .resolve_master_data
    )

    def fake_resolver(
        data_type,
        text,
    ):
        if (
            data_type == "activity"
            and text == "Bón phân"
        ):
            return {
                "matched": True,
                "code": "BON_PHAN",
                "name": "Bón phân",
                "confidence": 0.80,
                "match_type": "fuzzy",
                "requires_confirmation": True,
            }

        return original_resolver(
            data_type,
            text,
        )

    monkeypatch.setattr(
        dynamic_form_service,
        "resolve_master_data",
        fake_resolver,
    )

    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript=None,
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            activity_text="Bón phân",
            plot_text="Lô A",
            materials=[
                DynamicWorkLogMaterial(
                    material_text="Phân NPK",
                    quantity=Decimal("20"),
                    unit_text="kg",
                )
            ],
        ),
    )

    result = (
        process_dynamic_create_work_log(
            request
        )
    )

    assert (
        result.field_confidence[
            "activity_text"
        ]
        == 0.80
    )

    assert any(
        warning.code
        == "LOW_CONFIDENCE"
        for warning
        in result.warnings
    )

    assert (
        result.requires_confirmation
        is True
    )

    assert (
        "chưa đủ độ tin cậy"
        in result.next_question
    )

def test_dynamic_form_uses_existing_business_rule_catalog():
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript=None,
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            activity_text="Tưới nước",
            plot_text="Lô A",
            materials=[],
        ),
    )

    result = (
        process_dynamic_create_work_log(
            request
        )
    )

    assert result.missing_fields == []

    assert any(
        warning.code
        == "BUSINESS_RULE_WARNING"
        for warning
        in result.warnings
    )

    assert (
        result.requires_confirmation
        is True
    )

    # Business warning không bắt chatbot
    # hỏi lại field đã đầy đủ.
    assert (
        "Bạn xác nhận lưu nhật ký này không?"
        in result.next_question
    )

def test_dynamic_form_complete_record_requests_final_confirmation():
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript=None,
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            activity_text="Bón phân",
            plot_text="Lô A",
            materials=[
                DynamicWorkLogMaterial(
                    material_text="Phân NPK",
                    quantity=Decimal("20"),
                    unit_text="kg",
                )
            ],
        ),
    )

    result = (
        process_dynamic_create_work_log(
            request
        )
    )

    assert result.missing_fields == []

    assert not any(
        warning.code in {
            "UNKNOWN_MASTER_DATA",
            "NAME_NOT_MATCHED",
            "AMBIGUOUS_UNIT",
            "CONFLICTING_VALUE",
            "LOW_CONFIDENCE",
        }
        for warning
        in result.warnings
    )

    assert (
        result.field_confidence[
            "activity_text"
        ]
        == 1.0
    )

    assert (
        result.field_confidence[
            "plot_text"
        ]
        == 1.0
    )

    assert (
        result.field_confidence[
            "materials[0].material_text"
        ]
        == 1.0
    )

    assert (
        result.requires_confirmation
        is True
    )

    assert "Bón phân" in (
        result.next_question
    )

    assert "Lô A" in (
        result.next_question
    )

    assert "Phân NPK" in (
        result.next_question
    )

    assert "20" in (
        result.next_question
    )

    assert (
        "xác nhận lưu nhật ký"
        in result.next_question
    )

def test_dynamic_form_plot_answer_does_not_pollute_material():
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript="Lô B",
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            activity_text="Bón phân",
            plot_text=None,
            materials=[
                DynamicWorkLogMaterial(
                    material_text=None,
                    quantity=Decimal("20"),
                    unit_text=None,
                )
            ],
        ),
    )

    result = process_dynamic_create_work_log(
        request
    )

    assert result.fields.plot_text == "Lô B"

    material = result.fields.materials[0]

    assert material.material_text is None
    assert material.quantity == Decimal("20")
    assert material.unit_text is None

    assert (
        "materials[0].material_text"
        in result.missing_fields
    )

def test_dynamic_form_confidence_below_060_requires_confirmation(
    monkeypatch,
):
    from app.services import dynamic_form_service

    original_resolver = (
        dynamic_form_service.resolve_master_data
    )

    def fake_resolver(
        data_type,
        text,
    ):
        if (
            data_type == "activity"
            and text == "Bón phân"
        ):
            return {
                "matched": True,
                "code": "BON_PHAN",
                "name": "Bón phân",
                "confidence": 0.40,
                "match_type": "fuzzy",
                "requires_confirmation": True,
            }

        return original_resolver(
            data_type,
            text,
        )

    monkeypatch.setattr(
        dynamic_form_service,
        "resolve_master_data",
        fake_resolver,
    )

    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript=None,
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            activity_text="Bón phân",
            plot_text="Lô A",
            materials=[
                DynamicWorkLogMaterial(
                    material_text="Phân NPK",
                    quantity=Decimal("20"),
                    unit_text="kg",
                )
            ],
        ),
    )

    result = process_dynamic_create_work_log(
        request
    )

    assert (
        result.field_confidence[
            "activity_text"
        ]
        == 0.40
    )

    assert any(
        warning.code == "LOW_CONFIDENCE"
        and warning.field == "activity_text"
        for warning in result.warnings
    )

    assert result.requires_confirmation is True

    assert (
        "chưa đủ độ tin cậy"
        in result.next_question
    )

def test_dynamic_form_material_name_with_number_does_not_pollute_quantity():
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript="ABC Super 999",
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            activity_text="Bón phân",
            plot_text="Lô A",
            materials=[],
        ),
    )

    result = process_dynamic_create_work_log(
        request
    )

    assert len(result.fields.materials) == 1

    material = result.fields.materials[0]

    assert material.material_text == "ABC Super 999"

    # "999" là một phần tên vật tư,
    # không phải quantity (số lượng).
    assert material.quantity is None
    assert material.unit_text is None

    assert any(
        warning.code == "UNKNOWN_MASTER_DATA"
        and warning.field
        == "materials[0].material_text"
        for warning in result.warnings
    )

    assert (
        "materials[0].material_text"
        in result.missing_fields
    )

def test_dynamic_form_quantity_only_answer_is_still_accepted():
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript="20",
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            activity_text="Bón phân",
            plot_text="Lô A",
            materials=[
                DynamicWorkLogMaterial(
                    material_text="Phân NPK",
                    quantity=None,
                    unit_text=None,
                )
            ],
        ),
    )

    result = process_dynamic_create_work_log(
        request
    )

    material = result.fields.materials[0]

    assert material.material_text == "Phân NPK"
    assert material.quantity == Decimal("20")
    assert material.unit_text is None

    assert result.missing_fields == [
        "materials[0].unit_text"
    ]

    assert result.next_question == (
        "Đơn vị của số lượng này là gì?"
    )

def test_dynamic_form_updates_correct_material_in_multi_material_flow():
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript="5 kg",
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            activity_text="Bón phân",
            plot_text="Lô A",
            materials=[
                DynamicWorkLogMaterial(
                    material_text="Phân NPK",
                    quantity=Decimal("20"),
                    unit_text="kg",
                ),
                DynamicWorkLogMaterial(
                    material_text="Phân Urê",
                    quantity=None,
                    unit_text=None,
                ),
            ],
        ),
    )

    result = process_dynamic_create_work_log(
        request
    )

    assert len(result.fields.materials) == 2

    first_material = (
        result.fields.materials[0]
    )

    second_material = (
        result.fields.materials[1]
    )

    # Material đầu tiên tuyệt đối không được
    # bị thay đổi.
    assert (
        first_material.material_text
        == "Phân NPK"
    )
    assert (
        first_material.quantity
        == Decimal("20")
    )
    assert first_material.unit_text == "kg"

    # Câu "5 kg" phải được điền vào material
    # thứ hai đang thiếu.
    assert (
        second_material.material_text
        == "Phân Urê"
    )
    assert (
        second_material.quantity
        == Decimal("5")
    )
    assert second_material.unit_text == "kg"

    assert result.missing_fields == []

    assert (
        "Phân NPK"
        in result.next_question
    )

    assert (
        "Phân Urê"
        in result.next_question
    )

    assert (
        "Bạn xác nhận lưu nhật ký này không?"
        in result.next_question
    )

def test_dynamic_form_fills_second_material_name_without_overwriting_first():
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript="Urê",
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            activity_text="Bón phân",
            plot_text="Lô A",
            materials=[
                DynamicWorkLogMaterial(
                    material_text="Phân NPK",
                    quantity=Decimal("20"),
                    unit_text="kg",
                ),
                DynamicWorkLogMaterial(
                    material_text=None,
                    quantity=Decimal("5"),
                    unit_text="kg",
                ),
            ],
        ),
    )

    result = process_dynamic_create_work_log(
        request
    )

    assert (
        result.fields.materials[0]
        .material_text
        == "Phân NPK"
    )

    assert (
        result.fields.materials[0]
        .quantity
        == Decimal("20")
    )

    assert (
        result.fields.materials[1]
        .material_text
        == "Phân urê"
    )

    assert (
        result.fields.materials[1]
        .quantity
        == Decimal("5")
    )

    assert (
        result.fields.materials[1]
        .unit_text
        == "kg"
    )

    assert result.missing_fields == []
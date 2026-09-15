from app.services.dynamic_form_service import (
    _normalize_missing_fields,
)


def test_harvest_complete_clears_stale_missing_field():
    data = {
        "fields": {
            "plot_text": "A1",
            "crop_text": "lúa",
            "quantity": 120,
            "unit_text": "kg",
            "harvest_date_text": "hôm nay",
        },
        "missing_fields": [
            "harvest_date_text"
        ],
        "warnings": [],
        "requires_confirmation": True,
        "next_question": (
            "Ngày thu hoạch là khi nào?"
        ),
    }

    result = _normalize_missing_fields(
        operation="CREATE_HARVEST",
        data=data,
    )

    assert result["missing_fields"] == []
    assert (
        result["requires_confirmation"]
        is False
    )
    assert result["next_question"] is None


def test_crop_type_missing_code_requires_confirmation():
    data = {
        "fields": {
            "crop_name": "lúa vàng",
            "crop_group_text": "lương thực",
            "crop_code_suggestion": None,
            "days_to_harvest": None,
        },
        "missing_fields": [],
        "warnings": [],
        "requires_confirmation": False,
        "next_question": None,
    }

    result = _normalize_missing_fields(
        operation="CREATE_CROP_TYPE",
        data=data,
    )

    assert result["missing_fields"] == [
        "crop_code_suggestion"
    ]
    assert (
        result["requires_confirmation"]
        is True
    )
    assert result["next_question"] == (
        "Mã gợi ý cho loại cây trồng này là gì?"
    )


def test_plot_requires_boundary():
    data = {
        "fields": {
            "plot_name_or_code": "A2",
            "region_text": "phía Bắc",
            "boundary_required": None,
            "owner_text": None,
            "current_crop_text": None,
            "location_hint_text": None,
        },
        "missing_fields": [],
        "warnings": [],
        "requires_confirmation": False,
        "next_question": None,
    }

    result = _normalize_missing_fields(
        operation="CREATE_PLOT",
        data=data,
    )

    assert result["missing_fields"] == [
        "boundary_required"
    ]
    assert (
        result["requires_confirmation"]
        is True
    )
    assert result["next_question"] == (
        "Bạn cần vẽ ranh giới lô trên bản đồ để tiếp tục."
    )


def test_work_log_material_requires_quantity_and_unit():
    data = {
        "fields": {
            "result_status": "completed",
            "materials": [
                {
                    "material_text": "NPK",
                    "quantity": None,
                    "unit_text": None,
                }
            ],
        },
        "missing_fields": [],
        "warnings": [],
        "requires_confirmation": False,
        "next_question": None,
    }

    result = _normalize_missing_fields(
        operation="CREATE_WORK_LOG",
        data=data,
    )

    assert (
        "materials[0].quantity"
        in result["missing_fields"]
    )
    assert (
        "materials[0].unit_text"
        in result["missing_fields"]
    )
    assert (
        result["requires_confirmation"]
        is True
    )


def test_complete_task_has_no_missing_fields():
    data = {
        "fields": {
            "season_text": "hè thu",
            "task_name": "phun thuốc",
            "task_type_text": "phun thuốc",
            "due_time_text": "20 tháng 9",
            "assignee_text": "anh Nam",
            "photo_required": None,
            "note": None,
        },
        "missing_fields": [
            "season_text",
            "due_time_text",
        ],
        "warnings": [],
        "requires_confirmation": True,
        "next_question": (
            "Thông tin còn thiếu?"
        ),
    }

    result = _normalize_missing_fields(
        operation="CREATE_TASK",
        data=data,
    )

    assert result["missing_fields"] == []
    assert (
        result["requires_confirmation"]
        is False
    )
    assert result["next_question"] is None


def test_task_asks_only_first_missing_group():
    data = {
        "fields": {
            "season_text": None,
            "task_name": "phun thuốc",
            "task_type_text": "phun thuốc",
            "due_time_text": None,
            "assignee_text": None,
            "photo_required": None,
            "note": None,
        },
        "missing_fields": [],
        "warnings": [],
        "requires_confirmation": False,
        "next_question": None,
    }

    result = _normalize_missing_fields(
        operation="CREATE_TASK",
        data=data,
    )

    assert result["missing_fields"] == [
        "season_text",
        "due_time_text",
    ]
    assert (
        result["requires_confirmation"]
        is True
    )
    assert result["next_question"] == (
        "Công việc này thuộc vụ nào?"
    )


def test_issue_report_asks_only_severity_first():
    data = {
        "fields": {
            "plot_text": "A1",
            "issue_type_text": "sâu cuốn lá",
            "severity_text": None,
            "description": None,
            "photo_required": None,
            "note": None,
        },
        "missing_fields": [],
        "warnings": [],
        "requires_confirmation": False,
        "next_question": None,
    }

    result = _normalize_missing_fields(
        operation="CREATE_ISSUE_REPORT",
        data=data,
    )

    assert result["missing_fields"] == [
        "severity_text",
        "description",
    ]
    assert (
        result["requires_confirmation"]
        is True
    )
    assert result["next_question"] == (
        "Mức độ của vấn đề là nhẹ, trung bình hay nặng?"
    )


def test_harvest_quantity_and_unit_are_one_group():
    data = {
        "fields": {
            "plot_text": "A1",
            "crop_text": "lúa",
            "quantity": None,
            "unit_text": None,
            "harvest_date_text": None,
            "photo_required": None,
            "note": None,
        },
        "missing_fields": [],
        "warnings": [],
        "requires_confirmation": False,
        "next_question": None,
    }

    result = _normalize_missing_fields(
        operation="CREATE_HARVEST",
        data=data,
    )

    assert result["missing_fields"] == [
        "quantity",
        "unit_text",
        "harvest_date_text",
    ]
    assert (
        result["requires_confirmation"]
        is True
    )
    assert result["next_question"] == (
        "Số lượng thu hoạch và đơn vị là bao nhiêu?"
    )


def test_work_log_material_quantity_and_unit_are_one_group():
    data = {
        "fields": {
            "result_status": "completed",
            "materials": [
                {
                    "material_text": "NPK",
                    "quantity": None,
                    "unit_text": None,
                }
            ],
        },
        "missing_fields": [],
        "warnings": [],
        "requires_confirmation": False,
        "next_question": None,
    }

    result = _normalize_missing_fields(
        operation="CREATE_WORK_LOG",
        data=data,
    )

    assert result["missing_fields"] == [
        "materials[0].quantity",
        "materials[0].unit_text",
    ]
    assert (
        result["requires_confirmation"]
        is True
    )
    assert result["next_question"] == (
        "Bạn đã sử dụng vật tư này với "
        "số lượng và đơn vị bao nhiêu?"
    )


def test_warning_without_missing_fields_asks_confirmation():
    data = {
        "fields": {
            "plot_text": "A1",
            "crop_text": "lúa",
            "quantity": 120,
            "unit_text": "kg",
            "harvest_date_text": "hôm nay",
        },
        "missing_fields": [],
        "warnings": [
            {
                "field": "harvest_date_text",
                "code": "LOW_CONFIDENCE",
                "message": (
                    "Ngày thu hoạch chưa chắc chắn."
                ),
            }
        ],
        "requires_confirmation": False,
        "next_question": None,
    }

    result = _normalize_missing_fields(
        operation="CREATE_HARVEST",
        data=data,
    )

    assert result["missing_fields"] == []
    assert (
        result["requires_confirmation"]
        is True
    )
    assert result["next_question"] == (
        "Có thông tin chưa chắc chắn. "
        "Bạn vui lòng kiểm tra và xác nhận lại."
    )
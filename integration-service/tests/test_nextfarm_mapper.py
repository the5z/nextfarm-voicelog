from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest

from app.services.nextfarm_mapper import (
    build_description,
    format_number,
    map_cultivation_log_to_nextfarm,
)


def build_cultivation_log() -> dict[str, Any]:
    """
    Tạo dữ liệu nhật ký hợp lệ dùng trong các bài test.
    """

    return {
        "schema_version": "1.0",
        "client_record_id": "mapper-test-001",
        "transcript": "Bón 20 kg NPK cho lô A1",
        "context": {
            "tenant_id": "tenant-001",
            "user_id": "user-301",
            "season_id": "season-401",
            "plot_id": "plot-201",
            "task_id": "task-101",
        },
        "lot_code": "LO_A",
        "activity_code": "BON_PHAN",
        "materials": [
            {
                "material_code": "NPK",
                "quantity": 20,
                "unit_code": "KG",
            }
        ],
        "performed_at": "2026-08-03T08:00:00+07:00",
        "performer_code": "NV001",
        "notes": "Bón phân lần một",
        "source": "voice",
        "confirmed": True,
    }


def test_format_number() -> None:
    """
    Số lượng phải được định dạng gọn, không dư số 0.
    """

    assert format_number(20) == "20"
    assert format_number(20.0) == "20"
    assert format_number(20.5) == "20.5"
    assert format_number(Decimal("20.000")) == "20"
    assert format_number(Decimal("20.500")) == "20.5"


def test_build_description() -> None:
    """
    Mô tả phải chứa transcript, vật tư, ghi chú và mã bản ghi.
    """

    description = build_description(
        build_cultivation_log()
    )

    assert "Bón 20 kg NPK cho lô A1" in description
    assert "NPK - 20 - KG" in description
    assert "Bón phân lần một" in description
    assert "mapper-test-001" in description


def test_map_without_external_mapping() -> None:
    """Context NextFarm phải được map theo đúng semantic field."""

    result = map_cultivation_log_to_nextfarm(
        build_cultivation_log()
    )

    assert result["name"] == "Bón phân"
    assert result["location"] == "plot-201"
    assert result["assigned_to"] == "user-301"
    assert result["category_task_id"] == "task-101"
    assert result["season_id"] == "season-401"
    assert result["metadata"]["tenant_id"] == "tenant-001"

    assert result["start"] == (
        "2026-08-03T08:00:00+07:00"
    )

    assert result["end"] == result["start"]

    assert result["metadata"]["client_record_id"] == (
        "mapper-test-001"
    )

    assert result["metadata"]["integration_source"] == (
        "nextfarm-voicelog"
    )


def test_map_with_external_mapping() -> None:
    """
    Khi có mapping, mã nội bộ phải được đổi thành ID NextFarm.
    """

    result = map_cultivation_log_to_nextfarm(
        build_cultivation_log(),
        activity_mapping={
            "BON_PHAN": 101,
        },
        lot_mapping={
            "LO_A": 201,
        },
        performer_mapping={
            "NV001": 301,
        },
    )

    assert result["category_task_id"] == "task-101"
    assert result["location"] == "plot-201"
    assert result["assigned_to"] == "user-301"
    assert result["season_id"] == "season-401"


def test_map_accepts_datetime() -> None:
    """
    Mapper phải xử lý được datetime ngoài chuỗi ISO 8601.
    """

    cultivation_log = build_cultivation_log()

    cultivation_log["performed_at"] = datetime(
        2026,
        8,
        3,
        1,
        0,
        tzinfo=timezone.utc,
    )

    result = map_cultivation_log_to_nextfarm(
        cultivation_log
    )

    assert result["start"] == (
        "2026-08-03T01:00:00+00:00"
    )


def test_map_rejects_missing_client_record_id() -> None:
    """
    Nhật ký thiếu client_record_id không được chuyển đổi.
    """

    cultivation_log = build_cultivation_log()
    cultivation_log.pop("client_record_id")

    with pytest.raises(
        ValueError,
        match="Thiếu client_record_id",
    ):
        map_cultivation_log_to_nextfarm(
            cultivation_log
        )


def test_map_rejects_invalid_performed_at() -> None:
    """
    Thời gian không hợp lệ phải được báo lỗi.
    """

    cultivation_log = build_cultivation_log()
    cultivation_log["performed_at"] = "khong-hop-le"

    with pytest.raises(
        ValueError,
        match="ISO 8601",
    ):
        map_cultivation_log_to_nextfarm(
            cultivation_log
        )


def test_map_allows_optional_activity_and_lot_with_context() -> None:
    """
    CREATE_WORK_LOG V3.1 cho phép thiếu plot/activity.

    Khi đã có canonical NextFarm context,
    mapper phải dùng plot_id/task_id.
    """

    cultivation_log = build_cultivation_log()

    cultivation_log["activity_code"] = None
    cultivation_log["lot_code"] = None

    result = map_cultivation_log_to_nextfarm(
        cultivation_log
    )

    assert (
        result["name"]
        == "Nhật ký canh tác"
    )

    assert (
        result["location"]
        == "plot-201"
    )

    assert (
        result["category_task_id"]
        == "task-101"
    )

    assert (
        result["location"]
        != "None"
    )

    assert (
        result["category_task_id"]
        != "None"
    )


def test_map_optional_codes_do_not_become_string_none() -> None:
    """
    None không được biến thành canonical code giả "None".
    """

    cultivation_log = build_cultivation_log()

    cultivation_log["context"] = None
    cultivation_log["activity_code"] = None
    cultivation_log["lot_code"] = None

    result = map_cultivation_log_to_nextfarm(
        cultivation_log
    )

    assert (
        result["name"]
        == "Nhật ký canh tác"
    )

    assert result["location"] is None

    assert (
        result["category_task_id"]
        is None
    )
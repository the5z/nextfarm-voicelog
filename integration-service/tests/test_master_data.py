from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@pytest.mark.parametrize(
    ("data_type", "text", "expected_code"),
    [
        ("activity", "rải phân", "BON_PHAN"),
        ("activity", "xịt thuốc", "PHUN_THUOC"),
        ("activity", "Cho bò ăn", "CHO_BO_AN"),
        ("activity", "cho bo an", "CHO_BO_AN"),
        ("unit", "kg", "KG"),
        ("unit", "ky", "KG"),
        ("lot", "Lô A", "LO_A"),
        ("lot", "lo a", "LO_A"),
        ("lot", "khu vực b", "LO_B"),
        ("material", "Cám", "CAM"),
        ("material", "cam", "CAM"),
        ("material", "phân NPK", "NPK"),
        ("material", "ure", "URE"),
    ],
)
def test_resolve_exact_master_data_values(
    data_type: str,
    text: str,
    expected_code: str,
) -> None:
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": data_type,
            "text": text,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True
    assert body["code"] == expected_code
    assert body["confidence"] == 1.0
    assert body["requires_confirmation"] is False


def test_require_confirmation_for_ambiguous_unit() -> None:
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "unit",
            "text": "xị",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is False
    assert body["code"] is None
    assert body["name"] is None
    assert body["confidence"] == 0.0
    assert body["requires_confirmation"] is True
    assert "khác nhau theo khu vực" in body["message"]


def test_unknown_value_requires_confirmation() -> None:
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "activity",
            "text": "hoạt động hoàn toàn không tồn tại xyz",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is False
    assert body["code"] is None
    assert body["requires_confirmation"] is True
    assert body["message"] == (
        "Không tìm thấy giá trị phù hợp trong danh mục."
    )


def test_get_activities_contains_cattle_feeding() -> None:
    response = client.get(
        "/api/master-data/activities"
    )

    assert response.status_code == 200

    records = response.json()
    records_by_code = {
        record["code"]: record
        for record in records
    }

    assert "CHO_BO_AN" in records_by_code
    assert (
        records_by_code["CHO_BO_AN"]["name"]
        == "Cho bò ăn"
    )


def test_get_units_contains_kilogram() -> None:
    response = client.get(
        "/api/master-data/units"
    )

    assert response.status_code == 200

    records = response.json()
    codes = {
        record["code"]
        for record in records
    }

    assert "KG" in codes


def test_get_lots_returns_available_lots() -> None:
    response = client.get(
        "/api/master-data/lots"
    )

    assert response.status_code == 200

    records = response.json()
    records_by_code = {
        record["code"]: record
        for record in records
    }

    assert "LO_A" in records_by_code
    assert "LO_B" in records_by_code
    assert records_by_code["LO_A"]["name"] == "Lô A"
    assert records_by_code["LO_B"]["name"] == "Lô B"


def test_get_materials_returns_available_materials() -> None:
    response = client.get(
        "/api/master-data/materials"
    )

    assert response.status_code == 200

    records = response.json()
    records_by_code = {
        record["code"]: record
        for record in records
    }

    assert "CAM" in records_by_code
    assert "NPK" in records_by_code
    assert "URE" in records_by_code
    assert records_by_code["CAM"]["name"] == "Cám"


def test_resolve_rejects_invalid_data_type() -> None:
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "invalid",
            "text": "Lô A",
        },
    )

    assert response.status_code == 422


def test_resolve_rejects_empty_text() -> None:
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "lot",
            "text": "",
        },
    )

    assert response.status_code == 422

def test_resolve_activity_asr_like_text(client):
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "activity",
            "text": "Cho bỏ ăn",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True
    assert body["code"] == "CHO_BO_AN"


def test_resolve_activity_without_accents(client):
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "activity",
            "text": "Cho bo an",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True
    assert body["code"] == "CHO_BO_AN"


def test_resolve_material_asr_like_text(client):
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "material",
            "text": "Cảm",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True
    assert body["code"] == "CAM"


def test_resolve_material_without_accents(client):
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "material",
            "text": "cam",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True
    assert body["code"] == "CAM"


def test_resolve_unit_spoken_ky(client):
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "unit",
            "text": "ký",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True
    assert body["code"] == "KG"


def test_resolve_lot_without_accents(client):
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "lot",
            "text": "lo a",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True
    assert body["code"] == "LO_A"

def test_resolve_cultivation_success(client):
    response = client.post(
        "/api/master-data/resolve-cultivation",
        json={
            "activity_text": "Cho bò ăn",
            "lot_text": "Lô A",
            "materials": [
                {
                    "material_text": "Cám",
                    "quantity": 20,
                    "unit_text": "kg",
                }
            ],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["activity"]["matched"] is True
    assert body["activity"]["code"] == "CHO_BO_AN"

    assert body["lot"]["matched"] is True
    assert body["lot"]["code"] == "LO_A"

    assert body["materials"][0]["material"]["matched"] is True
    assert body["materials"][0]["material"]["code"] == "CAM"

    assert body["materials"][0]["quantity"] == 20

    assert body["materials"][0]["unit"]["matched"] is True
    assert body["materials"][0]["unit"]["code"] == "KG"

    assert body["requires_confirmation"] is False


def test_resolve_cultivation_missing_activity(client):
    response = client.post(
        "/api/master-data/resolve-cultivation",
        json={
            "activity_text": None,
            "lot_text": "Lô A",
            "materials": [
                {
                    "material_text": "Cám",
                    "quantity": 20,
                    "unit_text": "kg",
                }
            ],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["activity"]["matched"] is False
    assert body["activity"]["code"] is None
    assert body["activity"]["requires_confirmation"] is True

    assert body["requires_confirmation"] is True


def test_resolve_cultivation_ambiguous_unit(client):
    response = client.post(
        "/api/master-data/resolve-cultivation",
        json={
            "activity_text": "Bón phân",
            "lot_text": "Lô A",
            "materials": [
                {
                    "material_text": "Phân NPK",
                    "quantity": 1,
                    "unit_text": "xị",
                }
            ],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["materials"][0]["unit"]["matched"] is False
    assert body["materials"][0]["unit"]["code"] is None
    assert (
        body["materials"][0]["unit"]["requires_confirmation"]
        is True
    )

    assert body["requires_confirmation"] is True

def test_resolve_alias_returns_match_metadata(client):
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "activity",
            "text": "cho gia súc ăn",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True
    assert body["code"] == "CHO_BO_AN"
    assert body["match_type"] == "alias"
    assert body["matched_text"] == "cho gia súc ăn"
    assert body["confidence"] == 1.0
    assert body["requires_confirmation"] is False


def test_resolve_fuzzy_returns_existing_code_and_requires_confirmation(client):
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "activity",
            "text": "cho ra súc ăn",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True
    assert body["code"] == "CHO_BO_AN"
    assert body["match_type"] == "fuzzy"
    assert body["matched_text"] == "cho gia súc ăn"
    assert body["confidence"] < 1.0
    assert body["requires_confirmation"] is True


def test_resolve_unknown_returns_none_match_type(client):
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "activity",
            "text": "vệ sinh kho hoàn toàn mới",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is False
    assert body["code"] is None
    assert body["match_type"] == "none"
    assert body["matched_text"] is None
    assert body["requires_confirmation"] is True


def test_resolve_ambiguous_returns_ambiguous_match_type(client):
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "unit",
            "text": "xị",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is False
    assert body["code"] is None
    assert body["match_type"] == "ambiguous"
    assert body["matched_text"] is None
    assert body["requires_confirmation"] is True


def test_resolve_cultivation_fuzzy_activity(client):
    response = client.post(
        "/api/master-data/resolve-cultivation",
        json={
            "activity_text": "cho ra súc ăn",
            "lot_text": "Lô A",
            "materials": [
                {
                    "material_text": "Cám",
                    "quantity": 20,
                    "unit_text": "kg",
                }
            ],
            "time_text": "07:00",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["activity"]["code"] == "CHO_BO_AN"
    assert body["activity"]["match_type"] == "fuzzy"
    assert body["activity"]["matched_text"] == "cho gia súc ăn"
    assert body["activity"]["requires_confirmation"] is True

    assert body["lot"]["code"] == "LO_A"
    assert body["materials"][0]["material"]["code"] == "CAM"
    assert body["materials"][0]["unit"]["code"] == "KG"

    assert body["time_text"] == "07:00"
    assert body["requires_confirmation"] is True

def test_resolve_cultivation_unknown_activity_does_not_invent_code(client):
    response = client.post(
        "/api/master-data/resolve-cultivation",
        json={
            "activity_text": "vệ sinh chuồng hoàn toàn mới xyz",
            "lot_text": "Lô A",
            "materials": [],
            "time_text": "07:00",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["activity"]["matched"] is False
    assert body["activity"]["code"] is None
    assert body["activity"]["match_type"] == "none"
    assert body["activity"]["matched_text"] is None
    assert body["activity"]["requires_confirmation"] is True

    assert body["requires_confirmation"] is True


def test_resolve_cultivation_missing_quantity_requires_confirmation(client):
    response = client.post(
        "/api/master-data/resolve-cultivation",
        json={
            "activity_text": "Cho bò ăn",
            "lot_text": "Lô A",
            "materials": [
                {
                    "material_text": "Cám",
                    "quantity": None,
                    "unit_text": "kg",
                }
            ],
            "time_text": "07:00",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["materials"][0]["material"]["code"] == "CAM"
    assert body["materials"][0]["unit"]["code"] == "KG"
    assert body["materials"][0]["quantity"] is None

    assert body["requires_confirmation"] is True


def test_resolve_cultivation_missing_unit_requires_confirmation(client):
    response = client.post(
        "/api/master-data/resolve-cultivation",
        json={
            "activity_text": "Cho bò ăn",
            "lot_text": "Lô A",
            "materials": [
                {
                    "material_text": "Cám",
                    "quantity": 20,
                    "unit_text": None,
                }
            ],
            "time_text": "07:00",
        },
    )

    assert response.status_code == 200

    body = response.json()

    unit = body["materials"][0]["unit"]

    assert unit["matched"] is False
    assert unit["code"] is None
    assert unit["match_type"] == "none"
    assert unit["requires_confirmation"] is True

    assert body["requires_confirmation"] is True


def test_resolve_cultivation_without_material_is_valid_for_activity(client):
    response = client.post(
        "/api/master-data/resolve-cultivation",
        json={
            "activity_text": "Làm cỏ",
            "lot_text": "Lô A",
            "materials": [],
            "time_text": "07:00",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["activity"]["code"] == "LAM_CO"
    assert body["lot"]["code"] == "LO_A"
    assert body["materials"] == []

    assert body["requires_confirmation"] is False


def test_resolve_cultivation_time_text_is_preserved(client):
    response = client.post(
        "/api/master-data/resolve-cultivation",
        json={
            "activity_text": "Làm cỏ",
            "lot_text": "Lô A",
            "materials": [],
            "time_text": "Sáng nay",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["time_text"] == "Sáng nay"

    # time_text không phải Master Data.
    # Integration không tự biến nó thành performed_at.
    assert body["requires_confirmation"] is False
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
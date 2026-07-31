from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_validate_valid_cultivation_log() -> None:
    payload = {
        "schema_version": "1.0",
        "client_record_id": "record-001",
        "transcript": "Bón 20 kg NPK cho lô A1 lúc 7 giờ",
        "lot_code": "LO_A1",
        "activity_code": "BON_PHAN",
        "materials": [
            {
                "material_code": "NPK",
                "quantity": 20,
                "unit_code": "KG",
            }
        ],
        "performed_at": "2026-07-31T07:00:00+07:00",
        "performer_code": "NV001",
        "source": "voice",
        "confirmed": True,
    }

    response = client.post(
        "/api/cultivation-logs/validate",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["valid"] is True
    assert body["errors"] == []
    assert body["normalized_data"]["lot_code"] == "LO_A1"


def test_reject_zero_quantity() -> None:
    payload = {
        "client_record_id": "record-002",
        "lot_code": "LO_A1",
        "activity_code": "BON_PHAN",
        "materials": [
            {
                "material_code": "NPK",
                "quantity": 0,
                "unit_code": "KG",
            }
        ],
        "performed_at": "2026-07-31T07:00:00+07:00",
        "confirmed": True,
    }

    response = client.post(
        "/api/cultivation-logs/validate",
        json=payload,
    )

    assert response.status_code == 422
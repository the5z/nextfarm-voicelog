from fastapi.testclient import TestClient

from app.main import app
from app.services.log_service import clear_logs


client = TestClient(app)


def create_payload(record_id: str) -> dict:
    return {
        "schema_version": "1.0",
        "client_record_id": record_id,
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


def setup_function() -> None:
    clear_logs()


def test_save_confirmed_log() -> None:
    response = client.post(
        "/api/cultivation-logs",
        json=create_payload("save-test-001"),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["status"] == "saved"
    assert body["data"]["client_record_id"] == "save-test-001"


def test_reject_unconfirmed_log() -> None:
    payload = create_payload("save-test-002")
    payload["confirmed"] = False

    response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNCONFIRMED_RECORD"


def test_prevent_duplicate_record() -> None:
    payload = create_payload("duplicate-test-001")

    first_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    second_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert first_response.status_code == 201
    assert first_response.json()["status"] == "saved"

    assert second_response.status_code == 201
    assert second_response.json()["status"] == "already_exists"


def test_list_saved_logs() -> None:
    client.post(
        "/api/cultivation-logs",
        json=create_payload("list-test-001"),
    )

    response = client.get("/api/cultivation-logs")

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) == 1
from fastapi.testclient import TestClient

from app.main import app
from app.services.log_service import clear_logs


client = TestClient(app)


def create_record(
    record_id: str,
    *,
    confirmed: bool = True,
    quantity: int = 20,
) -> dict:
    return {
        "schema_version": "1.0",
        "client_record_id": record_id,
        "transcript": (
            "Bón 20 kg NPK cho lô A1 lúc 7 giờ"
        ),
        "lot_code": "LO_A1",
        "activity_code": "BON_PHAN",
        "materials": [
            {
                "material_code": "NPK",
                "quantity": quantity,
                "unit_code": "KG",
            }
        ],
        "performed_at": (
            "2026-08-01T07:00:00+07:00"
        ),
        "performer_code": "NV001",
        "notes": None,
        "source": "voice",
        "confirmed": confirmed,
    }


def setup_function() -> None:
    """
    Xóa kho dữ liệu RAM trước mỗi bài test.
    """

    clear_logs()


def test_sync_multiple_valid_records() -> None:
    payload = {
        "device_id": "android-device-001",
        "synced_at": (
            "2026-08-01T22:30:00+07:00"
        ),
        "records": [
            create_record("offline-001"),
            create_record("offline-002"),
        ],
    }

    response = client.post(
        "/api/sync/logs",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["summary"]["total"] == 2
    assert body["summary"]["saved"] == 2
    assert body["summary"]["duplicated"] == 0
    assert body["summary"]["failed"] == 0

    assert body["results"][0]["status"] == "saved"
    assert body["results"][1]["status"] == "saved"


def test_sync_duplicate_record() -> None:
    record = create_record("offline-duplicate-001")

    first_response = client.post(
        "/api/sync/logs",
        json={
            "device_id": "android-device-001",
            "records": [record],
        },
    )

    second_response = client.post(
        "/api/sync/logs",
        json={
            "device_id": "android-device-001",
            "records": [record],
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert (
        first_response.json()["results"][0]["status"]
        == "saved"
    )

    second_body = second_response.json()

    assert (
        second_body["results"][0]["status"]
        == "already_exists"
    )
    assert second_body["summary"]["duplicated"] == 1
    assert second_body["summary"]["saved"] == 0


def test_sync_partial_failure() -> None:
    payload = {
        "device_id": "android-device-002",
        "records": [
            create_record("offline-valid"),
            create_record(
                "offline-unconfirmed",
                confirmed=False,
            ),
            create_record(
                "offline-invalid-quantity",
                quantity=0,
            ),
        ],
    }

    response = client.post(
        "/api/sync/logs",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    # Có bản lỗi nên success bằng false.
    assert body["success"] is False

    assert body["summary"]["total"] == 3
    assert body["summary"]["saved"] == 1
    assert body["summary"]["duplicated"] == 0
    assert body["summary"]["failed"] == 2

    statuses = [
        result["status"]
        for result in body["results"]
    ]

    assert statuses == [
        "saved",
        "failed",
        "failed",
    ]


def test_sync_missing_client_record_id() -> None:
    invalid_record = create_record("temporary-id")
    invalid_record.pop("client_record_id")

    response = client.post(
        "/api/sync/logs",
        json={
            "device_id": "android-device-003",
            "records": [invalid_record],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is False
    assert body["summary"]["failed"] == 1

    result = body["results"][0]

    assert result["client_record_id"] is None
    assert result["status"] == "failed"
    assert len(result["errors"]) > 0
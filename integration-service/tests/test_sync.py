from copy import deepcopy
from typing import Any

from fastapi.testclient import TestClient


def build_sync_record(
    client_record_id: str = "sync-record-001",
) -> dict[str, Any]:
    """
    Tạo một nhật ký hợp lệ dùng cho API đồng bộ.
    """

    return {
        "schema_version": "1.0",
        "client_record_id": client_record_id,
        "transcript": "Bón 20 kg NPK cho lô A1",
        "lot_code": "LO_A",
        "activity_code": "BON_PHAN",
        "materials": [
            {
                "material_code": "NPK",
                "quantity": 20,
                "unit_code": "KG",
            }
        ],
        "performed_at": "2026-08-02T07:00:00+07:00",
        "performer_code": "NV001",
        "notes": None,
        "source": "sync",
        "confirmed": True,
    }


def build_sync_request(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Tạo request đồng bộ từ thiết bị.
    """

    return {
        "device_id": "android-test-device",
        "synced_at": "2026-08-02T08:00:00+07:00",
        "records": records,
    }


def test_sync_multiple_valid_records(
    client: TestClient,
) -> None:
    """
    Đồng bộ nhiều bản ghi hợp lệ phải lưu được toàn bộ.
    """

    first_record = build_sync_record(
        client_record_id="sync-valid-001"
    )

    second_record = deepcopy(first_record)
    second_record["client_record_id"] = "sync-valid-002"
    second_record["lot_code"] = "LO_B"
    second_record["activity_code"] = "TUOI_NUOC"
    second_record["transcript"] = (
        "Tưới nước cho lô A2"
    )
    second_record["materials"] = []

    payload = build_sync_request(
        records=[
            first_record,
            second_record,
        ]
    )

    response = client.post(
        "/api/sync/logs",
        json=payload,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["success"] is True
    assert response_data["device_id"] == (
        "android-test-device"
    )

    assert response_data["summary"]["total"] == 2
    assert response_data["summary"]["saved"] == 2
    assert response_data["summary"]["duplicated"] == 0
    assert response_data["summary"]["failed"] == 0

    assert len(response_data["results"]) == 2

    assert all(
        result["status"] == "saved"
        for result in response_data["results"]
    )


def test_sync_duplicate_record(
    client: TestClient,
) -> None:
    """
    Đồng bộ lại bản ghi cũ phải trả về already_exists.
    """

    record = build_sync_record(
        client_record_id="sync-duplicate-001"
    )

    payload = build_sync_request(
        records=[record]
    )

    first_response = client.post(
        "/api/sync/logs",
        json=payload,
    )

    second_response = client.post(
        "/api/sync/logs",
        json=payload,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data["summary"]["saved"] == 1
    assert first_data["summary"]["duplicated"] == 0

    assert second_data["summary"]["saved"] == 0
    assert second_data["summary"]["duplicated"] == 1
    assert second_data["summary"]["failed"] == 0

    assert (
        second_data["results"][0]["status"]
        == "already_exists"
    )


def test_sync_partial_failure(
    client: TestClient,
) -> None:
    """
    Một bản ghi lỗi không được làm thất bại toàn bộ request.
    """

    valid_record = build_sync_record(
        client_record_id="sync-partial-valid"
    )

    invalid_record = build_sync_record(
        client_record_id="sync-partial-invalid"
    )

    invalid_record["confirmed"] = False

    payload = build_sync_request(
        records=[
            valid_record,
            invalid_record,
        ]
    )

    response = client.post(
        "/api/sync/logs",
        json=payload,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["success"] is False

    assert response_data["summary"]["total"] == 2
    assert response_data["summary"]["saved"] == 1
    assert response_data["summary"]["duplicated"] == 0
    assert response_data["summary"]["failed"] == 1

    result_by_id = {
        result["client_record_id"]: result
        for result in response_data["results"]
    }

    assert (
        result_by_id["sync-partial-valid"]["status"]
        == "saved"
    )

    invalid_result = result_by_id[
        "sync-partial-invalid"
    ]

    assert invalid_result["status"] == "failed"
    assert invalid_result["success"] is False

    assert (
        invalid_result["errors"][0]["code"]
        == "UNCONFIRMED_RECORD"
    )


def test_sync_missing_client_record_id(
    client: TestClient,
) -> None:
    """
    Bản ghi thiếu client_record_id phải được báo lỗi riêng.
    """

    record = build_sync_record()
    record.pop("client_record_id")

    payload = build_sync_request(
        records=[record]
    )

    response = client.post(
        "/api/sync/logs",
        json=payload,
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["success"] is False
    assert response_data["summary"]["total"] == 1
    assert response_data["summary"]["saved"] == 0
    assert response_data["summary"]["duplicated"] == 0
    assert response_data["summary"]["failed"] == 1

    failed_result = response_data["results"][0]

    assert failed_result["status"] == "failed"
    assert failed_result["success"] is False
    assert failed_result["client_record_id"] == (
        "unknown-record-1"
    )

    error_fields = {
        error["field"]
        for error in failed_result["errors"]
    }

    assert "client_record_id" in error_fields
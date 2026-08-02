from copy import deepcopy
from typing import Any

from fastapi.testclient import TestClient


def build_valid_log(
    client_record_id: str = "test-log-001",
) -> dict[str, Any]:
    """
    Tạo một bản ghi nhật ký hợp lệ dùng chung cho các bài test.
    """

    return {
        "schema_version": "1.0",
        "client_record_id": client_record_id,
        "transcript": "Bón 20 kg NPK cho lô A1",
        "lot_code": "LO_A1",
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
        "notes": "Bón phân lần một",
        "source": "voice",
        "confirmed": True,
    }


def test_save_confirmed_log(
    client: TestClient,
) -> None:
    """
    Nhật ký đã xác nhận phải được lưu thành công.
    """

    payload = build_valid_log()

    response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["success"] is True
    assert response_data["status"] == "saved"

    stored_log = response_data["data"]

    assert stored_log["client_record_id"] == "test-log-001"
    assert stored_log["lot_code"] == "LO_A1"
    assert stored_log["activity_code"] == "BON_PHAN"
    assert stored_log["confirmed"] is True
    assert stored_log["status"] == "saved"

    assert len(stored_log["materials"]) == 1
    assert (
        stored_log["materials"][0]["material_code"]
        == "NPK"
    )
    assert stored_log["materials"][0]["quantity"] == 20
    assert stored_log["materials"][0]["unit_code"] == "KG"


def test_reject_unconfirmed_log(
    client: TestClient,
) -> None:
    """
    Nhật ký chưa xác nhận không được lưu vào database.
    """

    payload = build_valid_log(
        client_record_id="test-unconfirmed-001"
    )

    payload["confirmed"] = False

    response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert response.status_code == 400

    response_data = response.json()

    assert response_data["detail"]["code"] == (
        "UNCONFIRMED_RECORD"
    )

    list_response = client.get(
        "/api/cultivation-logs"
    )

    assert list_response.status_code == 200
    assert list_response.json()["data"] == []


def test_prevent_duplicate_record(
    client: TestClient,
) -> None:
    """
    Gửi lại cùng client_record_id không được tạo bản ghi mới.
    """

    payload = build_valid_log(
        client_record_id="test-duplicate-001"
    )

    first_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    second_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data["status"] == "saved"
    assert second_data["status"] == "already_exists"

    assert (
        first_data["data"]["id"]
        == second_data["data"]["id"]
    )

    list_response = client.get(
        "/api/cultivation-logs"
    )

    stored_logs = list_response.json()["data"]

    assert len(stored_logs) == 1


def test_list_saved_logs(
    client: TestClient,
) -> None:
    """
    API danh sách phải trả về các nhật ký đã lưu.
    """

    first_payload = build_valid_log(
        client_record_id="test-list-001"
    )

    second_payload = deepcopy(first_payload)
    second_payload["client_record_id"] = "test-list-002"
    second_payload["lot_code"] = "LO_A2"
    second_payload["transcript"] = (
        "Tưới nước cho lô A2"
    )
    second_payload["activity_code"] = "TUOI_NUOC"
    second_payload["materials"] = []

    first_response = client.post(
        "/api/cultivation-logs",
        json=first_payload,
    )

    second_response = client.post(
        "/api/cultivation-logs",
        json=second_payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get(
        "/api/cultivation-logs"
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["success"] is True
    assert len(response_data["data"]) == 2

    client_record_ids = {
        record["client_record_id"]
        for record in response_data["data"]
    }

    assert client_record_ids == {
        "test-list-001",
        "test-list-002",
    }
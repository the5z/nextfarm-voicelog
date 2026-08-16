from typing import Any

from fastapi.testclient import TestClient


def build_history_test_log(
    client_record_id: str,
    *,
    confirmed: bool = True,
) -> dict[str, Any]:
    """
    Tạo Cultivation Log dùng cho test Integration History.
    """

    return {
        "schema_version": "1.0",
        "client_record_id": client_record_id,
        "transcript": "Cho bò ăn 20 kg cám tại lô A",
        "lot_code": "LO_A",
        "activity_code": "CHO_BO_AN",
        "materials": [
            {
                "material_code": "CAM",
                "quantity": 20,
                "unit_code": "KG",
            }
        ],
        "performed_at": "2026-08-14T07:00:00+07:00",
        "performer_code": None,
        "notes": None,
        "source": "voice",
        "confirmed": confirmed,
    }


def test_save_log_creates_success_history(
    client: TestClient,
) -> None:
    """
    Lưu Cultivation Log thành công phải tạo history.
    """

    client_record_id = "history-save-001"

    response = client.post(
        "/api/cultivation-logs",
        json=build_history_test_log(
            client_record_id
        ),
    )

    assert response.status_code == 201
    assert response.json()["status"] == "saved"

    history_response = client.get(
        "/api/history",
        params={
            "client_record_id": client_record_id,
        },
    )

    assert history_response.status_code == 200

    body = history_response.json()

    assert body["success"] is True

    save_events = [
        item
        for item in body["data"]
        if item["event_type"]
        == "save_cultivation_log"
    ]

    assert len(save_events) == 1

    history = save_events[0]

    assert history["client_record_id"] == (
        client_record_id
    )
    assert history["status"] == "success"
    assert history["http_status"] == 201

    assert (
        history["request_payload"][
            "client_record_id"
        ]
        == client_record_id
    )

    assert (
        history["response_payload"]["status"]
        == "saved"
    )


def test_unconfirmed_log_creates_failed_history(
    client: TestClient,
) -> None:
    """
    Nhật ký chưa xác nhận phải tạo failed history.
    """

    client_record_id = "history-failed-save-001"

    response = client.post(
        "/api/cultivation-logs",
        json=build_history_test_log(
            client_record_id,
            confirmed=False,
        ),
    )

    assert response.status_code == 400

    history_response = client.get(
        "/api/history",
        params={
            "client_record_id": client_record_id,
        },
    )

    assert history_response.status_code == 200

    events = history_response.json()["data"]

    save_events = [
        item
        for item in events
        if item["event_type"]
        == "save_cultivation_log"
    ]

    assert len(save_events) == 1

    history = save_events[0]

    assert history["status"] == "failed"
    assert history["http_status"] == 400

    assert (
        history["response_payload"][
            "detail"
        ]["code"]
        == "UNCONFIRMED_RECORD"
    )


def test_duplicate_save_is_recorded_in_history(
    client: TestClient,
) -> None:
    """
    Request gửi trùng vẫn phải xuất hiện trong history.
    """

    client_record_id = "history-duplicate-001"

    payload = build_history_test_log(
        client_record_id
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

    assert (
        second_response.json()["status"]
        == "already_exists"
    )

    history_response = client.get(
        "/api/history",
        params={
            "client_record_id": client_record_id,
        },
    )

    assert history_response.status_code == 200

    save_events = [
        item
        for item
        in history_response.json()["data"]
        if item["event_type"]
        == "save_cultivation_log"
    ]

    assert len(save_events) == 2

    response_statuses = {
        item["response_payload"]["status"]
        for item in save_events
    }

    assert response_statuses == {
        "saved",
        "already_exists",
    }


def test_nextfarm_missing_log_creates_failed_history(
    client: TestClient,
) -> None:
    """
    Submit một client_record_id không tồn tại
    phải được ghi vào history.
    """

    client_record_id = (
        "history-nextfarm-not-found-001"
    )

    response = client.post(
        (
            "/api/nextfarm/cultivation-logs/"
            f"{client_record_id}/submit"
        )
    )

    assert response.status_code == 404

    history_response = client.get(
        "/api/history",
        params={
            "client_record_id": client_record_id,
        },
    )

    assert history_response.status_code == 200

    nextfarm_events = [
        item
        for item
        in history_response.json()["data"]
        if item["event_type"]
        == "submit_nextfarm"
    ]

    assert len(nextfarm_events) == 1

    history = nextfarm_events[0]

    assert history["status"] == "failed"
    assert history["http_status"] == 404

    assert (
        history["response_payload"][
            "detail"
        ]["code"]
        == "CULTIVATION_LOG_NOT_FOUND"
    )


def test_history_can_filter_by_client_record_id(
    client: TestClient,
) -> None:
    """
    API history phải lọc đúng theo client_record_id.
    """

    first_id = "history-filter-001"
    second_id = "history-filter-002"

    first_response = client.post(
        "/api/cultivation-logs",
        json=build_history_test_log(
            first_id
        ),
    )

    second_response = client.post(
        "/api/cultivation-logs",
        json=build_history_test_log(
            second_id
        ),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get(
        "/api/history",
        params={
            "client_record_id": first_id,
        },
    )

    assert response.status_code == 200

    records = response.json()["data"]

    assert len(records) >= 1

    assert all(
        record["client_record_id"]
        == first_id
        for record in records
    )
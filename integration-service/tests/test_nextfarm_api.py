from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def build_cultivation_log(
    client_record_id: str,
) -> dict[str, Any]:
    """
    Tạo nhật ký hợp lệ để kiểm tra API NextFarm.
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
        "performed_at": "2026-08-03T08:00:00+07:00",
        "performer_code": "NV001",
        "notes": "Kiểm tra tích hợp NextFarm",
        "source": "voice",
        "confirmed": True,
    }


def test_nextfarm_router_health(
    client: TestClient,
) -> None:
    """
    Router NextFarm phải được đăng ký trong FastAPI.
    """

    response = client.get(
        "/api/nextfarm/test"
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["status"] == "ok"
    assert (
        response_data["message"]
        == "NextFarm integration router is working"
    )


def test_submit_saved_log_to_nextfarm_mock(
    client: TestClient,
) -> None:
    """
    Nhật ký đã lưu phải gửi được sang NextFarm mock.
    """

    client_record_id = "nextfarm-api-test-001"

    save_response = client.post(
        "/api/cultivation-logs",
        json=build_cultivation_log(
            client_record_id
        ),
    )

    assert save_response.status_code == 201

    save_data = save_response.json()

    assert save_data["success"] is True
    assert save_data["status"] == "saved"

    submit_response = client.post(
        (
            "/api/nextfarm/cultivation-logs/"
            f"{client_record_id}/submit"
        )
    )

    assert submit_response.status_code == 200

    response_data = submit_response.json()

    assert response_data["success"] is True
    assert response_data["client_record_id"] == (
        client_record_id
    )
    assert response_data["mode"] == "mock"
    assert response_data["status"] == "accepted"
    assert response_data["status_code"] == 200

    mapped_payload = response_data[
        "mapped_payload"
    ]

    assert mapped_payload["name"] == "Bón phân"
    assert mapped_payload["location"] == "LO_A1"
    assert mapped_payload["assigned_to"] == "NV001"
    assert mapped_payload["category_task_id"] == (
        "BON_PHAN"
    )
    assert mapped_payload["season_id"] == "LO_A1"

    assert (
        mapped_payload["metadata"][
            "client_record_id"
        ]
        == client_record_id
    )

    nextfarm_response = response_data[
        "nextfarm_response"
    ]

    assert nextfarm_response["success"] is True
    assert nextfarm_response["mode"] == "mock"

    assert nextfarm_response["data"]["id"] == (
        f"mock-{client_record_id}"
    )


def test_submit_missing_log_returns_404(
    client: TestClient,
) -> None:
    """
    Nhật ký không tồn tại phải trả về HTTP 404.
    """

    response = client.post(
        (
            "/api/nextfarm/cultivation-logs/"
            "not-found-record/submit"
        )
    )

    assert response.status_code == 404

    response_data = response.json()

    assert response_data["detail"]["code"] == (
        "CULTIVATION_LOG_NOT_FOUND"
    )


def test_submit_unconfirmed_log_is_not_available(
    client: TestClient,
) -> None:
    """
    Nhật ký chưa xác nhận không được lưu, nên không thể gửi
    sang NextFarm.
    """

    client_record_id = (
        "nextfarm-api-unconfirmed-001"
    )

    payload = build_cultivation_log(
        client_record_id
    )

    payload["confirmed"] = False

    save_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert save_response.status_code == 400

    submit_response = client.post(
        (
            "/api/nextfarm/cultivation-logs/"
            f"{client_record_id}/submit"
        )
    )

    assert submit_response.status_code == 404

    response_data = submit_response.json()

    assert response_data["detail"]["code"] == (
        "CULTIVATION_LOG_NOT_FOUND"
    )
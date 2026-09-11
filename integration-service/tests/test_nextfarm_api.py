from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from unittest.mock import patch

from app.models.cultivation_log import CultivationLogModel
from tests.conftest import TestingSessionLocal

def build_cultivation_log(
    client_record_id: str,
) -> dict[str, Any]:
    """
    Tạo nhật ký hợp lệ để kiểm tra API NextFarm.
    """

    return {
        "schema_version": "1.0",
        "client_record_id": client_record_id,
        "context": {
            "tenant_id": "tenant-001",
            "user_id": "user-001",
            "season_id": "season-2026",
            "plot_id": "plot-001",
            "task_id": "task-001",
        },
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
    assert mapped_payload["location"] == "plot-001"
    assert mapped_payload["assigned_to"] == "user-001"
    assert mapped_payload["category_task_id"] == "task-001"
    assert mapped_payload["season_id"] == "season-2026"

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

def test_submit_live_requires_complete_nextfarm_context(
    client: TestClient,
) -> None:
    """
    Live submit phải bị chặn nếu thiếu bất kỳ canonical context ID nào.
    """

    client_record_id = "nextfarm-live-context-missing-001"

    payload = build_cultivation_log(client_record_id)

    # Tạo record hợp lệ qua API trước.
    save_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert save_response.status_code == 201

    # Sau khi lưu, mô phỏng dữ liệu legacy/incomplete trong DB:
    # task_id bị thiếu nhưng các field khác vẫn hợp lệ.
    with TestingSessionLocal() as database_session:
        stored_log = (
            database_session.query(CultivationLogModel)
            .filter(
                CultivationLogModel.client_record_id
                == client_record_id
            )
            .one()
        )

        stored_log.task_id = None
        database_session.commit()

    with patch(
        "app.services.nextfarm_service.NextFarmClient"
    ) as nextfarm_client_class:
        nextfarm_client_class.return_value.config.mode = "live"

        response = client.post(
            "/api/nextfarm/cultivation-logs/"
            f"{client_record_id}/submit"
        )

    assert response.status_code == 400

    response_data = response.json()

    assert response_data["detail"]["code"] == (
        "NEXTFARM_SUBMIT_FAILED"
    )

    assert "Thiếu NextFarm context đầy đủ" in (
        response_data["detail"]["message"]
    )

def test_submit_live_does_not_fallback_from_lot_code_to_context(
    client: TestClient,
) -> None:
    """
    Live submit không được lấy lot_code để thay thế
    cho plot_id hoặc season_id.
    """

    client_record_id = "nextfarm-live-no-fallback-001"

    payload = build_cultivation_log(client_record_id)

    # lot_code vẫn tồn tại.
    assert payload["lot_code"] == "LO_A"

    # Tạo record hợp lệ qua API trước.
    save_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert save_response.status_code == 201

    # Mô phỏng dữ liệu legacy/incomplete trong DB:
    # plot_id bị thiếu nhưng lot_code vẫn còn LO_A.
    with TestingSessionLocal() as database_session:
        stored_log = (
            database_session.query(CultivationLogModel)
            .filter(
                CultivationLogModel.client_record_id
                == client_record_id
            )
            .one()
        )

        stored_log.plot_id = None
        database_session.commit()

    with patch(
        "app.services.nextfarm_service.NextFarmClient"
    ) as nextfarm_client_class:
        nextfarm_client_class.return_value.config.mode = "live"

        response = client.post(
            "/api/nextfarm/cultivation-logs/"
            f"{client_record_id}/submit"
        )

    assert response.status_code == 400

    response_data = response.json()

    assert response_data["detail"]["code"] == (
        "NEXTFARM_SUBMIT_FAILED"
    )
    assert "Thiếu NextFarm context đầy đủ" in (
        response_data["detail"]["message"]
    )
def test_submit_live_accepts_complete_nextfarm_context(
    client: TestClient,
) -> None:
    """
    Đủ 5 canonical context ID thì live submit được phép
    đi qua Context Guard.
    """

    client_record_id = "nextfarm-live-context-valid-001"

    payload = build_cultivation_log(client_record_id)

    save_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert save_response.status_code == 201

    with patch(
        "app.services.nextfarm_service.NextFarmClient"
    ) as nextfarm_client_class:
        mock_client = nextfarm_client_class.return_value

        mock_client.config.mode = "live"

        mock_client.submit_production_diary.return_value = {
            "success": True,
            "mode": "live",
            "status": "accepted",
            "status_code": 200,
        }

        response = client.post(
            "/api/nextfarm/cultivation-logs/"
            f"{client_record_id}/submit"
        )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["success"] is True
    assert response_data["mode"] == "live"

    mapped_payload = response_data["mapped_payload"]

    assert mapped_payload["location"] == "plot-001"
    assert mapped_payload["assigned_to"] == "user-001"
    assert mapped_payload["category_task_id"] == "task-001"
    assert mapped_payload["season_id"] == "season-2026"
from copy import deepcopy
import json

import pytest
from fastapi.testclient import TestClient


SEASON_ENV = "NEXTFARM_SEASONS_JSON"


@pytest.fixture(autouse=True)
def configure_task_seasons(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        SEASON_ENV,
        json.dumps(
            [
                {
                    "season_id":
                        "season-dau-2026",
                    "name":
                        "Vụ Dâu 2026",
                    "aliases": [
                        "Mùa dâu 2026",
                        "Vụ dâu",
                    ],
                },
                {
                    "season_id":
                        "season-cam-2026",
                    "name":
                        "Vụ Cam 2026",
                    "aliases": [
                        "Mùa cam 2026",
                    ],
                },
            ],
            ensure_ascii=False,
        ),
    )


def build_valid_task(
    client_record_id: str = "task-001",
) -> dict[str, object]:
    return {
        "client_record_id":
            client_record_id,
        "season_text":
            "Vụ Dâu 2026",
        "task_name":
            "Phun thuốc khu 2",
        "task_type_text":
            "Phun",
        "due_time_text":
            "10/09/2026",
        "assignee_text":
            "Nguyễn Văn A",
        "photo_required":
            True,
        "note":
            "Ưu tiên thực hiện buổi sáng.",
        "confirmed":
            True,
    }


def test_tasks_router(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/tasks/test"
    )

    assert response.status_code == 200


def test_create_task(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/tasks",
        json=build_valid_task(),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["status"] == "saved"

    task = body["data"]

    assert (
        task["season_id"]
        == "season-dau-2026"
    )
    assert (
        task["task_name"]
        == "Phun thuốc khu 2"
    )
    assert (
        task["task_type_text"]
        == "Phun"
    )
    assert (
        task["due_time_text"]
        == "10/09/2026"
    )
    assert (
        task["assignee_text"]
        == "Nguyễn Văn A"
    )
    assert (
        task["photo_required"]
        is True
    )


def test_create_task_resolves_season_alias(
    client: TestClient,
) -> None:
    payload = build_valid_task(
        "task-alias-001"
    )

    payload["season_text"] = (
        "Mùa dâu 2026"
    )

    response = client.post(
        "/api/tasks",
        json=payload,
    )

    assert response.status_code == 201

    assert (
        response.json()["data"]["season_id"]
        == "season-dau-2026"
    )


def test_create_task_accepts_confirmed_fuzzy_season(
    client: TestClient,
) -> None:
    payload = build_valid_task(
        "task-fuzzy-001"
    )

    payload["season_text"] = (
        "Vụ Dâu 202"
    )

    response = client.post(
        "/api/tasks",
        json=payload,
    )

    assert response.status_code == 201

    assert (
        response.json()["data"]["season_id"]
        == "season-dau-2026"
    )


def test_create_task_rejects_unconfirmed(
    client: TestClient,
) -> None:
    payload = build_valid_task(
        "task-unconfirmed-001"
    )

    payload["confirmed"] = False

    response = client.post(
        "/api/tasks",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "UNCONFIRMED_RECORD"
    )


def test_create_task_rejects_unknown_season(
    client: TestClient,
) -> None:
    payload = build_valid_task(
        "task-unknown-season-001"
    )

    payload["season_text"] = (
        "Vụ hoàn toàn không tồn tại xyz"
    )

    response = client.post(
        "/api/tasks",
        json=payload,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert (
        detail["code"]
        == "TASK_VALIDATION_FAILED"
    )
    assert detail["field"] == "season_text"
    assert (
        detail["reason_code"]
        == "UNKNOWN_SEASON"
    )


def test_create_task_returns_503_without_season_source(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        SEASON_ENV,
        raising=False,
    )

    response = client.post(
        "/api/tasks",
        json=build_valid_task(
            "task-no-season-source-001"
        ),
    )

    assert response.status_code == 503

    assert (
        response.json()["detail"]["code"]
        == "SEASON_MASTER_DATA_UNAVAILABLE"
    )


def test_create_task_is_idempotent(
    client: TestClient,
) -> None:
    payload = build_valid_task(
        "task-idempotent-001"
    )

    first = client.post(
        "/api/tasks",
        json=payload,
    )

    second = client.post(
        "/api/tasks",
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 201

    assert (
        first.json()["status"]
        == "saved"
    )

    assert (
        second.json()["status"]
        == "already_exists"
    )

    records = client.get(
        "/api/tasks"
    ).json()["data"]

    assert len(records) == 1


def test_list_tasks(
    client: TestClient,
) -> None:
    first = build_valid_task(
        "task-list-001"
    )

    second = build_valid_task(
        "task-list-002"
    )

    second["task_name"] = (
        "Kiểm tra tưới"
    )

    assert client.post(
        "/api/tasks",
        json=first,
    ).status_code == 201

    assert client.post(
        "/api/tasks",
        json=second,
    ).status_code == 201

    response = client.get(
        "/api/tasks"
    )

    assert response.status_code == 200
    assert len(
        response.json()["data"]
    ) == 2


def test_get_task(
    client: TestClient,
) -> None:
    payload = build_valid_task(
        "task-detail-001"
    )

    client.post(
        "/api/tasks",
        json=payload,
    )

    response = client.get(
        "/api/tasks/task-detail-001"
    )

    assert response.status_code == 200

    assert (
        response.json()["data"][
            "client_record_id"
        ]
        == "task-detail-001"
    )


def test_get_task_not_found(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/tasks/not-found"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]["code"]
        == "TASK_NOT_FOUND"
    )


def test_update_task(
    client: TestClient,
) -> None:
    payload = build_valid_task(
        "task-update-001"
    )

    assert client.post(
        "/api/tasks",
        json=payload,
    ).status_code == 201

    updated = deepcopy(payload)

    updated["season_text"] = (
        "Vụ Cam 2026"
    )
    updated["task_name"] = (
        "Tưới khu cam"
    )
    updated["due_time_text"] = (
        "11/09/2026"
    )

    response = client.put(
        "/api/tasks/task-update-001",
        json=updated,
    )

    assert response.status_code == 200

    task = response.json()["data"]

    assert (
        task["season_id"]
        == "season-cam-2026"
    )
    assert (
        task["task_name"]
        == "Tưới khu cam"
    )
    assert (
        task["due_time_text"]
        == "11/09/2026"
    )


def test_update_task_not_found(
    client: TestClient,
) -> None:
    payload = build_valid_task(
        "task-update-missing-001"
    )

    response = client.put(
        "/api/tasks/task-update-missing-001",
        json=payload,
    )

    assert response.status_code == 404


def test_update_task_rejects_id_mismatch(
    client: TestClient,
) -> None:
    payload = build_valid_task(
        "task-mismatch-001"
    )

    client.post(
        "/api/tasks",
        json=payload,
    )

    updated = deepcopy(payload)

    updated["client_record_id"] = (
        "another-task-id"
    )

    response = client.put(
        "/api/tasks/task-mismatch-001",
        json=updated,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "CLIENT_RECORD_ID_MISMATCH"
    )


def test_update_task_rejects_unconfirmed(
    client: TestClient,
) -> None:
    payload = build_valid_task(
        "task-update-unconfirmed-001"
    )

    client.post(
        "/api/tasks",
        json=payload,
    )

    updated = deepcopy(payload)
    updated["confirmed"] = False
    updated["task_name"] = (
        "Không được lưu"
    )

    response = client.put(
        "/api/tasks/"
        "task-update-unconfirmed-001",
        json=updated,
    )

    assert response.status_code == 400

    stored = client.get(
        "/api/tasks/"
        "task-update-unconfirmed-001"
    ).json()["data"]

    assert (
        stored["task_name"]
        == "Phun thuốc khu 2"
    )


def test_update_task_rejects_unknown_season(
    client: TestClient,
) -> None:
    payload = build_valid_task(
        "task-update-season-001"
    )

    client.post(
        "/api/tasks",
        json=payload,
    )

    updated = deepcopy(payload)

    updated["season_text"] = (
        "Mùa vụ xyz không tồn tại"
    )

    response = client.put(
        "/api/tasks/task-update-season-001",
        json=updated,
    )

    assert response.status_code == 400

    stored = client.get(
        "/api/tasks/task-update-season-001"
    ).json()["data"]

    assert (
        stored["season_id"]
        == "season-dau-2026"
    )


def test_create_task_requires_task_name(
    client: TestClient,
) -> None:
    payload = build_valid_task(
        "task-no-name-001"
    )

    del payload["task_name"]

    response = client.post(
        "/api/tasks",
        json=payload,
    )

    assert response.status_code == 422
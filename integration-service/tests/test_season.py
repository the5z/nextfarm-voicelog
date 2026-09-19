from copy import deepcopy
import json

import pytest
from fastapi.testclient import TestClient


CROP_ENV = "NEXTFARM_CROPS_JSON"
SEASON_ENV = "NEXTFARM_SEASONS_JSON"


@pytest.fixture(autouse=True)
def configure_season_crops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        CROP_ENV,
        json.dumps(
            [
                {
                    "crop_id":
                        "crop-strawberry",
                    "name":
                        "Dâu tây",
                    "aliases": [
                        "Dâu",
                    ],
                },
                {
                    "crop_id":
                        "crop-orange",
                    "name":
                        "Cam",
                    "aliases": [
                        "Cây cam",
                    ],
                },
            ],
            ensure_ascii=False,
        ),
    )

    monkeypatch.delenv(
        SEASON_ENV,
        raising=False,
    )


def build_valid_season(
    client_record_id: str = (
        "season-create-001"
    ),
) -> dict[str, object]:
    return {
        "client_record_id":
            client_record_id,
        "plot_text":
            "Lô A",
        "crop_text":
            "Dâu tây",
        "planting_date_text":
            "05/10/2026",
        "season_name":
            "Vụ Dâu Thu 2026",
        "expected_harvest_date_text":
            "20/12/2026",
        "plant_count":
            1000,
        "expected_yield":
            500.5,
        "expected_yield_unit_text":
            "kg",
        "process_template_text":
            "Quy trình dâu tiêu chuẩn",
        "confirmed":
            True,
    }


def test_seasons_router(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/seasons/test"
    )

    assert response.status_code == 200


def test_create_season(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/seasons",
        json=build_valid_season(),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["status"] == "saved"

    season = body["data"]

    assert (
        season["season_id"]
        .startswith("local-season-")
    )

    assert season["plot_code"] == "LO_A"

    assert (
        season["crop_id"]
        == "crop-strawberry"
    )

    assert (
        season["planting_date_text"]
        == "05/10/2026"
    )

    assert (
        season["season_name"]
        == "Vụ Dâu Thu 2026"
    )

    assert (
        season[
            "expected_yield_unit_code"
        ]
        == "KG"
    )


def test_create_season_resolves_aliases(
    client: TestClient,
) -> None:
    payload = build_valid_season(
        "season-alias-001"
    )

    payload["plot_text"] = "Khu A"
    payload["crop_text"] = "Dâu"
    payload["expected_yield_unit_text"] = (
        "ký"
    )

    response = client.post(
        "/api/seasons",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()["data"]

    assert data["plot_code"] == "LO_A"

    assert (
        data["crop_id"]
        == "crop-strawberry"
    )

    assert (
        data["expected_yield_unit_code"]
        == "KG"
    )


def test_create_season_rejects_unconfirmed(
    client: TestClient,
) -> None:
    payload = build_valid_season(
        "season-unconfirmed-001"
    )

    payload["confirmed"] = False

    response = client.post(
        "/api/seasons",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "UNCONFIRMED_RECORD"
    )


def test_create_season_rejects_unknown_plot(
    client: TestClient,
) -> None:
    payload = build_valid_season(
        "season-plot-001"
    )

    payload["plot_text"] = (
        "Lô không tồn tại xyz"
    )

    response = client.post(
        "/api/seasons",
        json=payload,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert detail["field"] == "plot_text"

    assert (
        detail["reason_code"]
        == "UNKNOWN_PLOT"
    )


def test_create_season_rejects_unknown_crop(
    client: TestClient,
) -> None:
    payload = build_valid_season(
        "season-crop-001"
    )

    payload["crop_text"] = (
        "Cây không tồn tại xyz"
    )

    response = client.post(
        "/api/seasons",
        json=payload,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert detail["field"] == "crop_text"

    assert (
        detail["reason_code"]
        == "UNKNOWN_CROP"
    )


def test_create_season_requires_crop_source(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        CROP_ENV,
        raising=False,
    )

    response = client.post(
        "/api/seasons",
        json=build_valid_season(
            "season-no-crops-001"
        ),
    )

    assert response.status_code == 503

    assert (
        response.json()["detail"]["code"]
        == "CROP_MASTER_DATA_UNAVAILABLE"
    )


def test_create_season_rejects_unknown_yield_unit(
    client: TestClient,
) -> None:
    payload = build_valid_season(
        "season-unit-001"
    )

    payload[
        "expected_yield_unit_text"
    ] = "xị"

    response = client.post(
        "/api/seasons",
        json=payload,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert (
        detail["field"]
        == "expected_yield_unit_text"
    )

    assert (
        detail["reason_code"]
        == "UNKNOWN_EXPECTED_YIELD_UNIT"
    )


def test_create_season_is_idempotent(
    client: TestClient,
) -> None:
    payload = build_valid_season(
        "season-idempotent-001"
    )

    first = client.post(
        "/api/seasons",
        json=payload,
    )

    second = client.post(
        "/api/seasons",
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
        "/api/seasons"
    ).json()["data"]

    assert len(records) == 1


def test_create_season_rejects_duplicate_name(
    client: TestClient,
) -> None:
    first = build_valid_season(
        "season-name-001"
    )

    second = build_valid_season(
        "season-name-002"
    )

    assert client.post(
        "/api/seasons",
        json=first,
    ).status_code == 201

    response = client.post(
        "/api/seasons",
        json=second,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert detail["field"] == "season_name"

    assert (
        detail["reason_code"]
        == "DUPLICATE_SEASON_NAME"
    )


def test_list_seasons(
    client: TestClient,
) -> None:
    first = build_valid_season(
        "season-list-001"
    )

    second = build_valid_season(
        "season-list-002"
    )

    second["season_name"] = (
        "Vụ Cam Đông 2026"
    )

    second["crop_text"] = "Cam"

    assert client.post(
        "/api/seasons",
        json=first,
    ).status_code == 201

    assert client.post(
        "/api/seasons",
        json=second,
    ).status_code == 201

    response = client.get(
        "/api/seasons"
    )

    assert response.status_code == 200

    assert len(
        response.json()["data"]
    ) == 2


def test_get_season(
    client: TestClient,
) -> None:
    payload = build_valid_season(
        "season-detail-001"
    )

    client.post(
        "/api/seasons",
        json=payload,
    )

    response = client.get(
        "/api/seasons/"
        "season-detail-001"
    )

    assert response.status_code == 200

    assert (
        response.json()["data"][
            "client_record_id"
        ]
        == "season-detail-001"
    )


def test_get_season_not_found(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/seasons/not-found"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]["code"]
        == "SEASON_NOT_FOUND"
    )


def test_update_season(
    client: TestClient,
) -> None:
    payload = build_valid_season(
        "season-update-001"
    )

    assert client.post(
        "/api/seasons",
        json=payload,
    ).status_code == 201

    original = client.get(
        "/api/seasons/season-update-001"
    ).json()["data"]

    updated = deepcopy(payload)

    updated["plot_text"] = "Lô B"
    updated["crop_text"] = "Cam"

    updated["season_name"] = (
        "Vụ Cam Đông 2026"
    )

    response = client.put(
        "/api/seasons/"
        "season-update-001",
        json=updated,
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["plot_code"] == "LO_B"

    assert (
        data["crop_id"]
        == "crop-orange"
    )

    assert (
        data["season_name"]
        == "Vụ Cam Đông 2026"
    )

    assert (
        data["season_id"]
        == original["season_id"]
    )


def test_update_season_rejects_id_mismatch(
    client: TestClient,
) -> None:
    payload = build_valid_season(
        "season-mismatch-001"
    )

    client.post(
        "/api/seasons",
        json=payload,
    )

    updated = deepcopy(payload)

    updated["client_record_id"] = (
        "different-id"
    )

    response = client.put(
        "/api/seasons/"
        "season-mismatch-001",
        json=updated,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "CLIENT_RECORD_ID_MISMATCH"
    )


def test_update_season_rejects_unconfirmed(
    client: TestClient,
) -> None:
    payload = build_valid_season(
        "season-update-unconfirmed-001"
    )

    client.post(
        "/api/seasons",
        json=payload,
    )

    updated = deepcopy(payload)

    updated["confirmed"] = False

    updated["season_name"] = (
        "Tên không được lưu"
    )

    response = client.put(
        "/api/seasons/"
        "season-update-unconfirmed-001",
        json=updated,
    )

    assert response.status_code == 400

    stored = client.get(
        "/api/seasons/"
        "season-update-unconfirmed-001"
    ).json()["data"]

    assert (
        stored["season_name"]
        == "Vụ Dâu Thu 2026"
    )


def test_created_season_is_available_to_resolver(
    client: TestClient,
) -> None:
    payload = build_valid_season(
        "season-resolver-001"
    )

    response = client.post(
        "/api/seasons",
        json=payload,
    )

    assert response.status_code == 201

    created = response.json()["data"]

    response = client.post(
        "/api/master-data/resolve-season",
        json={
            "text": "Vụ Dâu Thu 2026",
        },
    )

    assert response.status_code == 200

    resolved = response.json()

    assert resolved["matched"] is True

    assert (
        resolved["season_id"]
        == created["season_id"]
    )


def test_task_can_use_created_season(
    client: TestClient,
) -> None:
    season_payload = build_valid_season(
        "season-task-source-001"
    )

    season_payload["season_name"] = (
        "Vụ Dâu Cho Công Việc 2026"
    )

    season_response = client.post(
        "/api/seasons",
        json=season_payload,
    )

    assert season_response.status_code == 201

    created_season = (
        season_response.json()["data"]
    )

    task_payload = {
        "client_record_id":
            "task-created-season-001",
        "season_text":
            "Vụ Dâu Cho Công Việc 2026",
        "task_name":
            "Tưới nước",
        "task_type_text":
            "Tưới",
        "due_time_text":
            "21/09/2026",
        "assignee_text":
            None,
        "photo_required":
            False,
        "note":
            None,
        "confirmed":
            True,
    }

    response = client.post(
        "/api/tasks",
        json=task_payload,
    )

    assert response.status_code == 201

    assert (
        response.json()["data"]["season_id"]
        == created_season["season_id"]
    )


def test_create_season_requires_positive_plant_count(
    client: TestClient,
) -> None:
    payload = build_valid_season(
        "season-count-001"
    )

    payload["plant_count"] = 0

    response = client.post(
        "/api/seasons",
        json=payload,
    )

    assert response.status_code == 422


def test_create_season_requires_positive_expected_yield(
    client: TestClient,
) -> None:
    payload = build_valid_season(
        "season-yield-001"
    )

    payload["expected_yield"] = 0

    response = client.post(
        "/api/seasons",
        json=payload,
    )

    assert response.status_code == 422
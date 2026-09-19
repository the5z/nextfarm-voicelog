from copy import deepcopy
import json

import pytest
from fastapi.testclient import TestClient


CROP_ENV = "NEXTFARM_CROPS_JSON"
SEASON_ENV = "NEXTFARM_SEASONS_JSON"


@pytest.fixture(autouse=True)
def isolate_crop_type_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        CROP_ENV,
        raising=False,
    )

    monkeypatch.delenv(
        SEASON_ENV,
        raising=False,
    )


def build_valid_crop_type(
    client_record_id: str = (
        "crop-type-001"
    ),
) -> dict[str, object]:
    return {
        "client_record_id":
            client_record_id,
        "crop_name":
            "Thanh long",
        "crop_group_text":
            "Cây ăn quả",
        "crop_code_suggestion":
            "THANH_LONG",
        "days_to_harvest":
            270,
        "confirmed":
            True,
    }


def test_crop_types_router(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/crop-types/test"
    )

    assert response.status_code == 200


def test_create_crop_type(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/crop-types",
        json=build_valid_crop_type(),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["status"] == "saved"

    crop = body["data"]

    assert (
        crop["crop_id"]
        .startswith("local-crop-")
    )

    assert (
        crop["crop_name"]
        == "Thanh long"
    )

    assert (
        crop["crop_group_text"]
        == "Cây ăn quả"
    )

    assert (
        crop["crop_code_suggestion"]
        == "THANH_LONG"
    )

    assert (
        crop["crop_id"]
        != crop["crop_code_suggestion"]
    )

    assert crop["days_to_harvest"] == 270


def test_create_crop_type_rejects_unconfirmed(
    client: TestClient,
) -> None:
    payload = build_valid_crop_type(
        "crop-unconfirmed-001"
    )

    payload["confirmed"] = False

    response = client.post(
        "/api/crop-types",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "UNCONFIRMED_RECORD"
    )


def test_create_crop_type_is_idempotent(
    client: TestClient,
) -> None:
    payload = build_valid_crop_type(
        "crop-idempotent-001"
    )

    first = client.post(
        "/api/crop-types",
        json=payload,
    )

    second = client.post(
        "/api/crop-types",
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
        "/api/crop-types"
    ).json()["data"]

    assert len(records) == 1


def test_create_crop_type_rejects_duplicate_name(
    client: TestClient,
) -> None:
    first = build_valid_crop_type(
        "crop-name-001"
    )

    second = build_valid_crop_type(
        "crop-name-002"
    )

    assert client.post(
        "/api/crop-types",
        json=first,
    ).status_code == 201

    response = client.post(
        "/api/crop-types",
        json=second,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert detail["field"] == "crop_name"

    assert (
        detail["reason_code"]
        == "DUPLICATE_CROP_NAME"
    )


def test_create_crop_type_rejects_configured_name(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        CROP_ENV,
        json.dumps(
            [
                {
                    "crop_id":
                        "crop-existing",
                    "name":
                        "Thanh long",
                    "aliases": [
                        "Cây thanh long",
                    ],
                },
            ],
            ensure_ascii=False,
        ),
    )

    response = client.post(
        "/api/crop-types",
        json=build_valid_crop_type(
            "crop-config-name-001"
        ),
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"][
            "reason_code"
        ]
        == "DUPLICATE_CROP_NAME"
    )


def test_create_crop_type_returns_503_for_invalid_source(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        CROP_ENV,
        "{invalid-json",
    )

    response = client.post(
        "/api/crop-types",
        json=build_valid_crop_type(
            "crop-invalid-source-001"
        ),
    )

    assert response.status_code == 503

    assert (
        response.json()["detail"]["code"]
        == "CROP_MASTER_DATA_UNAVAILABLE"
    )


def test_list_crop_types(
    client: TestClient,
) -> None:
    first = build_valid_crop_type(
        "crop-list-001"
    )

    second = build_valid_crop_type(
        "crop-list-002"
    )

    second["crop_name"] = "Bơ"
    second["crop_code_suggestion"] = "BO"

    assert client.post(
        "/api/crop-types",
        json=first,
    ).status_code == 201

    assert client.post(
        "/api/crop-types",
        json=second,
    ).status_code == 201

    response = client.get(
        "/api/crop-types"
    )

    assert response.status_code == 200

    assert len(
        response.json()["data"]
    ) == 2


def test_get_crop_type(
    client: TestClient,
) -> None:
    payload = build_valid_crop_type(
        "crop-detail-001"
    )

    client.post(
        "/api/crop-types",
        json=payload,
    )

    response = client.get(
        "/api/crop-types/"
        "crop-detail-001"
    )

    assert response.status_code == 200

    assert (
        response.json()["data"][
            "client_record_id"
        ]
        == "crop-detail-001"
    )


def test_get_crop_type_not_found(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/crop-types/not-found"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]["code"]
        == "CROP_TYPE_NOT_FOUND"
    )


def test_update_crop_type(
    client: TestClient,
) -> None:
    payload = build_valid_crop_type(
        "crop-update-001"
    )

    assert client.post(
        "/api/crop-types",
        json=payload,
    ).status_code == 201

    original = client.get(
        "/api/crop-types/crop-update-001"
    ).json()["data"]

    updated = deepcopy(
        payload
    )

    updated["crop_name"] = (
        "Thanh long ruột đỏ"
    )

    updated["crop_group_text"] = (
        "Cây ăn quả lâu năm"
    )

    updated["crop_code_suggestion"] = (
        "THANH_LONG_DO"
    )

    updated["days_to_harvest"] = 300

    response = client.put(
        "/api/crop-types/"
        "crop-update-001",
        json=updated,
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert (
        data["crop_name"]
        == "Thanh long ruột đỏ"
    )

    assert (
        data["crop_code_suggestion"]
        == "THANH_LONG_DO"
    )

    assert data["days_to_harvest"] == 300

    assert (
        data["crop_id"]
        == original["crop_id"]
    )


def test_update_crop_type_not_found(
    client: TestClient,
) -> None:
    payload = build_valid_crop_type(
        "crop-missing-001"
    )

    response = client.put(
        "/api/crop-types/"
        "crop-missing-001",
        json=payload,
    )

    assert response.status_code == 404


def test_update_crop_type_rejects_id_mismatch(
    client: TestClient,
) -> None:
    payload = build_valid_crop_type(
        "crop-mismatch-001"
    )

    client.post(
        "/api/crop-types",
        json=payload,
    )

    updated = deepcopy(
        payload
    )

    updated["client_record_id"] = (
        "different-id"
    )

    response = client.put(
        "/api/crop-types/"
        "crop-mismatch-001",
        json=updated,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "CLIENT_RECORD_ID_MISMATCH"
    )


def test_update_crop_type_rejects_unconfirmed(
    client: TestClient,
) -> None:
    payload = build_valid_crop_type(
        "crop-update-unconfirmed-001"
    )

    client.post(
        "/api/crop-types",
        json=payload,
    )

    updated = deepcopy(
        payload
    )

    updated["confirmed"] = False
    updated["crop_name"] = (
        "Tên không được lưu"
    )

    response = client.put(
        "/api/crop-types/"
        "crop-update-unconfirmed-001",
        json=updated,
    )

    assert response.status_code == 400

    stored = client.get(
        "/api/crop-types/"
        "crop-update-unconfirmed-001"
    ).json()["data"]

    assert (
        stored["crop_name"]
        == "Thanh long"
    )


def test_create_crop_type_requires_positive_days(
    client: TestClient,
) -> None:
    payload = build_valid_crop_type(
        "crop-days-001"
    )

    payload["days_to_harvest"] = 0

    response = client.post(
        "/api/crop-types",
        json=payload,
    )

    assert response.status_code == 422


def test_created_crop_is_available_to_resolver(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/crop-types",
        json=build_valid_crop_type(
            "crop-resolver-001"
        ),
    )

    assert response.status_code == 201

    created = response.json()["data"]

    response = client.post(
        "/api/master-data/resolve-crop",
        json={
            "text": "Thanh long",
        },
    )

    assert response.status_code == 200

    resolved = response.json()

    assert resolved["matched"] is True

    assert (
        resolved["crop_id"]
        == created["crop_id"]
    )


def test_created_crop_is_listed_as_master_data(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/crop-types",
        json=build_valid_crop_type(
            "crop-master-list-001"
        ),
    )

    assert response.status_code == 201

    created = response.json()["data"]

    response = client.get(
        "/api/master-data/crops"
    )

    assert response.status_code == 200

    items = response.json()

    assert len(items) == 1

    assert (
        items[0]["crop_id"]
        == created["crop_id"]
    )

    assert items[0]["name"] == "Thanh long"


def test_season_can_use_created_crop(
    client: TestClient,
) -> None:
    crop_response = client.post(
        "/api/crop-types",
        json=build_valid_crop_type(
            "crop-for-season-001"
        ),
    )

    assert crop_response.status_code == 201

    crop = crop_response.json()["data"]

    season_payload = {
        "client_record_id":
            "season-new-crop-001",
        "plot_text":
            "Lô A",
        "crop_text":
            "Thanh long",
        "planting_date_text":
            "19/09/2026",
        "season_name":
            "Vụ Thanh Long 2026",
        "expected_harvest_date_text":
            None,
        "plant_count":
            100,
        "expected_yield":
            None,
        "expected_yield_unit_text":
            None,
        "process_template_text":
            None,
        "confirmed":
            True,
    }

    response = client.post(
        "/api/seasons",
        json=season_payload,
    )

    assert response.status_code == 201

    assert (
        response.json()["data"]["crop_id"]
        == crop["crop_id"]
    )


def test_harvest_can_use_created_crop(
    client: TestClient,
) -> None:
    crop_response = client.post(
        "/api/crop-types",
        json=build_valid_crop_type(
            "crop-for-harvest-001"
        ),
    )

    assert crop_response.status_code == 201

    crop = crop_response.json()["data"]

    harvest_payload = {
        "client_record_id":
            "harvest-new-crop-001",
        "plot_text":
            "Lô A",
        "crop_text":
            "Thanh long",
        "quantity":
            50,
        "unit_text":
            "kg",
        "harvest_date_text":
            "19/09/2026",
        "photo":
            None,
        "note":
            None,
        "confirmed":
            True,
    }

    response = client.post(
        "/api/harvests",
        json=harvest_payload,
    )

    assert response.status_code == 201

    assert (
        response.json()["data"]["crop_id"]
        == crop["crop_id"]
    )
from copy import deepcopy
import json

import pytest
from fastapi.testclient import TestClient


CROP_ENV = "NEXTFARM_CROPS_JSON"


@pytest.fixture(autouse=True)
def configure_harvest_crops(
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
                        "Cây dâu tây",
                    ],
                },
                {
                    "crop_id":
                        "crop-orange",
                    "name":
                        "Cam",
                    "aliases": [
                        "Cây cam",
                        "Cam ngọt",
                    ],
                },
            ],
            ensure_ascii=False,
        ),
    )


def build_valid_harvest(
    client_record_id: str = (
        "harvest-001"
    ),
) -> dict[str, object]:
    return {
        "client_record_id":
            client_record_id,
        "plot_text":
            "Lô A",
        "crop_text":
            "Dâu tây",
        "quantity":
            12.5,
        "unit_text":
            "kg",
        "harvest_date_text":
            "19/09/2026",
        "photo":
            "harvest-photo-001.jpg",
        "note":
            "Thu hoạch buổi sáng.",
        "confirmed":
            True,
    }


def test_harvests_router(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/harvests/test"
    )

    assert response.status_code == 200


def test_create_harvest(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/harvests",
        json=build_valid_harvest(),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["status"] == "saved"

    harvest = body["data"]

    assert harvest["plot_code"] == "LO_A"
    assert (
        harvest["crop_id"]
        == "crop-strawberry"
    )
    assert harvest["quantity"] == 12.5
    assert harvest["unit_code"] == "KG"

    assert (
        harvest["harvest_date_text"]
        == "19/09/2026"
    )

    assert (
        harvest["photo"]
        == "harvest-photo-001.jpg"
    )


def test_create_harvest_resolves_aliases(
    client: TestClient,
) -> None:
    payload = build_valid_harvest(
        "harvest-alias-001"
    )

    payload["plot_text"] = "Khu A"
    payload["crop_text"] = (
        "Cây dâu tây"
    )
    payload["unit_text"] = "ký"

    response = client.post(
        "/api/harvests",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()["data"]

    assert data["plot_code"] == "LO_A"

    assert (
        data["crop_id"]
        == "crop-strawberry"
    )

    assert data["unit_code"] == "KG"


def test_create_harvest_accepts_confirmed_fuzzy_crop(
    client: TestClient,
) -> None:
    payload = build_valid_harvest(
        "harvest-fuzzy-001"
    )

    payload["crop_text"] = "Dâu tâ"

    response = client.post(
        "/api/harvests",
        json=payload,
    )

    assert response.status_code == 201

    assert (
        response.json()["data"]["crop_id"]
        == "crop-strawberry"
    )


def test_create_harvest_rejects_unconfirmed(
    client: TestClient,
) -> None:
    payload = build_valid_harvest(
        "harvest-unconfirmed-001"
    )

    payload["confirmed"] = False

    response = client.post(
        "/api/harvests",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "UNCONFIRMED_RECORD"
    )


def test_create_harvest_rejects_unknown_plot(
    client: TestClient,
) -> None:
    payload = build_valid_harvest(
        "harvest-unknown-plot-001"
    )

    payload["plot_text"] = (
        "Lô hoàn toàn không tồn tại xyz"
    )

    response = client.post(
        "/api/harvests",
        json=payload,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert (
        detail["code"]
        == "HARVEST_VALIDATION_FAILED"
    )

    assert detail["field"] == "plot_text"

    assert (
        detail["reason_code"]
        == "UNKNOWN_PLOT"
    )


def test_create_harvest_rejects_unknown_crop(
    client: TestClient,
) -> None:
    payload = build_valid_harvest(
        "harvest-unknown-crop-001"
    )

    payload["crop_text"] = (
        "Cây không tồn tại xyz"
    )

    response = client.post(
        "/api/harvests",
        json=payload,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert detail["field"] == "crop_text"

    assert (
        detail["reason_code"]
        == "UNKNOWN_CROP"
    )


def test_create_harvest_returns_503_without_crop_source(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        CROP_ENV,
        raising=False,
    )

    response = client.post(
        "/api/harvests",
        json=build_valid_harvest(
            "harvest-no-crop-source-001"
        ),
    )

    assert response.status_code == 503

    assert (
        response.json()["detail"]["code"]
        == "CROP_MASTER_DATA_UNAVAILABLE"
    )


def test_create_harvest_rejects_unknown_unit(
    client: TestClient,
) -> None:
    payload = build_valid_harvest(
        "harvest-unit-001"
    )

    payload["unit_text"] = "xị"

    response = client.post(
        "/api/harvests",
        json=payload,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert detail["field"] == "unit_text"

    assert (
        detail["reason_code"]
        == "UNKNOWN_UNIT"
    )


def test_create_harvest_is_idempotent(
    client: TestClient,
) -> None:
    payload = build_valid_harvest(
        "harvest-idempotent-001"
    )

    first = client.post(
        "/api/harvests",
        json=payload,
    )

    second = client.post(
        "/api/harvests",
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
        "/api/harvests"
    ).json()["data"]

    assert len(records) == 1


def test_list_harvests(
    client: TestClient,
) -> None:
    first = build_valid_harvest(
        "harvest-list-001"
    )

    second = build_valid_harvest(
        "harvest-list-002"
    )

    second["quantity"] = 20

    assert client.post(
        "/api/harvests",
        json=first,
    ).status_code == 201

    assert client.post(
        "/api/harvests",
        json=second,
    ).status_code == 201

    response = client.get(
        "/api/harvests"
    )

    assert response.status_code == 200

    assert len(
        response.json()["data"]
    ) == 2


def test_get_harvest(
    client: TestClient,
) -> None:
    payload = build_valid_harvest(
        "harvest-detail-001"
    )

    client.post(
        "/api/harvests",
        json=payload,
    )

    response = client.get(
        "/api/harvests/"
        "harvest-detail-001"
    )

    assert response.status_code == 200

    assert (
        response.json()["data"][
            "client_record_id"
        ]
        == "harvest-detail-001"
    )


def test_get_harvest_not_found(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/harvests/not-found"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]["code"]
        == "HARVEST_NOT_FOUND"
    )


def test_update_harvest(
    client: TestClient,
) -> None:
    payload = build_valid_harvest(
        "harvest-update-001"
    )

    assert client.post(
        "/api/harvests",
        json=payload,
    ).status_code == 201

    updated = deepcopy(
        payload
    )

    updated["plot_text"] = "Lô B"
    updated["crop_text"] = "Cam"
    updated["quantity"] = 25
    updated["unit_text"] = "lít"

    updated["harvest_date_text"] = (
        "20/09/2026"
    )

    response = client.put(
        "/api/harvests/"
        "harvest-update-001",
        json=updated,
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["plot_code"] == "LO_B"

    assert (
        data["crop_id"]
        == "crop-orange"
    )

    assert data["quantity"] == 25.0
    assert data["unit_code"] == "L"

    assert (
        data["harvest_date_text"]
        == "20/09/2026"
    )


def test_update_harvest_not_found(
    client: TestClient,
) -> None:
    payload = build_valid_harvest(
        "harvest-missing-001"
    )

    response = client.put(
        "/api/harvests/"
        "harvest-missing-001",
        json=payload,
    )

    assert response.status_code == 404


def test_update_harvest_rejects_id_mismatch(
    client: TestClient,
) -> None:
    payload = build_valid_harvest(
        "harvest-mismatch-001"
    )

    client.post(
        "/api/harvests",
        json=payload,
    )

    updated = deepcopy(
        payload
    )

    updated["client_record_id"] = (
        "another-harvest-id"
    )

    response = client.put(
        "/api/harvests/"
        "harvest-mismatch-001",
        json=updated,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "CLIENT_RECORD_ID_MISMATCH"
    )


def test_update_harvest_rejects_unconfirmed(
    client: TestClient,
) -> None:
    payload = build_valid_harvest(
        "harvest-update-unconfirmed-001"
    )

    client.post(
        "/api/harvests",
        json=payload,
    )

    updated = deepcopy(
        payload
    )

    updated["confirmed"] = False
    updated["quantity"] = 999

    response = client.put(
        "/api/harvests/"
        "harvest-update-unconfirmed-001",
        json=updated,
    )

    assert response.status_code == 400

    stored = client.get(
        "/api/harvests/"
        "harvest-update-unconfirmed-001"
    ).json()["data"]

    assert stored["quantity"] == 12.5


def test_create_harvest_requires_positive_quantity(
    client: TestClient,
) -> None:
    payload = build_valid_harvest(
        "harvest-invalid-quantity-001"
    )

    payload["quantity"] = 0

    response = client.post(
        "/api/harvests",
        json=payload,
    )

    assert response.status_code == 422
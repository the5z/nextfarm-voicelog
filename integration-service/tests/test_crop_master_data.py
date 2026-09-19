import json

import pytest
from fastapi.testclient import TestClient


CROP_ENV = "NEXTFARM_CROPS_JSON"


def configure_crops(
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


def test_get_crops_requires_configuration(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        CROP_ENV,
        raising=False,
    )

    response = client.get(
        "/api/master-data/crops"
    )

    assert response.status_code == 503

    assert (
        response.json()["detail"]["code"]
        == "CROP_MASTER_DATA_UNAVAILABLE"
    )


def test_get_crops_returns_configured_data(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_crops(
        monkeypatch
    )

    response = client.get(
        "/api/master-data/crops"
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 2
    assert (
        body[0]["crop_id"]
        == "crop-strawberry"
    )
    assert body[0]["name"] == "Dâu tây"


def test_resolve_crop_exact_name(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_crops(
        monkeypatch
    )

    response = client.post(
        "/api/master-data/resolve-crop",
        json={
            "text": "Dâu tây",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True
    assert (
        body["crop_id"]
        == "crop-strawberry"
    )
    assert body["match_type"] == "exact"
    assert body["confidence"] == 1.0
    assert (
        body["requires_confirmation"]
        is False
    )


def test_resolve_crop_alias(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_crops(
        monkeypatch
    )

    response = client.post(
        "/api/master-data/resolve-crop",
        json={
            "text": "Cây dâu tây",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True
    assert (
        body["crop_id"]
        == "crop-strawberry"
    )
    assert body["match_type"] == "alias"
    assert (
        body["matched_text"]
        == "Cây dâu tây"
    )


def test_resolve_crop_fuzzy_requires_confirmation(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_crops(
        monkeypatch
    )

    response = client.post(
        "/api/master-data/resolve-crop",
        json={
            "text": "Dâu tâ",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True
    assert (
        body["crop_id"]
        == "crop-strawberry"
    )
    assert body["match_type"] == "fuzzy"
    assert body["confidence"] < 1.0
    assert (
        body["requires_confirmation"]
        is True
    )


def test_resolve_unknown_crop_does_not_invent_id(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_crops(
        monkeypatch
    )

    response = client.post(
        "/api/master-data/resolve-crop",
        json={
            "text": (
                "Cây hoàn toàn "
                "không tồn tại xyz"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is False
    assert body["crop_id"] is None
    assert body["match_type"] == "none"
    assert (
        body["requires_confirmation"]
        is True
    )


def test_invalid_crop_json_returns_503(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        CROP_ENV,
        "{invalid-json",
    )

    response = client.get(
        "/api/master-data/crops"
    )

    assert response.status_code == 503

    assert (
        response.json()["detail"]["code"]
        == "CROP_MASTER_DATA_UNAVAILABLE"
    )


def test_duplicate_crop_id_returns_503(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        CROP_ENV,
        json.dumps(
            [
                {
                    "crop_id": "crop-001",
                    "name": "Cây A",
                },
                {
                    "crop_id": "crop-001",
                    "name": "Cây B",
                },
            ],
            ensure_ascii=False,
        ),
    )

    response = client.get(
        "/api/master-data/crops"
    )

    assert response.status_code == 503


def test_duplicate_crop_alias_returns_503(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        CROP_ENV,
        json.dumps(
            [
                {
                    "crop_id": "crop-001",
                    "name": "Dâu tây",
                    "aliases": [
                        "Dâu",
                    ],
                },
                {
                    "crop_id": "crop-002",
                    "name": "Dâu rừng",
                    "aliases": [
                        "Dâu",
                    ],
                },
            ],
            ensure_ascii=False,
        ),
    )

    response = client.get(
        "/api/master-data/crops"
    )

    assert response.status_code == 503


def test_resolve_crop_rejects_empty_text(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_crops(
        monkeypatch
    )

    response = client.post(
        "/api/master-data/resolve-crop",
        json={
            "text": "",
        },
    )

    assert response.status_code == 422
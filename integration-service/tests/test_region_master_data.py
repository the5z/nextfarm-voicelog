import json

import pytest
from fastapi.testclient import TestClient


REGION_ENV = "NEXTFARM_REGIONS_JSON"


@pytest.fixture(autouse=True)
def configure_regions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        REGION_ENV,
        json.dumps(
            [
                {
                    "region_id":
                        "region-north",
                    "name":
                        "Miền Bắc",
                    "aliases": [
                        "Bắc Bộ",
                        "Khu vực phía Bắc",
                    ],
                },
                {
                    "region_id":
                        "region-central",
                    "name":
                        "Miền Trung",
                    "aliases": [
                        "Trung Bộ",
                    ],
                },
            ],
            ensure_ascii=False,
        ),
    )


def test_get_regions(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/master-data/regions"
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 2

    assert (
        body[0]["region_id"]
        == "region-north"
    )


def test_resolve_region_exact(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/master-data/resolve-region",
        json={
            "text": "Miền Bắc",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True

    assert (
        body["region_id"]
        == "region-north"
    )

    assert body["match_type"] == "exact"

    assert (
        body["requires_confirmation"]
        is False
    )


def test_resolve_region_alias(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/master-data/resolve-region",
        json={
            "text": "Bắc Bộ",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True

    assert (
        body["region_id"]
        == "region-north"
    )

    assert body["match_type"] == "alias"


def test_resolve_region_without_accents(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/master-data/resolve-region",
        json={
            "text": "mien bac",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True

    assert (
        body["region_id"]
        == "region-north"
    )

    assert body["match_type"] == "exact"


def test_resolve_region_fuzzy(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/master-data/resolve-region",
        json={
            "text": "Miền Bắcc",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True

    assert (
        body["region_id"]
        == "region-north"
    )

    assert body["match_type"] == "fuzzy"

    assert (
        body["requires_confirmation"]
        is True
    )


def test_resolve_region_unknown(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/master-data/resolve-region",
        json={
            "text": (
                "Khu vực hoàn toàn "
                "không tồn tại xyz"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is False
    assert body["region_id"] is None
    assert body["match_type"] == "none"

    assert (
        body["requires_confirmation"]
        is True
    )


def test_regions_require_source(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        REGION_ENV,
        raising=False,
    )

    response = client.get(
        "/api/master-data/regions"
    )

    assert response.status_code == 503

    assert (
        response.json()["detail"]["code"]
        == "REGION_MASTER_DATA_UNAVAILABLE"
    )


def test_regions_reject_invalid_json(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        REGION_ENV,
        "{invalid-json",
    )

    response = client.get(
        "/api/master-data/regions"
    )

    assert response.status_code == 503


def test_regions_reject_duplicate_id(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        REGION_ENV,
        json.dumps(
            [
                {
                    "region_id": "same-id",
                    "name": "Khu A",
                    "aliases": [],
                },
                {
                    "region_id": "same-id",
                    "name": "Khu B",
                    "aliases": [],
                },
            ],
            ensure_ascii=False,
        ),
    )

    response = client.get(
        "/api/master-data/regions"
    )

    assert response.status_code == 503


def test_regions_reject_term_collision(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        REGION_ENV,
        json.dumps(
            [
                {
                    "region_id":
                        "region-a",
                    "name":
                        "Khu A",
                    "aliases": [
                        "Miền Bắc",
                    ],
                },
                {
                    "region_id":
                        "region-b",
                    "name":
                        "Miền Bắc",
                    "aliases": [],
                },
            ],
            ensure_ascii=False,
        ),
    )

    response = client.get(
        "/api/master-data/regions"
    )

    assert response.status_code == 503
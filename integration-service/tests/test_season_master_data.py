import json

import pytest
from fastapi.testclient import TestClient


SEASON_ENV = "NEXTFARM_SEASONS_JSON"


def configure_seasons(
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


def test_get_seasons_requires_configuration(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        SEASON_ENV,
        raising=False,
    )

    response = client.get(
        "/api/master-data/seasons"
    )

    assert response.status_code == 503

    assert (
        response.json()["detail"]["code"]
        == "SEASON_MASTER_DATA_UNAVAILABLE"
    )


def test_get_seasons_returns_configured_data(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_seasons(
        monkeypatch
    )

    response = client.get(
        "/api/master-data/seasons"
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 2
    assert (
        body[0]["season_id"]
        == "season-dau-2026"
    )
    assert (
        body[0]["name"]
        == "Vụ Dâu 2026"
    )


def test_resolve_season_exact_name(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_seasons(
        monkeypatch
    )

    response = client.post(
        "/api/master-data/resolve-season",
        json={
            "text": "Vụ Dâu 2026",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True
    assert (
        body["season_id"]
        == "season-dau-2026"
    )
    assert body["match_type"] == "exact"
    assert body["confidence"] == 1.0
    assert (
        body["requires_confirmation"]
        is False
    )


def test_resolve_season_alias(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_seasons(
        monkeypatch
    )

    response = client.post(
        "/api/master-data/resolve-season",
        json={
            "text": "Mùa dâu 2026",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True
    assert (
        body["season_id"]
        == "season-dau-2026"
    )
    assert body["match_type"] == "alias"
    assert (
        body["matched_text"]
        == "Mùa dâu 2026"
    )


def test_resolve_season_fuzzy_requires_confirmation(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_seasons(
        monkeypatch
    )

    response = client.post(
        "/api/master-data/resolve-season",
        json={
            "text": "Vụ Dâu 202",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True
    assert (
        body["season_id"]
        == "season-dau-2026"
    )
    assert body["match_type"] == "fuzzy"
    assert body["confidence"] < 1.0
    assert (
        body["requires_confirmation"]
        is True
    )


def test_resolve_unknown_season_does_not_invent_id(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_seasons(
        monkeypatch
    )

    response = client.post(
        "/api/master-data/resolve-season",
        json={
            "text": (
                "Mùa vụ hoàn toàn "
                "không tồn tại xyz"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is False
    assert body["season_id"] is None
    assert body["match_type"] == "none"
    assert (
        body["requires_confirmation"]
        is True
    )


def test_invalid_season_json_returns_503(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        SEASON_ENV,
        "{invalid-json",
    )

    response = client.get(
        "/api/master-data/seasons"
    )

    assert response.status_code == 503

    assert (
        response.json()["detail"]["code"]
        == "SEASON_MASTER_DATA_UNAVAILABLE"
    )


def test_duplicate_season_id_returns_503(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        SEASON_ENV,
        json.dumps(
            [
                {
                    "season_id": "season-001",
                    "name": "Vụ A",
                },
                {
                    "season_id": "season-001",
                    "name": "Vụ B",
                },
            ],
            ensure_ascii=False,
        ),
    )

    response = client.get(
        "/api/master-data/seasons"
    )

    assert response.status_code == 503


def test_resolve_season_rejects_empty_text(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_seasons(
        monkeypatch
    )

    response = client.post(
        "/api/master-data/resolve-season",
        json={
            "text": "",
        },
    )

    assert response.status_code == 422
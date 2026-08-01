from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_resolve_regional_activity_alias() -> None:
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "activity",
            "text": "rải phân",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is True
    assert body["code"] == "BON_PHAN"
    assert body["requires_confirmation"] is False


def test_resolve_southern_spray_alias() -> None:
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "activity",
            "text": "xịt thuốc",
        },
    )

    assert response.status_code == 200
    assert response.json()["code"] == "PHUN_THUOC"


def test_resolve_unit_without_accents() -> None:
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "unit",
            "text": "ky",
        },
    )

    assert response.status_code == 200
    assert response.json()["code"] == "KG"


def test_require_confirmation_for_ambiguous_unit() -> None:
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "unit",
            "text": "xị",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is False
    assert body["code"] is None
    assert body["confidence"] == 0.0
    assert body["requires_confirmation"] is True
    assert "khác nhau theo khu vực" in body["message"]


def test_unknown_value_requires_confirmation() -> None:
    response = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "activity",
            "text": "làm cái này cái kia",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["matched"] is False
    assert body["requires_confirmation"] is True
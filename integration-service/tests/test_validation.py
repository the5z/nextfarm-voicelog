from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def build_payload() -> dict:
    return {
        "schema_version": "1.0",
        "client_record_id": "rule-test-001",
        "transcript": (
            "Bón 20 kg NPK cho lô A "
            "lúc 7 giờ"
        ),
        "lot_code": "LO_A",
        "activity_code": "BON_PHAN",
        "materials": [
            {
                "material_code": "NPK",
                "quantity": 20,
                "unit_code": "KG",
            }
        ],
        "performed_at": (
            "2026-09-03T07:00:00+07:00"
        ),
        "performer_code": "NV001",
        "source": "voice",
        "confirmed": True,
    }


def test_validate_valid_cultivation_log() -> None:
    response = client.post(
        "/api/cultivation-logs/validate",
        json=build_payload(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["valid"] is True
    assert body["errors"] == []

    assert (
        body["requires_confirmation"]
        is False
    )

    assert (
        body["rule_version"]
        == "2026.09-review-v1"
    )


def test_bon_phan_without_material_is_business_error() -> None:
    payload = build_payload()

    payload[
        "client_record_id"
    ] = "rule-no-material"

    payload["materials"] = []

    response = client.post(
        "/api/cultivation-logs/validate",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["valid"] is False

    assert any(
        item["code"]
        == "MATERIAL_REQUIRED_FOR_ACTIVITY"
        for item in body["errors"]
    )


def test_save_cannot_bypass_business_validation() -> None:
    payload = build_payload()

    payload[
        "client_record_id"
    ] = "rule-save-bypass"

    payload["materials"] = []

    response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert response.status_code == 400

    body = response.json()

    assert (
        body["detail"]["code"]
        == "BUSINESS_VALIDATION_FAILED"
    )

    assert any(
        item["code"]
        == "MATERIAL_REQUIRED_FOR_ACTIVITY"
        for item
        in body["detail"]["errors"]
    )


def test_tuoi_nuoc_without_material_remains_allowed_provisionally() -> None:
    payload = build_payload()

    payload[
        "client_record_id"
    ] = "rule-tuoi-nuoc"

    payload[
        "activity_code"
    ] = "TUOI_NUOC"

    payload["materials"] = []

    response = client.post(
        "/api/cultivation-logs/validate",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["valid"] is True


def test_unknown_activity_is_rejected() -> None:
    payload = build_payload()

    payload[
        "client_record_id"
    ] = "rule-unknown-activity"

    payload[
        "activity_code"
    ] = "KHONG_TON_TAI"

    response = client.post(
        "/api/cultivation-logs/validate",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["valid"] is False

    assert any(
        item["code"]
        == "UNKNOWN_ACTIVITY"
        for item in body["errors"]
    )


def test_unknown_lot_is_rejected() -> None:
    payload = build_payload()

    payload[
        "client_record_id"
    ] = "rule-unknown-lot"

    payload[
        "lot_code"
    ] = "LO_KHONG_TON_TAI"

    response = client.post(
        "/api/cultivation-logs/validate",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["valid"] is False

    assert any(
        item["code"]
        == "UNKNOWN_LOT"
        for item in body["errors"]
    )


def test_unknown_material_is_rejected() -> None:
    payload = build_payload()

    payload[
        "client_record_id"
    ] = "rule-unknown-material"

    payload[
        "materials"
    ][0][
        "material_code"
    ] = "XYZ"

    response = client.post(
        "/api/cultivation-logs/validate",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["valid"] is False

    assert any(
        item["code"]
        == "UNKNOWN_MATERIAL"
        for item in body["errors"]
    )


def test_unknown_unit_is_rejected() -> None:
    payload = build_payload()

    payload[
        "client_record_id"
    ] = "rule-unknown-unit"

    payload[
        "materials"
    ][0][
        "unit_code"
    ] = "THUNG"

    response = client.post(
        "/api/cultivation-logs/validate",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["valid"] is False

    assert any(
        item["code"]
        == "UNKNOWN_UNIT"
        for item in body["errors"]
    )


def test_unconfirmed_is_warning_requiring_confirmation() -> None:
    payload = build_payload()

    payload[
        "client_record_id"
    ] = "rule-unconfirmed"

    payload["confirmed"] = False

    response = client.post(
        "/api/cultivation-logs/validate",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["valid"] is True

    assert (
        body[
            "requires_confirmation"
        ]
        is True
    )

    warning = next(
        item
        for item
        in body["warnings"]
        if (
            item["code"]
            == "UNCONFIRMED_RECORD"
        )
    )

    assert (
        warning[
            "requires_confirmation"
        ]
        is True
    )


def test_quantity_threshold_is_not_hardcoded() -> None:
    payload = build_payload()

    payload[
        "client_record_id"
    ] = "rule-large-quantity"

    payload[
        "materials"
    ][0][
        "quantity"
    ] = 5000

    response = client.post(
        "/api/cultivation-logs/validate",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    # Chưa có business threshold được duyệt.
    assert body["valid"] is True

    assert not any(
        item["code"]
        == "QUANTITY_OUTLIER"
        for item in body["warnings"]
    )


def test_zero_quantity_is_schema_error() -> None:
    payload = build_payload()

    payload[
        "client_record_id"
    ] = "rule-zero-quantity"

    payload[
        "materials"
    ][0][
        "quantity"
    ] = 0

    response = client.post(
        "/api/cultivation-logs/validate",
        json=payload,
    )

    assert response.status_code == 422
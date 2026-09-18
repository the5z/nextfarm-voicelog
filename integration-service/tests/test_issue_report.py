from copy import deepcopy

from fastapi.testclient import TestClient


def build_valid_issue_report(
    client_record_id: str = (
        "issue-report-001"
    ),
) -> dict[str, object]:
    return {
        "client_record_id":
            client_record_id,
        "plot_text":
            "Lô A",
        "issue_type_text":
            "Sâu",
        "severity_text":
            "Cao",
        "description":
            "Phát hiện sâu ăn lá.",
        "photo":
            "photo-001.jpg",
        "note":
            "Kiểm tra lại vào buổi chiều.",
        "confirmed":
            True,
    }


def test_issue_reports_router(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/issue-reports/test"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
        "message": (
            "Issue reports router "
            "is working"
        ),
    }


def test_create_issue_report(
    client: TestClient,
) -> None:
    payload = build_valid_issue_report()

    response = client.post(
        "/api/issue-reports",
        json=payload,
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["success"] is True
    assert response_data["status"] == "saved"

    report = response_data["data"]

    assert (
        report["client_record_id"]
        == "issue-report-001"
    )
    assert report["plot_code"] == "LO_A"
    assert report["issue_type"] == "Sâu"
    assert report["severity"] == "Cao"
    assert (
        report["description"]
        == "Phát hiện sâu ăn lá."
    )
    assert report["photo"] == "photo-001.jpg"
    assert report["confirmed"] is True
    assert report["status"] == "saved"


def test_create_issue_report_resolves_plot_text(
    client: TestClient,
) -> None:
    payload = build_valid_issue_report(
        "issue-plot-resolution-001"
    )

    payload["plot_text"] = "Lô A"

    response = client.post(
        "/api/issue-reports",
        json=payload,
    )

    assert response.status_code == 201

    assert (
        response.json()["data"]["plot_code"]
        == "LO_A"
    )


def test_create_issue_report_rejects_unconfirmed(
    client: TestClient,
) -> None:
    payload = build_valid_issue_report(
        "issue-unconfirmed-001"
    )

    payload["confirmed"] = False

    response = client.post(
        "/api/issue-reports",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "UNCONFIRMED_RECORD"
    )

    list_response = client.get(
        "/api/issue-reports"
    )

    assert list_response.status_code == 200
    assert list_response.json()["data"] == []


def test_create_issue_report_rejects_invalid_issue_type(
    client: TestClient,
) -> None:
    payload = build_valid_issue_report(
        "issue-invalid-type-001"
    )

    payload["issue_type_text"] = "Côn trùng"

    response = client.post(
        "/api/issue-reports",
        json=payload,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert (
        detail["code"]
        == "ISSUE_REPORT_VALIDATION_FAILED"
    )
    assert detail["field"] == "issue_type_text"
    assert (
        detail["reason_code"]
        == "INVALID_ISSUE_TYPE"
    )


def test_create_issue_report_rejects_invalid_severity(
    client: TestClient,
) -> None:
    payload = build_valid_issue_report(
        "issue-invalid-severity-001"
    )

    payload["severity_text"] = "Rất cao"

    response = client.post(
        "/api/issue-reports",
        json=payload,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert (
        detail["code"]
        == "ISSUE_REPORT_VALIDATION_FAILED"
    )
    assert detail["field"] == "severity_text"
    assert (
        detail["reason_code"]
        == "INVALID_SEVERITY"
    )


def test_create_issue_report_rejects_unknown_plot(
    client: TestClient,
) -> None:
    payload = build_valid_issue_report(
        "issue-unknown-plot-001"
    )

    payload["plot_text"] = (
        "Khu vực không tồn tại"
    )

    response = client.post(
        "/api/issue-reports",
        json=payload,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert (
        detail["code"]
        == "ISSUE_REPORT_VALIDATION_FAILED"
    )
    assert detail["field"] == "plot_text"
    assert (
        detail["reason_code"]
        == "UNKNOWN_PLOT"
    )


def test_create_issue_report_is_idempotent(
    client: TestClient,
) -> None:
    payload = build_valid_issue_report(
        "issue-idempotent-001"
    )

    first_response = client.post(
        "/api/issue-reports",
        json=payload,
    )

    second_response = client.post(
        "/api/issue-reports",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    assert (
        first_response.json()["status"]
        == "saved"
    )

    assert (
        second_response.json()["status"]
        == "already_exists"
    )

    list_response = client.get(
        "/api/issue-reports"
    )

    assert len(
        list_response.json()["data"]
    ) == 1


def test_list_issue_reports(
    client: TestClient,
) -> None:
    first_payload = build_valid_issue_report(
        "issue-list-001"
    )

    second_payload = build_valid_issue_report(
        "issue-list-002"
    )

    second_payload["issue_type_text"] = "Bệnh"

    first_response = client.post(
        "/api/issue-reports",
        json=first_payload,
    )

    second_response = client.post(
        "/api/issue-reports",
        json=second_payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get(
        "/api/issue-reports"
    )

    assert response.status_code == 200

    reports = response.json()["data"]

    assert len(reports) == 2

    ids = {
        report["client_record_id"]
        for report in reports
    }

    assert ids == {
        "issue-list-001",
        "issue-list-002",
    }


def test_get_issue_report(
    client: TestClient,
) -> None:
    payload = build_valid_issue_report(
        "issue-detail-001"
    )

    save_response = client.post(
        "/api/issue-reports",
        json=payload,
    )

    assert save_response.status_code == 201

    response = client.get(
        "/api/issue-reports/issue-detail-001"
    )

    assert response.status_code == 200

    report = response.json()["data"]

    assert (
        report["client_record_id"]
        == "issue-detail-001"
    )
    assert report["plot_code"] == "LO_A"
    assert report["issue_type"] == "Sâu"
    assert report["severity"] == "Cao"


def test_get_issue_report_not_found(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/issue-reports/not-found-001"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]["code"]
        == "ISSUE_REPORT_NOT_FOUND"
    )


def test_update_issue_report(
    client: TestClient,
) -> None:
    payload = build_valid_issue_report(
        "issue-update-001"
    )

    save_response = client.post(
        "/api/issue-reports",
        json=payload,
    )

    assert save_response.status_code == 201

    update_payload = deepcopy(payload)

    update_payload["severity_text"] = "Nguy cấp"
    update_payload["description"] = (
        "Mức độ sâu hại tăng nhanh."
    )
    update_payload["note"] = (
        "Cần xử lý sớm."
    )

    update_response = client.put(
        "/api/issue-reports/issue-update-001",
        json=update_payload,
    )

    assert update_response.status_code == 200

    updated_report = (
        update_response.json()["data"]
    )

    assert (
        updated_report["severity"]
        == "Nguy cấp"
    )

    assert (
        updated_report["description"]
        == "Mức độ sâu hại tăng nhanh."
    )

    detail_response = client.get(
        "/api/issue-reports/issue-update-001"
    )

    assert detail_response.status_code == 200

    stored_report = (
        detail_response.json()["data"]
    )

    assert (
        stored_report["severity"]
        == "Nguy cấp"
    )
    assert (
        stored_report["note"]
        == "Cần xử lý sớm."
    )


def test_update_issue_report_not_found(
    client: TestClient,
) -> None:
    payload = build_valid_issue_report(
        "issue-update-not-found-001"
    )

    response = client.put(
        "/api/issue-reports/"
        "issue-update-not-found-001",
        json=payload,
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]["code"]
        == "ISSUE_REPORT_NOT_FOUND"
    )


def test_update_issue_report_rejects_id_mismatch(
    client: TestClient,
) -> None:
    payload = build_valid_issue_report(
        "issue-mismatch-001"
    )

    save_response = client.post(
        "/api/issue-reports",
        json=payload,
    )

    assert save_response.status_code == 201

    update_payload = deepcopy(payload)

    update_payload["client_record_id"] = (
        "issue-another-id-001"
    )

    response = client.put(
        "/api/issue-reports/issue-mismatch-001",
        json=update_payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "CLIENT_RECORD_ID_MISMATCH"
    )


def test_update_issue_report_rejects_unconfirmed(
    client: TestClient,
) -> None:
    payload = build_valid_issue_report(
        "issue-update-unconfirmed-001"
    )

    save_response = client.post(
        "/api/issue-reports",
        json=payload,
    )

    assert save_response.status_code == 201

    update_payload = deepcopy(payload)

    update_payload["confirmed"] = False
    update_payload["severity_text"] = "Nguy cấp"

    response = client.put(
        "/api/issue-reports/"
        "issue-update-unconfirmed-001",
        json=update_payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "UNCONFIRMED_RECORD"
    )

    detail_response = client.get(
        "/api/issue-reports/"
        "issue-update-unconfirmed-001"
    )

    stored_report = (
        detail_response.json()["data"]
    )

    assert stored_report["severity"] == "Cao"


def test_update_issue_report_rejects_invalid_business_value(
    client: TestClient,
) -> None:
    payload = build_valid_issue_report(
        "issue-update-invalid-001"
    )

    save_response = client.post(
        "/api/issue-reports",
        json=payload,
    )

    assert save_response.status_code == 201

    update_payload = deepcopy(payload)

    update_payload["severity_text"] = (
        "Không xác định"
    )

    response = client.put(
        "/api/issue-reports/"
        "issue-update-invalid-001",
        json=update_payload,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert (
        detail["reason_code"]
        == "INVALID_SEVERITY"
    )

    detail_response = client.get(
        "/api/issue-reports/"
        "issue-update-invalid-001"
    )

    stored_report = (
        detail_response.json()["data"]
    )

    assert stored_report["severity"] == "Cao"


def test_create_issue_report_requires_description(
    client: TestClient,
) -> None:
    payload = build_valid_issue_report(
        "issue-no-description-001"
    )

    del payload["description"]

    response = client.post(
        "/api/issue-reports",
        json=payload,
    )

    assert response.status_code == 422
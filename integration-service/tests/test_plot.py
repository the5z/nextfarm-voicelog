from copy import deepcopy
import json

import pytest
from fastapi.testclient import TestClient


REGION_ENV = "NEXTFARM_REGIONS_JSON"
CROP_ENV = "NEXTFARM_CROPS_JSON"


@pytest.fixture(autouse=True)
def configure_plot_sources(
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


def build_valid_plot(
    client_record_id: str = (
        "plot-create-001"
    ),
) -> dict[str, object]:
    return {
        "client_record_id":
            client_record_id,
        "plot_name_or_code":
            "Vườn Dâu Tây",
        "region_text":
            "Miền Bắc",
        "boundary_required":
            True,
        "owner_text":
            "Nguyễn Văn A",
        "current_crop_text":
            "Dâu tây",
        "location_hint_text":
            "Phía sau nhà kính số 1",
        "confirmed":
            True,
    }


def test_plots_router(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/plots/test"
    )

    assert response.status_code == 200


def test_create_plot(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/plots",
        json=build_valid_plot(),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["status"] == "saved"

    plot = body["data"]

    assert (
        plot["plot_code"]
        .startswith("LOCAL_PLOT_")
    )

    assert (
        plot["plot_name_or_code"]
        == "Vườn Dâu Tây"
    )

    assert (
        plot["region_id"]
        == "region-north"
    )

    assert (
        plot["current_crop_id"]
        == "crop-strawberry"
    )

    assert (
        plot["boundary_required"]
        is True
    )

    assert (
        plot["owner_text"]
        == "Nguyễn Văn A"
    )

    assert (
        plot["location_hint_text"]
        == "Phía sau nhà kính số 1"
    )


def test_create_plot_resolves_aliases(
    client: TestClient,
) -> None:
    payload = build_valid_plot(
        "plot-alias-001"
    )

    payload["region_text"] = "Bắc Bộ"
    payload["current_crop_text"] = "Dâu"

    response = client.post(
        "/api/plots",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()["data"]

    assert (
        data["region_id"]
        == "region-north"
    )

    assert (
        data["current_crop_id"]
        == "crop-strawberry"
    )


def test_create_plot_without_current_crop(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        CROP_ENV,
        raising=False,
    )

    payload = build_valid_plot(
        "plot-no-crop-001"
    )

    payload["current_crop_text"] = None

    response = client.post(
        "/api/plots",
        json=payload,
    )

    assert response.status_code == 201

    assert (
        response.json()["data"][
            "current_crop_id"
        ]
        is None
    )


def test_create_plot_rejects_unconfirmed(
    client: TestClient,
) -> None:
    payload = build_valid_plot(
        "plot-unconfirmed-001"
    )

    payload["confirmed"] = False

    response = client.post(
        "/api/plots",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "UNCONFIRMED_RECORD"
    )


def test_create_plot_requires_region_source(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        REGION_ENV,
        raising=False,
    )

    response = client.post(
        "/api/plots",
        json=build_valid_plot(
            "plot-no-region-source-001"
        ),
    )

    assert response.status_code == 503

    assert (
        response.json()["detail"]["code"]
        == "REGION_MASTER_DATA_UNAVAILABLE"
    )


def test_create_plot_rejects_unknown_region(
    client: TestClient,
) -> None:
    payload = build_valid_plot(
        "plot-region-001"
    )

    payload["region_text"] = (
        "Khu vực không tồn tại xyz"
    )

    response = client.post(
        "/api/plots",
        json=payload,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert detail["field"] == "region_text"

    assert (
        detail["reason_code"]
        == "UNKNOWN_REGION"
    )


def test_create_plot_requires_crop_source(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        CROP_ENV,
        raising=False,
    )

    response = client.post(
        "/api/plots",
        json=build_valid_plot(
            "plot-no-crop-source-001"
        ),
    )

    assert response.status_code == 503

    assert (
        response.json()["detail"]["code"]
        == "CROP_MASTER_DATA_UNAVAILABLE"
    )


def test_create_plot_rejects_unknown_crop(
    client: TestClient,
) -> None:
    payload = build_valid_plot(
        "plot-crop-001"
    )

    payload["current_crop_text"] = (
        "Cây hoàn toàn không tồn tại xyz"
    )

    response = client.post(
        "/api/plots",
        json=payload,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert (
        detail["field"]
        == "current_crop_text"
    )

    assert (
        detail["reason_code"]
        == "UNKNOWN_CURRENT_CROP"
    )


def test_create_plot_is_idempotent(
    client: TestClient,
) -> None:
    payload = build_valid_plot(
        "plot-idempotent-001"
    )

    first = client.post(
        "/api/plots",
        json=payload,
    )

    second = client.post(
        "/api/plots",
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

    assert (
        first.json()["data"]["plot_code"]
        == second.json()["data"]["plot_code"]
    )

    records = client.get(
        "/api/plots"
    ).json()["data"]

    assert len(records) == 1


def test_create_plot_rejects_duplicate_name(
    client: TestClient,
) -> None:
    first = build_valid_plot(
        "plot-name-001"
    )

    second = build_valid_plot(
        "plot-name-002"
    )

    assert client.post(
        "/api/plots",
        json=first,
    ).status_code == 201

    response = client.post(
        "/api/plots",
        json=second,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert (
        detail["field"]
        == "plot_name_or_code"
    )

    assert (
        detail["reason_code"]
        == "DUPLICATE_PLOT_NAME"
    )


def test_create_plot_rejects_existing_static_lot_name(
    client: TestClient,
) -> None:
    payload = build_valid_plot(
        "plot-static-name-001"
    )

    payload["plot_name_or_code"] = "Lô A"

    response = client.post(
        "/api/plots",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"][
            "reason_code"
        ]
        == "DUPLICATE_PLOT_NAME"
    )


def test_list_plots(
    client: TestClient,
) -> None:
    first = build_valid_plot(
        "plot-list-001"
    )

    second = build_valid_plot(
        "plot-list-002"
    )

    second["plot_name_or_code"] = (
        "Vườn Cam"
    )

    second["current_crop_text"] = "Cam"

    assert client.post(
        "/api/plots",
        json=first,
    ).status_code == 201

    assert client.post(
        "/api/plots",
        json=second,
    ).status_code == 201

    response = client.get(
        "/api/plots"
    )

    assert response.status_code == 200

    assert len(
        response.json()["data"]
    ) == 2


def test_get_plot(
    client: TestClient,
) -> None:
    payload = build_valid_plot(
        "plot-detail-001"
    )

    client.post(
        "/api/plots",
        json=payload,
    )

    response = client.get(
        "/api/plots/plot-detail-001"
    )

    assert response.status_code == 200

    assert (
        response.json()["data"][
            "client_record_id"
        ]
        == "plot-detail-001"
    )


def test_get_plot_not_found(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/plots/not-found"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]["code"]
        == "PLOT_NOT_FOUND"
    )


def test_update_plot(
    client: TestClient,
) -> None:
    payload = build_valid_plot(
        "plot-update-001"
    )

    assert client.post(
        "/api/plots",
        json=payload,
    ).status_code == 201

    original = client.get(
        "/api/plots/plot-update-001"
    ).json()["data"]

    updated = deepcopy(payload)

    updated["plot_name_or_code"] = (
        "Vườn Cam Miền Trung"
    )

    updated["region_text"] = (
        "Miền Trung"
    )

    updated["current_crop_text"] = "Cam"

    updated["boundary_required"] = False

    response = client.put(
        "/api/plots/plot-update-001",
        json=updated,
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert (
        data["plot_name_or_code"]
        == "Vườn Cam Miền Trung"
    )

    assert (
        data["region_id"]
        == "region-central"
    )

    assert (
        data["current_crop_id"]
        == "crop-orange"
    )

    assert (
        data["boundary_required"]
        is False
    )

    assert (
        data["plot_code"]
        == original["plot_code"]
    )


def test_update_plot_rejects_id_mismatch(
    client: TestClient,
) -> None:
    payload = build_valid_plot(
        "plot-mismatch-001"
    )

    client.post(
        "/api/plots",
        json=payload,
    )

    updated = deepcopy(payload)

    updated["client_record_id"] = (
        "different-id"
    )

    response = client.put(
        "/api/plots/plot-mismatch-001",
        json=updated,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "CLIENT_RECORD_ID_MISMATCH"
    )


def test_update_plot_rejects_unconfirmed(
    client: TestClient,
) -> None:
    payload = build_valid_plot(
        "plot-update-unconfirmed-001"
    )

    client.post(
        "/api/plots",
        json=payload,
    )

    updated = deepcopy(payload)

    updated["confirmed"] = False

    updated["plot_name_or_code"] = (
        "Tên không được lưu"
    )

    response = client.put(
        "/api/plots/"
        "plot-update-unconfirmed-001",
        json=updated,
    )

    assert response.status_code == 400

    stored = client.get(
        "/api/plots/"
        "plot-update-unconfirmed-001"
    ).json()["data"]

    assert (
        stored["plot_name_or_code"]
        == "Vườn Dâu Tây"
    )


def test_created_plot_is_available_in_lot_master_data(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/plots",
        json=build_valid_plot(
            "plot-master-data-001"
        ),
    )

    assert response.status_code == 201

    created = response.json()["data"]

    response = client.get(
        "/api/master-data/lots"
    )

    assert response.status_code == 200

    lots = response.json()

    matching = [
        item
        for item in lots
        if item["code"]
        == created["plot_code"]
    ]

    assert len(matching) == 1

    assert (
        matching[0]["name"]
        == "Vườn Dâu Tây"
    )


def test_created_plot_can_be_resolved_by_name_and_code(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/plots",
        json=build_valid_plot(
            "plot-resolver-001"
        ),
    )

    assert response.status_code == 201

    created = response.json()["data"]

    by_name = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "lot",
            "text": "Vườn Dâu Tây",
        },
    )

    assert by_name.status_code == 200

    assert (
        by_name.json()["code"]
        == created["plot_code"]
    )

    by_code = client.post(
        "/api/master-data/resolve",
        json={
            "data_type": "lot",
            "text": created["plot_code"],
        },
    )

    assert by_code.status_code == 200

    assert by_code.json()["matched"] is True

    assert (
        by_code.json()["code"]
        == created["plot_code"]
    )


def test_harvest_can_use_created_plot(
    client: TestClient,
) -> None:
    plot_response = client.post(
        "/api/plots",
        json=build_valid_plot(
            "plot-for-harvest-001"
        ),
    )

    assert plot_response.status_code == 201

    plot = plot_response.json()["data"]

    response = client.post(
        "/api/harvests",
        json={
            "client_record_id":
                "harvest-new-plot-001",
            "plot_text":
                "Vườn Dâu Tây",
            "crop_text":
                "Dâu tây",
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
        },
    )

    assert response.status_code == 201

    assert (
        response.json()["data"]["plot_code"]
        == plot["plot_code"]
    )


def test_season_can_use_created_plot(
    client: TestClient,
) -> None:
    plot_response = client.post(
        "/api/plots",
        json=build_valid_plot(
            "plot-for-season-001"
        ),
    )

    assert plot_response.status_code == 201

    plot = plot_response.json()["data"]

    response = client.post(
        "/api/seasons",
        json={
            "client_record_id":
                "season-new-plot-001",
            "plot_text":
                "Vườn Dâu Tây",
            "crop_text":
                "Dâu tây",
            "planting_date_text":
                "19/09/2026",
            "season_name":
                "Vụ Dâu Trên Thửa Mới",
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
        },
    )

    assert response.status_code == 201

    assert (
        response.json()["data"]["plot_code"]
        == plot["plot_code"]
    )


def test_issue_report_can_use_created_plot(
    client: TestClient,
) -> None:
    plot_response = client.post(
        "/api/plots",
        json=build_valid_plot(
            "plot-for-issue-001"
        ),
    )

    assert plot_response.status_code == 201

    plot = plot_response.json()["data"]

    response = client.post(
        "/api/issue-reports",
        json={
            "client_record_id":
                "issue-new-plot-001",
            "plot_text":
                "Vườn Dâu Tây",
            "issue_type_text":
                "Sâu",
            "severity_text":
                "Cao",
            "description":
                "Phát hiện sâu trên thửa mới.",
            "photo":
                None,
            "note":
                None,
            "confirmed":
                True,
        },
    )

    assert response.status_code == 201

    assert (
        response.json()["data"]["plot_code"]
        == plot["plot_code"]
    )


def test_dynamic_work_log_can_use_created_plot(
    client: TestClient,
) -> None:
    plot_response = client.post(
        "/api/plots",
        json=build_valid_plot(
            "plot-for-work-log-001"
        ),
    )

    assert plot_response.status_code == 201

    plot = plot_response.json()["data"]

    response = client.post(
        "/api/cultivation-logs/"
        "from-dynamic-form",
        json={
            "dynamic_form": {
                "contract_version":
                    "3.1",
                "operation":
                    "CREATE_WORK_LOG",
                "template_id":
                    "work_log",
                "transcript":
                    "Làm cỏ Vườn Dâu Tây",
                "current_fields": {
                    "result_status":
                        "completed",
                    "plot_text":
                        "Vườn Dâu Tây",
                    "activity_text":
                        "Làm cỏ",
                    "materials":
                        [],
                    "note":
                        None,
                },
                "context":
                    {},
            },
            "client_record_id":
                "work-log-new-plot-001",
            "performed_at":
                "2026-09-19T08:00:00+07:00",
            "context":
                None,
            "confirmed":
                True,
        },
    )

    assert response.status_code == 201

    assert (
        response.json()["data"]["lot_code"]
        == plot["plot_code"]
    )


def test_resolve_cultivation_can_use_created_plot(
    client: TestClient,
) -> None:
    plot_response = client.post(
        "/api/plots",
        json=build_valid_plot(
            "plot-for-resolver-001"
        ),
    )

    assert plot_response.status_code == 201

    plot = plot_response.json()["data"]

    response = client.post(
        "/api/master-data/"
        "resolve-cultivation",
        json={
            "activity_text":
                "Làm cỏ",
            "lot_text":
                "Vườn Dâu Tây",
            "materials":
                [],
            "time_text":
                "07:00",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["lot"]["matched"] is True

    assert (
        body["lot"]["code"]
        == plot["plot_code"]
    )
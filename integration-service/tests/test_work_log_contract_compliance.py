from datetime import datetime

from fastapi.testclient import TestClient

from app.schemas.cultivation_log import (
    CultivationLogInput,
)
from app.schemas.dynamic_form import (
    DynamicCreateWorkLogRequest,
    DynamicWorkLogFields,
)
from app.services.business_validation_service import (
    validate_business_rules,
)
from app.services.dynamic_form_adapter_service import (
    build_cultivation_log_input,
)


def test_adapter_preserves_work_log_contract_fields() -> None:
    request = DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript="Đã làm một phần công việc",
        current_fields=DynamicWorkLogFields(
            result_status="partial",
            material_batch_text="Lô vật tư 09-2026",
            note="Còn một phần chưa hoàn thành",
        ),
    )

    payload = build_cultivation_log_input(
        request,
        client_record_id="task5-adapter-001",
        performed_at=datetime(
            2026,
            9,
            16,
            8,
            0,
        ),
        confirmed=True,
    )

    assert payload.result_status == "partial"
    assert payload.material_batch_text == "Lô vật tư 09-2026"
    assert payload.lot_code is None
    assert payload.activity_code is None


def test_business_validation_allows_missing_optional_plot_activity() -> None:
    payload = CultivationLogInput(
        client_record_id="task5-validation-001",
        result_status="completed",
        lot_code=None,
        activity_code=None,
        materials=[],
        performed_at=datetime(
            2026,
            9,
            16,
            8,
            0,
        ),
        confirmed=True,
    )

    result = validate_business_rules(payload)

    assert result["valid"] is True
    assert result["errors"] == []


def test_dynamic_form_bridge_persists_contract_fields(
    client: TestClient,
) -> None:
    payload = {
        "dynamic_form": {
            "contract_version": "3.1",
            "operation": "CREATE_WORK_LOG",
            "template_id": "work_log",
            "transcript": "Đã hoàn thành công việc",
            "current_fields": {
                "result_status": "completed",
                "plot_text": None,
                "activity_text": None,
                "materials": [],
                "material_batch_text": "Lô vật tư 09-2026",
                "note": "Kiểm tra contract V3.1",
            },
            "context": {},
        },
        "client_record_id": "task5-bridge-001",
        "performed_at": "2026-09-16T08:00:00+07:00",
        "context": {
            "tenant_id": "tenant-001",
            "user_id": "user-001",
            "season_id": "season-2026",
            "plot_id": "plot-001",
            "task_id": "task-001",
        },
        "confirmed": True,
    }

    response = client.post(
        "/api/cultivation-logs/from-dynamic-form",
        json=payload,
    )

    assert response.status_code == 201

    record = response.json()["data"]

    assert record["result_status"] == "completed"
    assert record["material_batch_text"] == "Lô vật tư 09-2026"
    assert record["lot_code"] is None
    assert record["activity_code"] is None

    detail_response = client.get(
        "/api/cultivation-logs/task5-bridge-001"
    )

    assert detail_response.status_code == 200

    stored = detail_response.json()["data"]

    assert stored["result_status"] == "completed"
    assert stored["material_batch_text"] == "Lô vật tư 09-2026"
    assert stored["lot_code"] is None
    assert stored["activity_code"] is None


def test_update_round_trip_contract_fields(
    client: TestClient,
) -> None:
    payload = {
        "schema_version": "1.0",
        "client_record_id": "task5-update-001",
        "result_status": "partial",
        "lot_code": None,
        "activity_code": None,
        "materials": [],
        "performed_at": "2026-09-16T08:00:00+07:00",
        "material_batch_text": "Batch A",
        "source": "voice",
        "confirmed": True,
    }

    save_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert save_response.status_code == 201

    update_payload = dict(payload)
    update_payload["result_status"] = "completed"
    update_payload["material_batch_text"] = "Batch B"

    update_response = client.put(
        "/api/cultivation-logs/task5-update-001",
        json=update_payload,
    )

    assert update_response.status_code == 200

    updated = update_response.json()["data"]

    assert updated["result_status"] == "completed"
    assert updated["material_batch_text"] == "Batch B"

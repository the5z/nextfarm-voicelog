from fastapi.testclient import (
    TestClient,
)


def build_bridge_payload(
    *,
    client_record_id: str,
    confirmed: bool = True,
) -> dict:
    return {
        "dynamic_form": {
            "contract_version": "3.1",
            "operation": "CREATE_WORK_LOG",
            "template_id": "work_log",

            "transcript": (
                "Bón 20 kg NPK và "
                "5 kg urê cho lô A"
            ),

            "current_fields": {
                "result_status":
                    "completed",

                "plot_text":
                    "Lô A",

                "activity_text":
                    "Bón phân",

                "materials": [
                    {
                        "material_text":
                            "Phân NPK",

                        "quantity":
                            20,

                        "unit_text":
                            "kg",
                    },
                    {
                        "material_text":
                            "Phân urê",

                        "quantity":
                            5,

                        "unit_text":
                            "kg",
                    },
                ],

                "note":
                    "Bón phân buổi sáng",
            },

            "context": {},
        },

        "client_record_id":
            client_record_id,

        "performed_at":
            "2026-09-15T08:00:00+07:00",

        "context": {
            "tenant_id":
                "tenant-001",

            "user_id":
                "user-001",

            "season_id":
                "season-2026",

            "plot_id":
                "plot-001",

            "task_id":
                "task-001",
        },

        "confirmed":
            confirmed,
    }

def test_dynamic_form_bridge_saves_canonical_log(
    client: TestClient,
) -> None:
    payload = build_bridge_payload(
        client_record_id=(
            "dynamic-bridge-001"
        ),
    )

    response = client.post(
        (
            "/api/cultivation-logs/"
            "from-dynamic-form"
        ),
        json=payload,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["status"] == "saved"

    record = body["data"]

    assert record["activity_code"] == (
        "BON_PHAN"
    )

    assert record["lot_code"] == "LO_A"

    assert (
        record["materials"][0][
            "material_code"
        ]
        == "NPK"
    )

    assert (
        record["materials"][0][
            "unit_code"
        ]
        == "KG"
    )

    assert (
        record["materials"][1][
            "material_code"
        ]
        == "URE"
    )

    assert record["context"] == {
        "tenant_id": "tenant-001",
        "user_id": "user-001",
        "season_id": "season-2026",
        "plot_id": "plot-001",
        "task_id": "task-001",
    }

def test_dynamic_form_bridge_reuses_confirmation_gate(
    client: TestClient,
) -> None:
    payload = build_bridge_payload(
        client_record_id=(
            "dynamic-bridge-002"
        ),
        confirmed=False,
    )

    response = client.post(
        (
            "/api/cultivation-logs/"
            "from-dynamic-form"
        ),
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["code"]
        == "UNCONFIRMED_RECORD"
    )

def test_dynamic_form_bridge_rejects_unknown_material(
    client: TestClient,
) -> None:
    payload = build_bridge_payload(
        client_record_id=(
            "dynamic-bridge-003"
        ),
    )

    payload[
        "dynamic_form"
    ][
        "current_fields"
    ][
        "materials"
    ][0][
        "material_text"
    ] = "ABC Super 999"

    response = client.post(
        (
            "/api/cultivation-logs/"
            "from-dynamic-form"
        ),
        json=payload,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert detail["code"] == (
        "DYNAMIC_FORM_RESOLUTION_FAILED"
    )

    assert detail["reason_code"] == (
        "UNKNOWN_MASTER_DATA"
    )

    assert detail["field"] == (
        "materials[0].material_text"
    )

def test_dynamic_form_bridge_reuses_business_validation(
    client: TestClient,
) -> None:
    payload = build_bridge_payload(
        client_record_id=(
            "dynamic-bridge-004"
        ),
    )

    payload[
        "dynamic_form"
    ][
        "current_fields"
    ][
        "materials"
    ] = []

    response = client.post(
        (
            "/api/cultivation-logs/"
            "from-dynamic-form"
        ),
        json=payload,
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert detail["code"] == (
        "BUSINESS_VALIDATION_FAILED"
    )

    assert any(
        error["code"]
        == "MATERIAL_REQUIRED_FOR_ACTIVITY"
        for error
        in detail["errors"]
    )
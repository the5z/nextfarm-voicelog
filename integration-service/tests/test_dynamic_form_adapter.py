from datetime import datetime
from decimal import Decimal

import pytest

from app.schemas.dynamic_form import (
    DynamicCreateWorkLogRequest,
    DynamicWorkLogFields,
    DynamicWorkLogMaterial,
)
from app.schemas.nextfarm import (
    NextFarmContext,
)
from app.services.dynamic_form_adapter_service import (
    DynamicFormCanonicalResolutionError,
    build_cultivation_log_input,
)


def build_request(
    *,
    transcript: str | None = None,
) -> DynamicCreateWorkLogRequest:
    return DynamicCreateWorkLogRequest(
        operation="CREATE_WORK_LOG",
        template_id="work_log",
        transcript=transcript,
        current_fields=DynamicWorkLogFields(
            result_status="completed",
            activity_text="Bón phân",
            plot_text="Lô A",
            materials=[
                DynamicWorkLogMaterial(
                    material_text="Phân NPK",
                    quantity=Decimal("20"),
                    unit_text="kg",
                ),
                DynamicWorkLogMaterial(
                    material_text="Phân urê",
                    quantity=Decimal("5"),
                    unit_text="kg",
                ),
            ],
            note="Bón phân buổi sáng",
        ),
    )


def test_adapter_resolves_text_to_canonical_codes():
    request = build_request()

    payload = build_cultivation_log_input(
        request,
        client_record_id=(
            "dynamic-adapter-001"
        ),
        performed_at=datetime(
            2026,
            9,
            15,
            8,
            0,
        ),
        confirmed=True,
    )

    assert payload.activity_code == (
        "BON_PHAN"
    )

    assert payload.lot_code == "LO_A"

    assert len(payload.materials) == 2

    assert (
        payload.materials[0].material_code
        == "NPK"
    )

    assert (
        payload.materials[0].quantity
        == Decimal("20")
    )

    assert (
        payload.materials[0].unit_code
        == "KG"
    )

    assert (
        payload.materials[1].material_code
        == "URE"
    )

    assert (
        payload.materials[1].quantity
        == Decimal("5")
    )

    assert (
        payload.materials[1].unit_code
        == "KG"
    )


def test_adapter_does_not_parse_transcript():
    request = build_request(
        transcript=(
            "Tưới nước cho lô B"
        )
    )

    payload = build_cultivation_log_input(
        request,
        client_record_id=(
            "dynamic-adapter-002"
        ),
        performed_at=datetime(
            2026,
            9,
            15,
            8,
            0,
        ),
        confirmed=True,
    )

    # Structured fields là source
    # (nguồn dữ liệu) cho adapter.
    #
    # Transcript nói "Tưới nước / lô B"
    # nhưng adapter tuyệt đối không tự
    # parse transcript để ghi đè.
    assert payload.activity_code == (
        "BON_PHAN"
    )

    assert payload.lot_code == "LO_A"

    assert payload.transcript == (
        "Tưới nước cho lô B"
    )


def test_adapter_rejects_unknown_material_without_fallback():
    request = build_request()

    request.current_fields.materials[
        0
    ].material_text = "ABC Super 999"

    with pytest.raises(
        DynamicFormCanonicalResolutionError
    ) as error:
        build_cultivation_log_input(
            request,
            client_record_id=(
                "dynamic-adapter-003"
            ),
            performed_at=datetime(
                2026,
                9,
                15,
                8,
                0,
            ),
            confirmed=True,
        )

    assert error.value.field == (
        "materials[0].material_text"
    )

    assert error.value.code == (
        "UNKNOWN_MASTER_DATA"
    )


def test_adapter_rejects_ambiguous_unit():
    request = build_request()

    request.current_fields.materials[
        0
    ].unit_text = "xị"

    with pytest.raises(
        DynamicFormCanonicalResolutionError
    ) as error:
        build_cultivation_log_input(
            request,
            client_record_id=(
                "dynamic-adapter-004"
            ),
            performed_at=datetime(
                2026,
                9,
                15,
                8,
                0,
            ),
            confirmed=True,
        )

    assert error.value.field == (
        "materials[0].unit_text"
    )

    assert error.value.code == (
        "AMBIGUOUS_UNIT"
    )


def test_adapter_preserves_canonical_nextfarm_context():
    request = build_request()

    context = NextFarmContext(
        tenant_id="tenant-001",
        user_id="user-001",
        season_id="season-2026",
        plot_id="plot-001",
        task_id="task-001",
    )

    payload = build_cultivation_log_input(
        request,
        client_record_id=(
            "dynamic-adapter-005"
        ),
        performed_at=datetime(
            2026,
            9,
            15,
            8,
            0,
        ),
        context=context,
        confirmed=True,
    )

    assert payload.context == context

    assert (
        payload.context.plot_id
        == "plot-001"
    )

    assert (
        payload.context.task_id
        == "task-001"
    )
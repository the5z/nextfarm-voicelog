from __future__ import annotations

from typing import Any, Literal

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.harvest import (
    HarvestModel,
)
from app.schemas.harvest import (
    HarvestCreateRequest,
    HarvestInput,
)
from app.services.crop_master_data_service import (
    resolve_crop_text,
)
from app.services.normalization_service import (
    resolve_master_data,
)


HarvestValidationCode = Literal[
    "UNKNOWN_PLOT",
    "UNKNOWN_CROP",
    "UNKNOWN_UNIT",
]


class HarvestValidationError(
    ValueError
):
    def __init__(
        self,
        *,
        field: str,
        code: HarvestValidationCode,
        message: str,
    ) -> None:
        super().__init__(message)

        self.field = field
        self.code = code
        self.message = message


def _resolve_standard_code(
    *,
    data_type: Literal[
        "lot",
        "unit",
    ],
    text: str,
    field: str,
    error_code: HarvestValidationCode,
) -> str:
    result = resolve_master_data(
        data_type,
        text,
    )

    code = result.get(
        "code"
    )

    if (
        not result.get("matched")
        or not code
    ):
        raise HarvestValidationError(
            field=field,
            code=error_code,
            message=(
                f"Không thể ánh xạ "
                f"'{text}' sang dữ liệu chuẩn."
            ),
        )

    return (
        str(code)
        .strip()
        .upper()
    )


def build_harvest_input(
    request: HarvestCreateRequest,
) -> HarvestInput:
    """
    Chuyển CREATE_HARVEST dạng text
    thành dữ liệu canonical.

    Không:
    - đọc transcript
    - chạy NLP
    - tự sinh ID
    - tự suy diễn ngày thu hoạch
    """

    plot_code = _resolve_standard_code(
        data_type="lot",
        text=request.plot_text,
        field="plot_text",
        error_code="UNKNOWN_PLOT",
    )

    crop_result = resolve_crop_text(
        request.crop_text
    )

    crop_id = (
        crop_result.crop_id
    )

    if (
        not crop_result.matched
        or not crop_id
    ):
        raise HarvestValidationError(
            field="crop_text",
            code="UNKNOWN_CROP",
            message=(
                "Không thể ánh xạ "
                f"'{request.crop_text}' "
                "sang crop_id chuẩn."
            ),
        )

    unit_code = _resolve_standard_code(
        data_type="unit",
        text=request.unit_text,
        field="unit_text",
        error_code="UNKNOWN_UNIT",
    )

    return HarvestInput(
        client_record_id=(
            request.client_record_id
        ),
        plot_code=plot_code,
        crop_id=crop_id,
        quantity=request.quantity,
        unit_code=unit_code,
        harvest_date_text=(
            request.harvest_date_text
        ),
        photo=request.photo,
        note=request.note,
        confirmed=request.confirmed,
    )


def serialize_harvest(
    harvest: HarvestModel,
) -> dict[str, Any]:
    return {
        "id": harvest.id,
        "client_record_id": (
            harvest.client_record_id
        ),
        "plot_code": harvest.plot_code,
        "crop_id": harvest.crop_id,
        "quantity": float(
            harvest.quantity
        ),
        "unit_code": harvest.unit_code,
        "harvest_date_text": (
            harvest.harvest_date_text
        ),
        "photo": harvest.photo,
        "note": harvest.note,
        "confirmed": harvest.confirmed,
        "status": harvest.status,
        "created_at": (
            harvest.created_at.isoformat()
            if harvest.created_at is not None
            else None
        ),
    }


def find_harvest_by_client_record_id(
    database_session: Session,
    client_record_id: str,
) -> HarvestModel | None:
    statement = (
        select(HarvestModel)
        .where(
            HarvestModel.client_record_id
            == client_record_id
        )
    )

    return database_session.scalar(
        statement
    )


def create_harvest(
    database_session: Session,
    payload: HarvestInput,
) -> tuple[dict[str, Any], bool]:
    existing = (
        find_harvest_by_client_record_id(
            database_session,
            payload.client_record_id,
        )
    )

    if existing is not None:
        return (
            serialize_harvest(
                existing
            ),
            False,
        )

    harvest = HarvestModel(
        client_record_id=(
            payload.client_record_id
        ),
        plot_code=payload.plot_code,
        crop_id=payload.crop_id,
        quantity=payload.quantity,
        unit_code=payload.unit_code,
        harvest_date_text=(
            payload.harvest_date_text
        ),
        photo=payload.photo,
        note=payload.note,
        confirmed=payload.confirmed,
        status="saved",
    )

    database_session.add(
        harvest
    )

    try:
        database_session.commit()

    except IntegrityError:
        database_session.rollback()

        existing = (
            find_harvest_by_client_record_id(
                database_session,
                payload.client_record_id,
            )
        )

        if existing is not None:
            return (
                serialize_harvest(
                    existing
                ),
                False,
            )

        raise

    database_session.refresh(
        harvest
    )

    return (
        serialize_harvest(
            harvest
        ),
        True,
    )


def update_harvest(
    database_session: Session,
    client_record_id: str,
    payload: HarvestInput,
) -> dict[str, Any] | None:
    harvest = (
        find_harvest_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if harvest is None:
        return None

    harvest.plot_code = (
        payload.plot_code
    )

    harvest.crop_id = (
        payload.crop_id
    )

    harvest.quantity = (
        payload.quantity
    )

    harvest.unit_code = (
        payload.unit_code
    )

    harvest.harvest_date_text = (
        payload.harvest_date_text
    )

    harvest.photo = payload.photo
    harvest.note = payload.note
    harvest.confirmed = (
        payload.confirmed
    )
    harvest.status = "saved"

    try:
        database_session.commit()

    except Exception:
        database_session.rollback()
        raise

    database_session.refresh(
        harvest
    )

    return serialize_harvest(
        harvest
    )


def get_harvest_by_client_record_id(
    database_session: Session,
    client_record_id: str,
) -> dict[str, Any] | None:
    harvest = (
        find_harvest_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if harvest is None:
        return None

    return serialize_harvest(
        harvest
    )


def get_all_harvests(
    database_session: Session,
) -> list[dict[str, Any]]:
    statement = (
        select(HarvestModel)
        .order_by(
            HarvestModel.id.desc()
        )
    )

    records = (
        database_session
        .scalars(statement)
        .all()
    )

    return [
        serialize_harvest(
            harvest
        )
        for harvest in records
    ]


def clear_harvests(
    database_session: Session,
) -> None:
    """
    Chỉ dùng cho database kiểm thử.
    """

    database_session.execute(
        delete(HarvestModel)
    )

    database_session.commit()
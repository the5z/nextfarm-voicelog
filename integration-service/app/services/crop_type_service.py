from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.crop_type import (
    CropTypeModel,
)
from app.schemas.crop_type import (
    CropTypeCreateRequest,
    CropTypeInput,
)
from app.services.crop_master_data_service import (
    load_configured_crop_master_data,
)
from app.services.normalization_service import (
    normalize_text,
)


CropTypeValidationCode = Literal[
    "DUPLICATE_CROP_NAME",
]


class CropTypeValidationError(
    ValueError
):
    def __init__(
        self,
        *,
        field: str,
        code: CropTypeValidationCode,
        message: str,
    ) -> None:
        super().__init__(message)

        self.field = field
        self.code = code
        self.message = message


def build_crop_type_input(
    request: CropTypeCreateRequest,
) -> CropTypeInput:
    """
    crop_code_suggestion chỉ là gợi ý.

    Integration không dùng giá trị này
    làm business code cuối cùng.
    """

    return CropTypeInput(
        client_record_id=(
            request.client_record_id
        ),
        crop_name=request.crop_name,
        crop_group_text=(
            request.crop_group_text
        ),
        crop_code_suggestion=(
            request.crop_code_suggestion
        ),
        days_to_harvest=(
            request.days_to_harvest
        ),
        confirmed=request.confirmed,
    )


def _ensure_crop_name_available(
    database_session: Session,
    crop_name: str,
    *,
    exclude_client_record_id: (
        str | None
    ) = None,
) -> None:
    normalized_name = normalize_text(
        crop_name
    )

    for configured in (
        load_configured_crop_master_data()
    ):
        if (
            normalize_text(
                configured.name
            )
            == normalized_name
        ):
            raise CropTypeValidationError(
                field="crop_name",
                code="DUPLICATE_CROP_NAME",
                message=(
                    "Tên cây trồng đã tồn tại "
                    "trong dữ liệu canonical."
                ),
            )

        for alias in configured.aliases:
            if (
                normalize_text(alias)
                == normalized_name
            ):
                raise CropTypeValidationError(
                    field="crop_name",
                    code="DUPLICATE_CROP_NAME",
                    message=(
                        "Tên cây trồng trùng với "
                        "bí danh cây trồng hiện có."
                    ),
                )

    statement = (
        select(CropTypeModel)
        .where(
            CropTypeModel.status
            == "saved"
        )
    )

    records = (
        database_session
        .scalars(statement)
        .all()
    )

    for record in records:
        if (
            exclude_client_record_id
            is not None
            and record.client_record_id
            == exclude_client_record_id
        ):
            continue

        if (
            normalize_text(
                record.crop_name
            )
            == normalized_name
        ):
            raise CropTypeValidationError(
                field="crop_name",
                code="DUPLICATE_CROP_NAME",
                message=(
                    "Tên cây trồng đã tồn tại."
                ),
            )


def serialize_crop_type(
    crop: CropTypeModel,
) -> dict[str, Any]:
    return {
        "id": crop.id,
        "client_record_id": (
            crop.client_record_id
        ),
        "crop_id": crop.crop_id,
        "crop_name": crop.crop_name,
        "crop_group_text": (
            crop.crop_group_text
        ),
        "crop_code_suggestion": (
            crop.crop_code_suggestion
        ),
        "days_to_harvest": (
            crop.days_to_harvest
        ),
        "confirmed": crop.confirmed,
        "status": crop.status,
        "created_at": (
            crop.created_at.isoformat()
            if crop.created_at is not None
            else None
        ),
    }


def find_crop_type_by_client_record_id(
    database_session: Session,
    client_record_id: str,
) -> CropTypeModel | None:
    return database_session.scalar(
        select(CropTypeModel)
        .where(
            CropTypeModel.client_record_id
            == client_record_id
        )
    )


def create_crop_type(
    database_session: Session,
    payload: CropTypeInput,
) -> tuple[dict[str, Any], bool]:
    existing = (
        find_crop_type_by_client_record_id(
            database_session,
            payload.client_record_id,
        )
    )

    if existing is not None:
        return (
            serialize_crop_type(existing),
            False,
        )

    _ensure_crop_name_available(
        database_session,
        payload.crop_name,
    )

    crop = CropTypeModel(
        client_record_id=(
            payload.client_record_id
        ),
        crop_id=(
            f"local-crop-{uuid4()}"
        ),
        crop_name=payload.crop_name,
        crop_group_text=(
            payload.crop_group_text
        ),
        crop_code_suggestion=(
            payload.crop_code_suggestion
        ),
        days_to_harvest=(
            payload.days_to_harvest
        ),
        confirmed=payload.confirmed,
        status="saved",
    )

    database_session.add(
        crop
    )

    try:
        database_session.commit()

    except IntegrityError:
        database_session.rollback()

        existing = (
            find_crop_type_by_client_record_id(
                database_session,
                payload.client_record_id,
            )
        )

        if existing is not None:
            return (
                serialize_crop_type(
                    existing
                ),
                False,
            )

        raise

    database_session.refresh(
        crop
    )

    return (
        serialize_crop_type(crop),
        True,
    )


def update_crop_type(
    database_session: Session,
    client_record_id: str,
    payload: CropTypeInput,
) -> dict[str, Any] | None:
    crop = (
        find_crop_type_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if crop is None:
        return None

    _ensure_crop_name_available(
        database_session,
        payload.crop_name,
        exclude_client_record_id=(
            client_record_id
        ),
    )

    crop.crop_name = (
        payload.crop_name
    )

    crop.crop_group_text = (
        payload.crop_group_text
    )

    crop.crop_code_suggestion = (
        payload.crop_code_suggestion
    )

    crop.days_to_harvest = (
        payload.days_to_harvest
    )

    crop.confirmed = (
        payload.confirmed
    )

    crop.status = "saved"

    database_session.commit()
    database_session.refresh(
        crop
    )

    return serialize_crop_type(
        crop
    )


def get_crop_type_by_client_record_id(
    database_session: Session,
    client_record_id: str,
) -> dict[str, Any] | None:
    crop = (
        find_crop_type_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if crop is None:
        return None

    return serialize_crop_type(
        crop
    )


def get_all_crop_types(
    database_session: Session,
) -> list[dict[str, Any]]:
    records = (
        database_session
        .scalars(
            select(CropTypeModel)
            .order_by(
                CropTypeModel.id.desc()
            )
        )
        .all()
    )

    return [
        serialize_crop_type(record)
        for record in records
    ]


def clear_crop_types(
    database_session: Session,
) -> None:
    database_session.execute(
        delete(CropTypeModel)
    )

    database_session.commit()
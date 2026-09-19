from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.data.master_data import LOTS
from app.models.plot import PlotModel
from app.schemas.plot import (
    PlotCreateRequest,
    PlotInput,
)
from app.services.crop_master_data_service import (
    resolve_crop_text,
)
from app.services.normalization_service import (
    normalize_text,
)
from app.services.region_master_data_service import (
    resolve_region_text,
)


PlotValidationCode = Literal[
    "UNKNOWN_REGION",
    "UNKNOWN_CURRENT_CROP",
    "DUPLICATE_PLOT_NAME",
]


class PlotValidationError(
    ValueError
):
    def __init__(
        self,
        *,
        field: str,
        code: PlotValidationCode,
        message: str,
    ) -> None:
        super().__init__(message)

        self.field = field
        self.code = code
        self.message = message


def build_plot_input(
    request: PlotCreateRequest,
    database_session: Session | None = None,
) -> PlotInput:
    region_result = resolve_region_text(
        request.region_text
    )

    if (
        not region_result.matched
        or not region_result.region_id
    ):
        raise PlotValidationError(
            field="region_text",
            code="UNKNOWN_REGION",
            message=(
                "Không thể ánh xạ "
                f"'{request.region_text}' "
                "sang region_id chuẩn."
            ),
        )

    current_crop_id = None

    if request.current_crop_text:
        crop_result = resolve_crop_text(
            request.current_crop_text,
            database_session,
        )

        if (
            not crop_result.matched
            or not crop_result.crop_id
        ):
            raise PlotValidationError(
                field="current_crop_text",
                code="UNKNOWN_CURRENT_CROP",
                message=(
                    "Không thể ánh xạ "
                    f"'{request.current_crop_text}' "
                    "sang crop_id chuẩn."
                ),
            )

        current_crop_id = (
            crop_result.crop_id
        )

    return PlotInput(
        client_record_id=(
            request.client_record_id
        ),
        plot_name_or_code=(
            request.plot_name_or_code
        ),
        region_id=(
            region_result.region_id
        ),
        boundary_required=(
            request.boundary_required
        ),
        owner_text=request.owner_text,
        current_crop_id=current_crop_id,
        location_hint_text=(
            request.location_hint_text
        ),
        confirmed=request.confirmed,
    )


def _ensure_plot_name_available(
    database_session: Session,
    plot_name_or_code: str,
    *,
    exclude_client_record_id: (
        str | None
    ) = None,
) -> None:
    normalized_name = normalize_text(
        plot_name_or_code
    )

    for record in LOTS:
        candidates = [
            record["code"],
            record["name"],
            *record.get(
                "aliases",
                [],
            ),
        ]

        for candidate in candidates:
            if (
                normalize_text(
                    str(candidate)
                )
                == normalized_name
            ):
                raise PlotValidationError(
                    field="plot_name_or_code",
                    code="DUPLICATE_PLOT_NAME",
                    message=(
                        "Tên/mã thửa đất "
                        "đã tồn tại trong "
                        "dữ liệu chuẩn."
                    ),
                )

    records = (
        database_session
        .scalars(
            select(PlotModel)
            .where(
                PlotModel.status
                == "saved"
            )
        )
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
                record.plot_name_or_code
            )
            == normalized_name
        ):
            raise PlotValidationError(
                field="plot_name_or_code",
                code="DUPLICATE_PLOT_NAME",
                message=(
                    "Tên/mã thửa đất "
                    "đã tồn tại."
                ),
            )


def serialize_plot(
    plot: PlotModel,
) -> dict[str, Any]:
    return {
        "id": plot.id,
        "client_record_id":
            plot.client_record_id,
        "plot_code": plot.plot_code,
        "plot_name_or_code":
            plot.plot_name_or_code,
        "region_id": plot.region_id,
        "boundary_required":
            plot.boundary_required,
        "owner_text":
            plot.owner_text,
        "current_crop_id":
            plot.current_crop_id,
        "location_hint_text":
            plot.location_hint_text,
        "confirmed":
            plot.confirmed,
        "status":
            plot.status,
        "created_at": (
            plot.created_at.isoformat()
            if plot.created_at is not None
            else None
        ),
    }


def find_plot_by_client_record_id(
    database_session: Session,
    client_record_id: str,
) -> PlotModel | None:
    return database_session.scalar(
        select(PlotModel)
        .where(
            PlotModel.client_record_id
            == client_record_id
        )
    )


def create_plot(
    database_session: Session,
    payload: PlotInput,
) -> tuple[dict[str, Any], bool]:
    existing = (
        find_plot_by_client_record_id(
            database_session,
            payload.client_record_id,
        )
    )

    if existing is not None:
        return (
            serialize_plot(existing),
            False,
        )

    _ensure_plot_name_available(
        database_session,
        payload.plot_name_or_code,
    )

    plot = PlotModel(
        client_record_id=(
            payload.client_record_id
        ),
        plot_code=(
            f"LOCAL_PLOT_{uuid4().hex.upper()}"
        ),
        plot_name_or_code=(
            payload.plot_name_or_code
        ),
        region_id=payload.region_id,
        boundary_required=(
            payload.boundary_required
        ),
        owner_text=(
            payload.owner_text
        ),
        current_crop_id=(
            payload.current_crop_id
        ),
        location_hint_text=(
            payload.location_hint_text
        ),
        confirmed=payload.confirmed,
        status="saved",
    )

    database_session.add(plot)

    try:
        database_session.commit()

    except IntegrityError:
        database_session.rollback()

        existing = (
            find_plot_by_client_record_id(
                database_session,
                payload.client_record_id,
            )
        )

        if existing is not None:
            return (
                serialize_plot(existing),
                False,
            )

        raise

    database_session.refresh(plot)

    return (
        serialize_plot(plot),
        True,
    )


def update_plot(
    database_session: Session,
    client_record_id: str,
    payload: PlotInput,
) -> dict[str, Any] | None:
    plot = (
        find_plot_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if plot is None:
        return None

    _ensure_plot_name_available(
        database_session,
        payload.plot_name_or_code,
        exclude_client_record_id=(
            client_record_id
        ),
    )

    plot.plot_name_or_code = (
        payload.plot_name_or_code
    )

    plot.region_id = (
        payload.region_id
    )

    plot.boundary_required = (
        payload.boundary_required
    )

    plot.owner_text = (
        payload.owner_text
    )

    plot.current_crop_id = (
        payload.current_crop_id
    )

    plot.location_hint_text = (
        payload.location_hint_text
    )

    plot.confirmed = (
        payload.confirmed
    )

    plot.status = "saved"

    database_session.commit()
    database_session.refresh(plot)

    return serialize_plot(plot)


def get_plot_by_client_record_id(
    database_session: Session,
    client_record_id: str,
) -> dict[str, Any] | None:
    plot = (
        find_plot_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if plot is None:
        return None

    return serialize_plot(plot)


def get_all_plots(
    database_session: Session,
) -> list[dict[str, Any]]:
    records = (
        database_session
        .scalars(
            select(PlotModel)
            .order_by(
                PlotModel.id.desc()
            )
        )
        .all()
    )

    return [
        serialize_plot(record)
        for record in records
    ]


def clear_plots(
    database_session: Session,
) -> None:
    database_session.execute(
        delete(PlotModel)
    )

    database_session.commit()
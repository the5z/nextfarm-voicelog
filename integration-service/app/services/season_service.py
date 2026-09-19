from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.season import SeasonModel
from app.schemas.season import (
    SeasonCreateRequest,
    SeasonInput,
)
from app.services.crop_master_data_service import (
    resolve_crop_text,
)
from app.services.normalization_service import (
    normalize_text,
    resolve_master_data,
)
from app.services.season_master_data_service import (
    load_configured_season_master_data,
)


SeasonValidationCode = Literal[
    "UNKNOWN_PLOT",
    "UNKNOWN_CROP",
    "UNKNOWN_EXPECTED_YIELD_UNIT",
    "DUPLICATE_SEASON_NAME",
]


class SeasonValidationError(
    ValueError
):
    def __init__(
        self,
        *,
        field: str,
        code: SeasonValidationCode,
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
    error_code: SeasonValidationCode,
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
        raise SeasonValidationError(
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


def build_season_input(
    request: SeasonCreateRequest,
) -> SeasonInput:
    plot_code = _resolve_standard_code(
        data_type="lot",
        text=request.plot_text,
        field="plot_text",
        error_code="UNKNOWN_PLOT",
    )

    crop_result = resolve_crop_text(
        request.crop_text
    )

    if (
        not crop_result.matched
        or not crop_result.crop_id
    ):
        raise SeasonValidationError(
            field="crop_text",
            code="UNKNOWN_CROP",
            message=(
                "Không thể ánh xạ "
                f"'{request.crop_text}' "
                "sang crop_id chuẩn."
            ),
        )

    expected_yield_unit_code = None

    if request.expected_yield_unit_text:
        expected_yield_unit_code = (
            _resolve_standard_code(
                data_type="unit",
                text=(
                    request
                    .expected_yield_unit_text
                ),
                field=(
                    "expected_yield_unit_text"
                ),
                error_code=(
                    "UNKNOWN_EXPECTED_YIELD_UNIT"
                ),
            )
        )

    return SeasonInput(
        client_record_id=(
            request.client_record_id
        ),
        plot_code=plot_code,
        crop_id=crop_result.crop_id,
        planting_date_text=(
            request.planting_date_text
        ),
        season_name=request.season_name,
        expected_harvest_date_text=(
            request
            .expected_harvest_date_text
        ),
        plant_count=request.plant_count,
        expected_yield=(
            request.expected_yield
        ),
        expected_yield_unit_code=(
            expected_yield_unit_code
        ),
        process_template_text=(
            request.process_template_text
        ),
        confirmed=request.confirmed,
    )


def _ensure_season_name_available(
    database_session: Session,
    season_name: str,
    *,
    exclude_client_record_id: (
        str | None
    ) = None,
) -> None:
    normalized_name = normalize_text(
        season_name
    )

    for configured in (
        load_configured_season_master_data()
    ):
        if (
            normalize_text(
                configured.name
            )
            == normalized_name
        ):
            raise SeasonValidationError(
                field="season_name",
                code="DUPLICATE_SEASON_NAME",
                message=(
                    "Tên mùa vụ đã tồn tại "
                    "trong dữ liệu canonical."
                ),
            )

        for alias in configured.aliases:
            if (
                normalize_text(alias)
                == normalized_name
            ):
                raise SeasonValidationError(
                    field="season_name",
                    code=(
                        "DUPLICATE_SEASON_NAME"
                    ),
                    message=(
                        "Tên mùa vụ trùng với "
                        "bí danh mùa vụ hiện có."
                    ),
                )

    statement = (
        select(SeasonModel)
        .where(
            SeasonModel.status
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
                record.season_name
            )
            == normalized_name
        ):
            raise SeasonValidationError(
                field="season_name",
                code="DUPLICATE_SEASON_NAME",
                message=(
                    "Tên mùa vụ đã tồn tại."
                ),
            )


def serialize_season(
    season: SeasonModel,
) -> dict[str, Any]:
    return {
        "id": season.id,
        "client_record_id": (
            season.client_record_id
        ),
        "season_id": season.season_id,
        "plot_code": season.plot_code,
        "crop_id": season.crop_id,
        "planting_date_text": (
            season.planting_date_text
        ),
        "season_name": (
            season.season_name
        ),
        "expected_harvest_date_text": (
            season
            .expected_harvest_date_text
        ),
        "plant_count": season.plant_count,
        "expected_yield": (
            float(season.expected_yield)
            if season.expected_yield
            is not None
            else None
        ),
        "expected_yield_unit_code": (
            season
            .expected_yield_unit_code
        ),
        "process_template_text": (
            season.process_template_text
        ),
        "confirmed": season.confirmed,
        "status": season.status,
        "created_at": (
            season.created_at.isoformat()
            if season.created_at is not None
            else None
        ),
    }


def find_season_by_client_record_id(
    database_session: Session,
    client_record_id: str,
) -> SeasonModel | None:
    return database_session.scalar(
        select(SeasonModel)
        .where(
            SeasonModel.client_record_id
            == client_record_id
        )
    )


def create_season(
    database_session: Session,
    payload: SeasonInput,
) -> tuple[dict[str, Any], bool]:
    existing = (
        find_season_by_client_record_id(
            database_session,
            payload.client_record_id,
        )
    )

    if existing is not None:
        return (
            serialize_season(existing),
            False,
        )

    _ensure_season_name_available(
        database_session,
        payload.season_name,
    )

    season = SeasonModel(
        client_record_id=(
            payload.client_record_id
        ),
        season_id=(
            f"local-season-{uuid4()}"
        ),
        plot_code=payload.plot_code,
        crop_id=payload.crop_id,
        planting_date_text=(
            payload.planting_date_text
        ),
        season_name=payload.season_name,
        expected_harvest_date_text=(
            payload
            .expected_harvest_date_text
        ),
        plant_count=payload.plant_count,
        expected_yield=(
            payload.expected_yield
        ),
        expected_yield_unit_code=(
            payload
            .expected_yield_unit_code
        ),
        process_template_text=(
            payload.process_template_text
        ),
        confirmed=payload.confirmed,
        status="saved",
    )

    database_session.add(
        season
    )

    try:
        database_session.commit()

    except IntegrityError:
        database_session.rollback()

        existing = (
            find_season_by_client_record_id(
                database_session,
                payload.client_record_id,
            )
        )

        if existing is not None:
            return (
                serialize_season(existing),
                False,
            )

        raise

    database_session.refresh(
        season
    )

    return (
        serialize_season(season),
        True,
    )


def update_season(
    database_session: Session,
    client_record_id: str,
    payload: SeasonInput,
) -> dict[str, Any] | None:
    season = (
        find_season_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if season is None:
        return None

    _ensure_season_name_available(
        database_session,
        payload.season_name,
        exclude_client_record_id=(
            client_record_id
        ),
    )

    season.plot_code = payload.plot_code
    season.crop_id = payload.crop_id

    season.planting_date_text = (
        payload.planting_date_text
    )

    season.season_name = (
        payload.season_name
    )

    season.expected_harvest_date_text = (
        payload
        .expected_harvest_date_text
    )

    season.plant_count = (
        payload.plant_count
    )

    season.expected_yield = (
        payload.expected_yield
    )

    season.expected_yield_unit_code = (
        payload
        .expected_yield_unit_code
    )

    season.process_template_text = (
        payload.process_template_text
    )

    season.confirmed = (
        payload.confirmed
    )

    season.status = "saved"

    database_session.commit()
    database_session.refresh(
        season
    )

    return serialize_season(
        season
    )


def get_season_by_client_record_id(
    database_session: Session,
    client_record_id: str,
) -> dict[str, Any] | None:
    season = (
        find_season_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if season is None:
        return None

    return serialize_season(
        season
    )


def get_all_seasons(
    database_session: Session,
) -> list[dict[str, Any]]:
    records = (
        database_session
        .scalars(
            select(SeasonModel)
            .order_by(
                SeasonModel.id.desc()
            )
        )
        .all()
    )

    return [
        serialize_season(record)
        for record in records
    ]


def clear_seasons(
    database_session: Session,
) -> None:
    database_session.execute(
        delete(SeasonModel)
    )

    database_session.commit()
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.season import (
    SeasonCreateRequest,
    SeasonGetResponse,
    SeasonListResponse,
    SeasonSaveResponse,
)
from app.services.crop_master_data_service import (
    CropMasterDataConfigurationError,
)
from app.services.history_service import (
    create_history,
)
from app.services.season_service import (
    SeasonValidationError,
    build_season_input,
    create_season,
    get_all_seasons,
    get_season_by_client_record_id,
    update_season,
)


router = APIRouter(
    prefix="/api/seasons",
    tags=["Seasons"],
)


@router.get("/test")
def test_seasons_router(
) -> dict[str, str]:
    return {
        "status": "ok",
        "message": "Seasons router is working",
    }


def _write_failed_history(
    *,
    database_session: Session,
    event_type: str,
    client_record_id: str,
    request_payload: dict,
    detail: dict,
    http_status: int,
) -> None:
    create_history(
        database_session=database_session,
        event_type=event_type,
        client_record_id=client_record_id,
        request_payload=request_payload,
        response_payload={
            "detail": detail,
        },
        status="failed",
        http_status=http_status,
    )


def _raise_validation_error(
    *,
    error: SeasonValidationError,
    payload: SeasonCreateRequest,
    database_session: Session,
    event_type: str,
) -> None:
    detail = {
        "code": "SEASON_VALIDATION_FAILED",
        "field": error.field,
        "reason_code": error.code,
        "message": error.message,
    }

    _write_failed_history(
        database_session=database_session,
        event_type=event_type,
        client_record_id=(
            payload.client_record_id
        ),
        request_payload=(
            payload.model_dump(
                mode="json"
            )
        ),
        detail=detail,
        http_status=400,
    )

    raise HTTPException(
        status_code=400,
        detail=detail,
    ) from error


def _build_canonical_payload(
    *,
    payload: SeasonCreateRequest,
    database_session: Session,
    event_type: str,
):
    try:
        return build_season_input(
            payload
        )

    except (
        CropMasterDataConfigurationError
    ) as error:
        detail = {
            "code": (
                "CROP_MASTER_DATA_UNAVAILABLE"
            ),
            "message": str(error),
        }

        _write_failed_history(
            database_session=database_session,
            event_type=event_type,
            client_record_id=(
                payload.client_record_id
            ),
            request_payload=(
                payload.model_dump(
                    mode="json"
                )
            ),
            detail=detail,
            http_status=503,
        )

        raise HTTPException(
            status_code=503,
            detail=detail,
        ) from error

    except SeasonValidationError as error:
        _raise_validation_error(
            error=error,
            payload=payload,
            database_session=(
                database_session
            ),
            event_type=event_type,
        )


@router.post(
    "",
    status_code=(
        status.HTTP_201_CREATED
    ),
    response_model=SeasonSaveResponse,
)
def save_season(
    payload: SeasonCreateRequest,
    database_session: Session = Depends(
        get_db
    ),
) -> SeasonSaveResponse:
    request_payload = (
        payload.model_dump(
            mode="json"
        )
    )

    if not payload.confirmed:
        detail = {
            "code": "UNCONFIRMED_RECORD",
            "message": (
                "Mùa vụ chưa được "
                "người dùng xác nhận."
            ),
        }

        _write_failed_history(
            database_session=database_session,
            event_type="save_season",
            client_record_id=(
                payload.client_record_id
            ),
            request_payload=request_payload,
            detail=detail,
            http_status=400,
        )

        raise HTTPException(
            status_code=400,
            detail=detail,
        )

    canonical_payload = (
        _build_canonical_payload(
            payload=payload,
            database_session=(
                database_session
            ),
            event_type="save_season",
        )
    )

    try:
        record, created = create_season(
            database_session,
            canonical_payload,
        )

    except SeasonValidationError as error:
        _raise_validation_error(
            error=error,
            payload=payload,
            database_session=(
                database_session
            ),
            event_type="save_season",
        )

    response = SeasonSaveResponse(
        success=True,
        status=(
            "saved"
            if created
            else "already_exists"
        ),
        data=record,
    )

    create_history(
        database_session=database_session,
        event_type="save_season",
        client_record_id=(
            payload.client_record_id
        ),
        request_payload=request_payload,
        response_payload=(
            response.model_dump(
                mode="json"
            )
        ),
        status="success",
        http_status=201,
    )

    return response


@router.put(
    "/{client_record_id}",
    response_model=SeasonSaveResponse,
)
def update_saved_season(
    client_record_id: str,
    payload: SeasonCreateRequest,
    database_session: Session = Depends(
        get_db
    ),
) -> SeasonSaveResponse:
    request_payload = (
        payload.model_dump(
            mode="json"
        )
    )

    if (
        client_record_id
        != payload.client_record_id
    ):
        detail = {
            "code":
                "CLIENT_RECORD_ID_MISMATCH",
            "message": (
                "client_record_id trong URL "
                "không khớp với payload."
            ),
        }

        _write_failed_history(
            database_session=database_session,
            event_type="update_season",
            client_record_id=(
                client_record_id
            ),
            request_payload=request_payload,
            detail=detail,
            http_status=400,
        )

        raise HTTPException(
            status_code=400,
            detail=detail,
        )

    existing = (
        get_season_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if existing is None:
        detail = {
            "code": "SEASON_NOT_FOUND",
            "message": (
                "Không tìm thấy mùa vụ."
            ),
        }

        _write_failed_history(
            database_session=database_session,
            event_type="update_season",
            client_record_id=(
                client_record_id
            ),
            request_payload=request_payload,
            detail=detail,
            http_status=404,
        )

        raise HTTPException(
            status_code=404,
            detail=detail,
        )

    if not payload.confirmed:
        detail = {
            "code": "UNCONFIRMED_RECORD",
            "message": (
                "Mùa vụ chưa được "
                "người dùng xác nhận."
            ),
        }

        _write_failed_history(
            database_session=database_session,
            event_type="update_season",
            client_record_id=(
                client_record_id
            ),
            request_payload=request_payload,
            detail=detail,
            http_status=400,
        )

        raise HTTPException(
            status_code=400,
            detail=detail,
        )

    canonical_payload = (
        _build_canonical_payload(
            payload=payload,
            database_session=(
                database_session
            ),
            event_type="update_season",
        )
    )

    try:
        record = update_season(
            database_session,
            client_record_id,
            canonical_payload,
        )

    except SeasonValidationError as error:
        _raise_validation_error(
            error=error,
            payload=payload,
            database_session=(
                database_session
            ),
            event_type="update_season",
        )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "SEASON_NOT_FOUND",
                "message": (
                    "Không tìm thấy mùa vụ."
                ),
            },
        )

    response = SeasonSaveResponse(
        success=True,
        status="updated",
        data=record,
    )

    create_history(
        database_session=database_session,
        event_type="update_season",
        client_record_id=(
            client_record_id
        ),
        request_payload=request_payload,
        response_payload=(
            response.model_dump(
                mode="json"
            )
        ),
        status="success",
        http_status=200,
    )

    return response


@router.get(
    "",
    response_model=SeasonListResponse,
)
def list_seasons(
    database_session: Session = Depends(
        get_db
    ),
) -> SeasonListResponse:
    return SeasonListResponse(
        success=True,
        data=get_all_seasons(
            database_session
        ),
    )


@router.get(
    "/{client_record_id}",
    response_model=SeasonGetResponse,
)
def get_season(
    client_record_id: str,
    database_session: Session = Depends(
        get_db
    ),
) -> SeasonGetResponse:
    record = (
        get_season_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "SEASON_NOT_FOUND",
                "message": (
                    "Không tìm thấy mùa vụ."
                ),
            },
        )

    return SeasonGetResponse(
        success=True,
        data=record,
    )
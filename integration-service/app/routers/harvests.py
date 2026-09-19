from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.harvest import (
    HarvestCreateRequest,
    HarvestGetResponse,
    HarvestListResponse,
    HarvestSaveResponse,
)
from app.services.crop_master_data_service import (
    CropMasterDataConfigurationError,
)
from app.services.harvest_service import (
    HarvestValidationError,
    build_harvest_input,
    create_harvest,
    get_all_harvests,
    get_harvest_by_client_record_id,
    update_harvest,
)
from app.services.history_service import (
    create_history,
)


router = APIRouter(
    prefix="/api/harvests",
    tags=["Harvests"],
)


@router.get("/test")
def test_harvests_router(
) -> dict[str, str]:
    return {
        "status": "ok",
        "message": (
            "Harvests router is working"
        ),
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


def _build_canonical_payload(
    *,
    payload: HarvestCreateRequest,
    database_session: Session,
    event_type: str,
):
    request_payload = (
        payload.model_dump(
            mode="json"
        )
    )

    try:
        return build_harvest_input(
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
            database_session=(
                database_session
            ),
            event_type=event_type,
            client_record_id=(
                payload.client_record_id
            ),
            request_payload=(
                request_payload
            ),
            detail=detail,
            http_status=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
        )

        raise HTTPException(
            status_code=503,
            detail=detail,
        ) from error

    except HarvestValidationError as error:
        detail = {
            "code": (
                "HARVEST_VALIDATION_FAILED"
            ),
            "field": error.field,
            "reason_code": error.code,
            "message": error.message,
        }

        _write_failed_history(
            database_session=(
                database_session
            ),
            event_type=event_type,
            client_record_id=(
                payload.client_record_id
            ),
            request_payload=(
                request_payload
            ),
            detail=detail,
            http_status=400,
        )

        raise HTTPException(
            status_code=400,
            detail=detail,
        ) from error


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=HarvestSaveResponse,
)
def save_harvest(
    payload: HarvestCreateRequest,
    database_session: Session = Depends(
        get_db
    ),
) -> HarvestSaveResponse:
    request_payload = (
        payload.model_dump(
            mode="json"
        )
    )

    if not payload.confirmed:
        detail = {
            "code": "UNCONFIRMED_RECORD",
            "message": (
                "Bản ghi thu hoạch chưa "
                "được người dùng xác nhận."
            ),
        }

        _write_failed_history(
            database_session=(
                database_session
            ),
            event_type="save_harvest",
            client_record_id=(
                payload.client_record_id
            ),
            request_payload=(
                request_payload
            ),
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
            event_type="save_harvest",
        )
    )

    record, created = create_harvest(
        database_session,
        canonical_payload,
    )

    response = HarvestSaveResponse(
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
        event_type="save_harvest",
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
    response_model=HarvestSaveResponse,
)
def update_saved_harvest(
    client_record_id: str,
    payload: HarvestCreateRequest,
    database_session: Session = Depends(
        get_db
    ),
) -> HarvestSaveResponse:
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
            "code": (
                "CLIENT_RECORD_ID_MISMATCH"
            ),
            "message": (
                "client_record_id trong URL "
                "không khớp với payload."
            ),
        }

        _write_failed_history(
            database_session=(
                database_session
            ),
            event_type="update_harvest",
            client_record_id=(
                client_record_id
            ),
            request_payload=(
                request_payload
            ),
            detail=detail,
            http_status=400,
        )

        raise HTTPException(
            status_code=400,
            detail=detail,
        )

    existing = (
        get_harvest_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if existing is None:
        detail = {
            "code": "HARVEST_NOT_FOUND",
            "message": (
                "Không tìm thấy "
                "bản ghi thu hoạch."
            ),
        }

        _write_failed_history(
            database_session=(
                database_session
            ),
            event_type="update_harvest",
            client_record_id=(
                client_record_id
            ),
            request_payload=(
                request_payload
            ),
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
                "Bản ghi thu hoạch chưa "
                "được người dùng xác nhận."
            ),
        }

        _write_failed_history(
            database_session=(
                database_session
            ),
            event_type="update_harvest",
            client_record_id=(
                client_record_id
            ),
            request_payload=(
                request_payload
            ),
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
            event_type="update_harvest",
        )
    )

    record = update_harvest(
        database_session,
        client_record_id,
        canonical_payload,
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code":
                    "HARVEST_NOT_FOUND",
                "message": (
                    "Không tìm thấy "
                    "bản ghi thu hoạch."
                ),
            },
        )

    response = HarvestSaveResponse(
        success=True,
        status="updated",
        data=record,
    )

    create_history(
        database_session=database_session,
        event_type="update_harvest",
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
    response_model=HarvestListResponse,
)
def list_harvests(
    database_session: Session = Depends(
        get_db
    ),
) -> HarvestListResponse:
    return HarvestListResponse(
        success=True,
        data=get_all_harvests(
            database_session
        ),
    )


@router.get(
    "/{client_record_id}",
    response_model=HarvestGetResponse,
)
def get_harvest(
    client_record_id: str,
    database_session: Session = Depends(
        get_db
    ),
) -> HarvestGetResponse:
    record = (
        get_harvest_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code":
                    "HARVEST_NOT_FOUND",
                "message": (
                    "Không tìm thấy "
                    "bản ghi thu hoạch."
                ),
            },
        )

    return HarvestGetResponse(
        success=True,
        data=record,
    )
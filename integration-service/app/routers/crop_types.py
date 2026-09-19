from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.crop_type import (
    CropTypeCreateRequest,
    CropTypeGetResponse,
    CropTypeListResponse,
    CropTypeSaveResponse,
)
from app.services.crop_master_data_service import (
    CropMasterDataConfigurationError,
)
from app.services.crop_type_service import (
    CropTypeValidationError,
    build_crop_type_input,
    create_crop_type,
    get_all_crop_types,
    get_crop_type_by_client_record_id,
    update_crop_type,
)
from app.services.history_service import (
    create_history,
)


router = APIRouter(
    prefix="/api/crop-types",
    tags=["Crop Types"],
)


@router.get("/test")
def test_crop_types_router(
) -> dict[str, str]:
    return {
        "status": "ok",
        "message": (
            "Crop types router is working"
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


def _raise_validation_error(
    *,
    error: CropTypeValidationError,
    payload: CropTypeCreateRequest,
    database_session: Session,
    event_type: str,
) -> None:
    detail = {
        "code": (
            "CROP_TYPE_VALIDATION_FAILED"
        ),
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


def _raise_master_data_error(
    *,
    error: CropMasterDataConfigurationError,
    payload: CropTypeCreateRequest,
    database_session: Session,
    event_type: str,
) -> None:
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


@router.post(
    "",
    status_code=(
        status.HTTP_201_CREATED
    ),
    response_model=CropTypeSaveResponse,
)
def save_crop_type(
    payload: CropTypeCreateRequest,
    database_session: Session = Depends(
        get_db
    ),
) -> CropTypeSaveResponse:
    request_payload = (
        payload.model_dump(
            mode="json"
        )
    )

    if not payload.confirmed:
        detail = {
            "code": "UNCONFIRMED_RECORD",
            "message": (
                "Loại cây trồng chưa được "
                "người dùng xác nhận."
            ),
        }

        _write_failed_history(
            database_session=database_session,
            event_type="save_crop_type",
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
        build_crop_type_input(
            payload
        )
    )

    try:
        record, created = (
            create_crop_type(
                database_session,
                canonical_payload,
            )
        )

    except (
        CropMasterDataConfigurationError
    ) as error:
        _raise_master_data_error(
            error=error,
            payload=payload,
            database_session=(
                database_session
            ),
            event_type="save_crop_type",
        )

    except CropTypeValidationError as error:
        _raise_validation_error(
            error=error,
            payload=payload,
            database_session=(
                database_session
            ),
            event_type="save_crop_type",
        )

    response = CropTypeSaveResponse(
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
        event_type="save_crop_type",
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
    response_model=CropTypeSaveResponse,
)
def update_saved_crop_type(
    client_record_id: str,
    payload: CropTypeCreateRequest,
    database_session: Session = Depends(
        get_db
    ),
) -> CropTypeSaveResponse:
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
            event_type="update_crop_type",
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
        get_crop_type_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if existing is None:
        detail = {
            "code": "CROP_TYPE_NOT_FOUND",
            "message": (
                "Không tìm thấy "
                "loại cây trồng."
            ),
        }

        _write_failed_history(
            database_session=database_session,
            event_type="update_crop_type",
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
                "Loại cây trồng chưa được "
                "người dùng xác nhận."
            ),
        }

        _write_failed_history(
            database_session=database_session,
            event_type="update_crop_type",
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
        build_crop_type_input(
            payload
        )
    )

    try:
        record = update_crop_type(
            database_session,
            client_record_id,
            canonical_payload,
        )

    except (
        CropMasterDataConfigurationError
    ) as error:
        _raise_master_data_error(
            error=error,
            payload=payload,
            database_session=(
                database_session
            ),
            event_type="update_crop_type",
        )

    except CropTypeValidationError as error:
        _raise_validation_error(
            error=error,
            payload=payload,
            database_session=(
                database_session
            ),
            event_type="update_crop_type",
        )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code":
                    "CROP_TYPE_NOT_FOUND",
                "message": (
                    "Không tìm thấy "
                    "loại cây trồng."
                ),
            },
        )

    response = CropTypeSaveResponse(
        success=True,
        status="updated",
        data=record,
    )

    create_history(
        database_session=database_session,
        event_type="update_crop_type",
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
    response_model=CropTypeListResponse,
)
def list_crop_types(
    database_session: Session = Depends(
        get_db
    ),
) -> CropTypeListResponse:
    return CropTypeListResponse(
        success=True,
        data=get_all_crop_types(
            database_session
        ),
    )


@router.get(
    "/{client_record_id}",
    response_model=CropTypeGetResponse,
)
def get_crop_type(
    client_record_id: str,
    database_session: Session = Depends(
        get_db
    ),
) -> CropTypeGetResponse:
    record = (
        get_crop_type_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code":
                    "CROP_TYPE_NOT_FOUND",
                "message": (
                    "Không tìm thấy "
                    "loại cây trồng."
                ),
            },
        )

    return CropTypeGetResponse(
        success=True,
        data=record,
    )
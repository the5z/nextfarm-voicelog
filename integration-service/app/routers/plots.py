from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.plot import (
    PlotCreateRequest,
    PlotGetResponse,
    PlotListResponse,
    PlotSaveResponse,
)
from app.services.crop_master_data_service import (
    CropMasterDataConfigurationError,
)
from app.services.history_service import (
    create_history,
)
from app.services.plot_service import (
    PlotValidationError,
    build_plot_input,
    create_plot,
    get_all_plots,
    get_plot_by_client_record_id,
    update_plot,
)
from app.services.region_master_data_service import (
    RegionMasterDataConfigurationError,
)


router = APIRouter(
    prefix="/api/plots",
    tags=["Plots"],
)


@router.get("/test")
def test_plots_router(
) -> dict[str, str]:
    return {
        "status": "ok",
        "message": "Plots router is working",
    }


def _failed(
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


def _build_payload(
    *,
    payload: PlotCreateRequest,
    database_session: Session,
    event_type: str,
):
    try:
        return build_plot_input(
            payload,
            database_session,
        )

    except (
        RegionMasterDataConfigurationError
    ) as error:
        detail = {
            "code":
                "REGION_MASTER_DATA_UNAVAILABLE",
            "message": str(error),
        }

        _failed(
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

    except (
        CropMasterDataConfigurationError
    ) as error:
        detail = {
            "code":
                "CROP_MASTER_DATA_UNAVAILABLE",
            "message": str(error),
        }

        _failed(
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

    except PlotValidationError as error:
        detail = {
            "code":
                "PLOT_VALIDATION_FAILED",
            "field": error.field,
            "reason_code": error.code,
            "message": error.message,
        }

        _failed(
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


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PlotSaveResponse,
)
def save_plot(
    payload: PlotCreateRequest,
    database_session: Session = Depends(
        get_db
    ),
) -> PlotSaveResponse:
    request_payload = payload.model_dump(
        mode="json"
    )

    if not payload.confirmed:
        detail = {
            "code": "UNCONFIRMED_RECORD",
            "message": (
                "Thửa đất chưa được "
                "người dùng xác nhận."
            ),
        }

        _failed(
            database_session=database_session,
            event_type="save_plot",
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

    canonical_payload = _build_payload(
        payload=payload,
        database_session=database_session,
        event_type="save_plot",
    )

    try:
        record, created = create_plot(
            database_session,
            canonical_payload,
        )

    except PlotValidationError as error:
        detail = {
            "code":
                "PLOT_VALIDATION_FAILED",
            "field": error.field,
            "reason_code": error.code,
            "message": error.message,
        }

        _failed(
            database_session=database_session,
            event_type="save_plot",
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
        ) from error

    response = PlotSaveResponse(
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
        event_type="save_plot",
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
    response_model=PlotSaveResponse,
)
def update_saved_plot(
    client_record_id: str,
    payload: PlotCreateRequest,
    database_session: Session = Depends(
        get_db
    ),
) -> PlotSaveResponse:
    request_payload = payload.model_dump(
        mode="json"
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

        _failed(
            database_session=database_session,
            event_type="update_plot",
            client_record_id=client_record_id,
            request_payload=request_payload,
            detail=detail,
            http_status=400,
        )

        raise HTTPException(
            status_code=400,
            detail=detail,
        )

    existing = (
        get_plot_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if existing is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PLOT_NOT_FOUND",
                "message":
                    "Không tìm thấy thửa đất.",
            },
        )

    if not payload.confirmed:
        raise HTTPException(
            status_code=400,
            detail={
                "code":
                    "UNCONFIRMED_RECORD",
                "message": (
                    "Thửa đất chưa được "
                    "người dùng xác nhận."
                ),
            },
        )

    canonical_payload = _build_payload(
        payload=payload,
        database_session=database_session,
        event_type="update_plot",
    )

    try:
        record = update_plot(
            database_session,
            client_record_id,
            canonical_payload,
        )

    except PlotValidationError as error:
        raise HTTPException(
            status_code=400,
            detail={
                "code":
                    "PLOT_VALIDATION_FAILED",
                "field": error.field,
                "reason_code": error.code,
                "message": error.message,
            },
        ) from error

    if record is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PLOT_NOT_FOUND",
                "message":
                    "Không tìm thấy thửa đất.",
            },
        )

    return PlotSaveResponse(
        success=True,
        status="updated",
        data=record,
    )


@router.get(
    "",
    response_model=PlotListResponse,
)
def list_plots(
    database_session: Session = Depends(
        get_db
    ),
) -> PlotListResponse:
    return PlotListResponse(
        success=True,
        data=get_all_plots(
            database_session
        ),
    )


@router.get(
    "/{client_record_id}",
    response_model=PlotGetResponse,
)
def get_plot(
    client_record_id: str,
    database_session: Session = Depends(
        get_db
    ),
) -> PlotGetResponse:
    record = (
        get_plot_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PLOT_NOT_FOUND",
                "message":
                    "Không tìm thấy thửa đất.",
            },
        )

    return PlotGetResponse(
        success=True,
        data=record,
    )
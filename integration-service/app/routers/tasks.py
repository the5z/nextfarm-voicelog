from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.task import (
    TaskCreateRequest,
    TaskGetResponse,
    TaskListResponse,
    TaskSaveResponse,
)
from app.services.history_service import (
    create_history,
)
from app.services.season_master_data_service import (
    SeasonMasterDataConfigurationError,
)
from app.services.task_service import (
    TaskValidationError,
    build_task_input,
    create_task,
    get_all_tasks,
    get_task_by_client_record_id,
    update_task,
)


router = APIRouter(
    prefix="/api/tasks",
    tags=["Tasks"],
)


@router.get("/test")
def test_tasks_router() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "Tasks router is working",
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


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskSaveResponse,
)
def save_task(
    payload: TaskCreateRequest,
    database_session: Session = Depends(
        get_db
    ),
) -> TaskSaveResponse:
    request_payload = payload.model_dump(
        mode="json"
    )

    if not payload.confirmed:
        detail = {
            "code": "UNCONFIRMED_RECORD",
            "message": (
                "Công việc chưa được "
                "người dùng xác nhận."
            ),
        }

        _write_failed_history(
            database_session=database_session,
            event_type="save_task",
            client_record_id=(
                payload.client_record_id
            ),
            request_payload=request_payload,
            detail=detail,
            http_status=(
                status.HTTP_400_BAD_REQUEST
            ),
        )

        raise HTTPException(
            status_code=400,
            detail=detail,
        )

    try:
        canonical_payload = (
            build_task_input(payload)
        )

    except (
        SeasonMasterDataConfigurationError
    ) as error:
        detail = {
            "code": (
                "SEASON_MASTER_DATA_UNAVAILABLE"
            ),
            "message": str(error),
        }

        _write_failed_history(
            database_session=database_session,
            event_type="save_task",
            client_record_id=(
                payload.client_record_id
            ),
            request_payload=request_payload,
            detail=detail,
            http_status=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
        )

        raise HTTPException(
            status_code=503,
            detail=detail,
        ) from error

    except TaskValidationError as error:
        detail = {
            "code": "TASK_VALIDATION_FAILED",
            "field": error.field,
            "reason_code": error.code,
            "message": error.message,
        }

        _write_failed_history(
            database_session=database_session,
            event_type="save_task",
            client_record_id=(
                payload.client_record_id
            ),
            request_payload=request_payload,
            detail=detail,
            http_status=(
                status.HTTP_400_BAD_REQUEST
            ),
        )

        raise HTTPException(
            status_code=400,
            detail=detail,
        ) from error

    record, created = create_task(
        database_session,
        canonical_payload,
    )

    response = TaskSaveResponse(
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
        event_type="save_task",
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
    response_model=TaskSaveResponse,
)
def update_saved_task(
    client_record_id: str,
    payload: TaskCreateRequest,
    database_session: Session = Depends(
        get_db
    ),
) -> TaskSaveResponse:
    request_payload = payload.model_dump(
        mode="json"
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
            database_session=database_session,
            event_type="update_task",
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
        get_task_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if existing is None:
        detail = {
            "code": "TASK_NOT_FOUND",
            "message": (
                "Không tìm thấy công việc."
            ),
        }

        _write_failed_history(
            database_session=database_session,
            event_type="update_task",
            client_record_id=client_record_id,
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
                "Công việc chưa được "
                "người dùng xác nhận."
            ),
        }

        _write_failed_history(
            database_session=database_session,
            event_type="update_task",
            client_record_id=client_record_id,
            request_payload=request_payload,
            detail=detail,
            http_status=400,
        )

        raise HTTPException(
            status_code=400,
            detail=detail,
        )

    try:
        canonical_payload = (
            build_task_input(payload)
        )

    except (
        SeasonMasterDataConfigurationError
    ) as error:
        detail = {
            "code": (
                "SEASON_MASTER_DATA_UNAVAILABLE"
            ),
            "message": str(error),
        }

        _write_failed_history(
            database_session=database_session,
            event_type="update_task",
            client_record_id=client_record_id,
            request_payload=request_payload,
            detail=detail,
            http_status=503,
        )

        raise HTTPException(
            status_code=503,
            detail=detail,
        ) from error

    except TaskValidationError as error:
        detail = {
            "code": "TASK_VALIDATION_FAILED",
            "field": error.field,
            "reason_code": error.code,
            "message": error.message,
        }

        _write_failed_history(
            database_session=database_session,
            event_type="update_task",
            client_record_id=client_record_id,
            request_payload=request_payload,
            detail=detail,
            http_status=400,
        )

        raise HTTPException(
            status_code=400,
            detail=detail,
        ) from error

    record = update_task(
        database_session,
        client_record_id,
        canonical_payload,
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": (
                    "Không tìm thấy công việc."
                ),
            },
        )

    response = TaskSaveResponse(
        success=True,
        status="updated",
        data=record,
    )

    create_history(
        database_session=database_session,
        event_type="update_task",
        client_record_id=client_record_id,
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
    response_model=TaskListResponse,
)
def list_tasks(
    database_session: Session = Depends(
        get_db
    ),
) -> TaskListResponse:
    return TaskListResponse(
        success=True,
        data=get_all_tasks(
            database_session
        ),
    )


@router.get(
    "/{client_record_id}",
    response_model=TaskGetResponse,
)
def get_task(
    client_record_id: str,
    database_session: Session = Depends(
        get_db
    ),
) -> TaskGetResponse:
    record = (
        get_task_by_client_record_id(
            database_session,
            client_record_id,
        )
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": (
                    "Không tìm thấy công việc."
                ),
            },
        )

    return TaskGetResponse(
        success=True,
        data=record,
    )
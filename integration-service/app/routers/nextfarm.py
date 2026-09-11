from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.clients.nextfarm_client import (
    NextFarmConfigurationError,
    NextFarmRequestError,
)
from app.database import get_db
from app.schemas.nextfarm import NextFarmSubmitResponse
from app.services.history_service import create_history
from app.services.nextfarm_service import (
    NextFarmContextValidationError,
    NextFarmLogNotFoundError,
    submit_saved_log_to_nextfarm,
)

router = APIRouter(
    prefix="/api/nextfarm",
    tags=["NextFarm Integration"],
)


@router.get("/test")
def test_nextfarm_router() -> dict[str, str]:
    """
    Kiểm tra router tích hợp NextFarm.
    """

    return {
        "status": "ok",
        "message": "NextFarm integration router is working",
    }


@router.post(
    "/cultivation-logs/{client_record_id}/submit",
    response_model=NextFarmSubmitResponse,
)
def submit_cultivation_log_to_nextfarm(
    client_record_id: str,
    database_session: Session = Depends(get_db),
) -> NextFarmSubmitResponse:
    """
    Gửi một nhật ký đã lưu sang NextFarm
    và ghi lại lịch sử xử lý.
    """

    request_payload = {
        "client_record_id": client_record_id,
    }

    try:
        result = submit_saved_log_to_nextfarm(
            database_session=database_session,
            client_record_id=client_record_id,
        )

    except NextFarmLogNotFoundError as error:
        error_detail = {
            "code": "CULTIVATION_LOG_NOT_FOUND",
            "message": str(error),
        }

        create_history(
            database_session=database_session,
            event_type="submit_nextfarm",
            client_record_id=client_record_id,
            request_payload=request_payload,
            response_payload={
                "detail": error_detail,
            },
            status="failed",
            http_status=status.HTTP_404_NOT_FOUND,
        )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_detail,
        ) from error

    except NextFarmConfigurationError as error:
        error_detail = {
            "code": "NEXTFARM_CONFIGURATION_ERROR",
            "message": str(error),
        }

        create_history(
            database_session=database_session,
            event_type="submit_nextfarm",
            client_record_id=client_record_id,
            request_payload=request_payload,
            response_payload={
                "detail": error_detail,
            },
            status="failed",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail,
        ) from error

    except NextFarmRequestError as error:
        error_detail = {
            "code": "NEXTFARM_REQUEST_ERROR",
            "message": str(error),
            "upstream_status_code": error.status_code,
        }

        create_history(
            database_session=database_session,
            event_type="submit_nextfarm",
            client_record_id=client_record_id,
            request_payload=request_payload,
            response_payload={
                "detail": error_detail,
            },
            status="failed",
            http_status=status.HTTP_502_BAD_GATEWAY,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error_detail,
        ) from error
    except NextFarmContextValidationError as error:
        error_detail = {
            "code": "NEXTFARM_SUBMIT_FAILED",
            "message": str(error),
        }

        create_history(
            database_session=database_session,
            event_type="submit_nextfarm",
            client_record_id=client_record_id,
            request_payload=request_payload,
            response_payload={
                "detail": error_detail,
            },
            status="failed",
            http_status=status.HTTP_400_BAD_REQUEST,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail,
    ) from error
    except ValueError as error:
        error_detail = {
            "code": "NEXTFARM_MAPPING_ERROR",
            "message": str(error),
        }

        create_history(
            database_session=database_session,
            event_type="submit_nextfarm",
            client_record_id=client_record_id,
            request_payload=request_payload,
            response_payload={
                "detail": error_detail,
            },
            status="failed",
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_detail,
        ) from error

    response = NextFarmSubmitResponse.model_validate(
        result
    )

    create_history(
        database_session=database_session,
        event_type="submit_nextfarm",
        client_record_id=client_record_id,
        request_payload=request_payload,
        response_payload=response.model_dump(
            mode="json"
        ),
        status="success",
        http_status=status.HTTP_200_OK,
    )

    return response
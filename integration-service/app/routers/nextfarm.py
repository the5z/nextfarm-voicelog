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
from app.services.nextfarm_service import (
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
    Gửi một nhật ký đã lưu sang NextFarm.
    """

    try:
        result = submit_saved_log_to_nextfarm(
            database_session=database_session,
            client_record_id=client_record_id,
        )

    except NextFarmLogNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CULTIVATION_LOG_NOT_FOUND",
                "message": str(error),
            },
        ) from error

    except NextFarmConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "NEXTFARM_CONFIGURATION_ERROR",
                "message": str(error),
            },
        ) from error

    except NextFarmRequestError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "NEXTFARM_REQUEST_ERROR",
                "message": str(error),
                "upstream_status_code": error.status_code,
            },
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "NEXTFARM_MAPPING_ERROR",
                "message": str(error),
            },
        ) from error

    return NextFarmSubmitResponse.model_validate(result)
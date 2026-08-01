from fastapi import APIRouter, HTTPException, status

from app.schemas.cultivation_log import CultivationLogInput
from app.services.log_service import create_log, get_all_logs
from app.schemas.responses import (
    ListLogsResponse,
    SaveLogResponse,
    ValidationResponse,
)

router = APIRouter(
    prefix="/api/cultivation-logs",
    tags=["Cultivation Logs"],
)


@router.get("/test")
def test_cultivation_logs() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "Cultivation logs router is working",
    }


@router.post(
    "/validate",
    response_model=ValidationResponse,
)
def validate_cultivation_log(
    payload: CultivationLogInput,
) -> ValidationResponse:
    errors = []
    warnings = []

    if not payload.confirmed:
        warnings.append(
            {
                "field": "confirmed",
                "code": "UNCONFIRMED_RECORD",
                "message": "Nhật ký chưa được người dùng xác nhận",
            }
        )

    if not payload.materials:
        warnings.append(
            {
                "field": "materials",
                "code": "EMPTY_MATERIALS",
                "message": "Nhật ký chưa có thông tin vật tư",
            }
        )

    return ValidationResponse(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        normalized_data=payload.model_dump(mode="json"),
    )

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SaveLogResponse,
)
def save_cultivation_log(
    payload: CultivationLogInput,
) -> SaveLogResponse:
    if not payload.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "UNCONFIRMED_RECORD",
                "message": "Nhật ký chưa được người dùng xác nhận",
            },
        )

    record, created = create_log(payload)

    if not created:
        return SaveLogResponse(
            success=True,
            status="already_exists",
            data=record,
        )

    return SaveLogResponse(
        success=True,
        status="saved",
        data=record,
    )


@router.get(
    "",
    response_model=ListLogsResponse,
)
def list_cultivation_logs() -> ListLogsResponse:
    return ListLogsResponse(
        success=True,
        data=get_all_logs(),
    )
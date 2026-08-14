from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.cultivation_log import CultivationLogInput
from app.schemas.responses import (
    GetLogResponse,
    ListLogsResponse,
    SaveLogResponse,
    ValidationResponse,
)
from app.services.log_service import (
    create_log,
    get_all_logs,
    get_log_by_client_record_id,
)


router = APIRouter(
    prefix="/api/cultivation-logs",
    tags=["Cultivation Logs"],
)


@router.get("/test")
def test_cultivation_logs_router() -> dict[str, str]:
    """
    Kiểm tra router nhật ký có hoạt động hay không.
    """

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
    """
    Kiểm tra dữ liệu nhật ký nhưng không lưu vào database.

    Các lỗi kiểu dữ liệu, thiếu trường hoặc số lượng không hợp lệ
    đã được Pydantic xử lý trước khi hàm này chạy.
    """

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if not payload.confirmed:
        warnings.append(
            {
                "field": "confirmed",
                "code": "UNCONFIRMED_RECORD",
                "message": (
                    "Nhật ký chưa được người dùng xác nhận"
                ),
            }
        )

    if not payload.materials:
        warnings.append(
            {
                "field": "materials",
                "code": "EMPTY_MATERIALS",
                "message": (
                    "Nhật ký chưa có thông tin vật tư"
                ),
            }
        )

    return ValidationResponse(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        normalized_data=payload.model_dump(
            mode="json"
        ),
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SaveLogResponse,
)
def save_cultivation_log(
    payload: CultivationLogInput,
    database_session: Session = Depends(get_db),
) -> SaveLogResponse:
    """
    Lưu nhật ký đã được người dùng xác nhận vào PostgreSQL.
    """

    if not payload.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "UNCONFIRMED_RECORD",
                "message": (
                    "Nhật ký chưa được người dùng xác nhận"
                ),
            },
        )

    record, created = create_log(
        database_session=database_session,
        payload=payload,
    )

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
def list_cultivation_logs(
    database_session: Session = Depends(get_db),
) -> ListLogsResponse:
    """
    Lấy danh sách nhật ký từ PostgreSQL.
    """

    records = get_all_logs(
        database_session=database_session
    )

    return ListLogsResponse(
        success=True,
        data=records,
    )

@router.get(
    "/{client_record_id}",
    response_model=GetLogResponse,
)
def get_cultivation_log(
    client_record_id: str,
    database_session: Session = Depends(get_db),
) -> GetLogResponse:
    """
    Lấy chi tiết một nhật ký theo client_record_id.
    """

    record = get_log_by_client_record_id(
        database_session=database_session,
        client_record_id=client_record_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CULTIVATION_LOG_NOT_FOUND",
                "message": "Không tìm thấy nhật ký.",
            },
        )

    return GetLogResponse(
        success=True,
        data=record,
    )
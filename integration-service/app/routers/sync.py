from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.sync import (
    SyncLogsRequest,
    SyncLogsResponse,
)
from app.services.sync_service import sync_logs


router = APIRouter(
    prefix="/api/sync",
    tags=["Sync"],
)


@router.get("/test")
def test_sync_router() -> dict[str, str]:
    """
    Kiểm tra router đồng bộ có hoạt động hay không.
    """

    return {
        "status": "ok",
        "message": "Sync router is working",
    }


@router.post(
    "/logs",
    response_model=SyncLogsResponse,
)
def sync_cultivation_logs(
    payload: SyncLogsRequest,
    database_session: Session = Depends(get_db),
) -> SyncLogsResponse:
    """
    Nhận các nhật ký được lưu ngoại tuyến từ thiết bị.

    Mỗi bản ghi được xử lý độc lập:

    - Bản ghi hợp lệ được lưu vào PostgreSQL.
    - Bản ghi đã tồn tại trả về already_exists.
    - Bản ghi không hợp lệ trả về failed.
    - Một bản ghi lỗi không làm hỏng toàn bộ lô đồng bộ.
    """

    return sync_logs(
        database_session=database_session,
        payload=payload,
    )
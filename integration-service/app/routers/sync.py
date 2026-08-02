from fastapi import APIRouter

from app.schemas.sync import (
    SyncLogsRequest,
    SyncLogsResponse,
)
from app.services.sync_service import sync_logs


router = APIRouter(
    prefix="/api/sync",
    tags=["Offline Sync"],
)


@router.post(
    "/logs",
    response_model=SyncLogsResponse,
)
def sync_cultivation_logs(
    payload: SyncLogsRequest,
) -> SyncLogsResponse:
    """
    Nhận nhiều nhật ký ngoại tuyến và xử lý từng bản ghi.
    """

    return sync_logs(payload)
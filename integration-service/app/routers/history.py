from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.history import (
    IntegrationHistoryListResponse,
)
from app.services.history_service import get_history


router = APIRouter(
    prefix="/api/history",
    tags=["Integration History"],
)


@router.get(
    "",
    response_model=IntegrationHistoryListResponse,
)
def list_integration_history(
    client_record_id: str | None = None,
    database_session: Session = Depends(get_db),
) -> IntegrationHistoryListResponse:
    """
    Lấy lịch sử xử lý của Integration Service.

    Có thể lọc theo client_record_id.
    """

    records = get_history(
        database_session=database_session,
        client_record_id=client_record_id,
    )

    return IntegrationHistoryListResponse(
        success=True,
        data=records,
    )
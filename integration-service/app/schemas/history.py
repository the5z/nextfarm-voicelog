from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class IntegrationHistoryItem(BaseModel):
    """Một bản ghi lịch sử Integration."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    client_record_id: str | None
    request_payload: dict[str, Any] | None
    response_payload: dict[str, Any] | None
    status: str
    http_status: int | None
    created_at: datetime


class IntegrationHistoryListResponse(BaseModel):
    """Danh sách lịch sử Integration."""

    success: bool
    data: list[IntegrationHistoryItem]
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.schemas.activity import ActivityData


class BotSessionStatus(str, Enum):
    COLLECTING = "collecting"
    COMPLETED = "completed"


class BotSession(BaseModel):
    session_id: str
    status: BotSessionStatus = BotSessionStatus.COLLECTING

    collected_data: ActivityData

    missing_fields: list[str] = []
    warnings: list[str] = []

    requires_confirmation: bool = False

    # Field mà Voice Bot hiện đang chờ người dùng trả lời.
    # Ví dụ:
    # "lot_text"
    # "materials.quantity"
    # "time_text"
    expected_field: Optional[str] = None

    next_question: Optional[str] = None
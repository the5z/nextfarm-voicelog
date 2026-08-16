from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.activity import ActivityData


class BotSessionStatus(str, Enum):
    COLLECTING = "collecting"
    COMPLETED = "completed"


class BotSession(BaseModel):
    session_id: str

    status: BotSessionStatus = BotSessionStatus.COLLECTING

    collected_data: ActivityData

    missing_fields: list[str] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)

    requires_confirmation: bool = False

    next_question: Optional[str] = None
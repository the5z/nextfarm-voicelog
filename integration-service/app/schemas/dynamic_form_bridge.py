from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
)

from app.schemas.dynamic_form import (
    DynamicCreateWorkLogRequest,
)
from app.schemas.nextfarm import (
    NextFarmContext,
)


class DynamicWorkLogSaveRequest(BaseModel):
    """
    Request riêng của Integration để nối
    Dynamic Form V3.1 với cultivation log.

    Không chứa logic AI/extraction.
    """

    dynamic_form: DynamicCreateWorkLogRequest

    client_record_id: str = Field(
        min_length=1,
        max_length=100,
    )

    # Đây phải là datetime canonical.
    # Integration không parse
    # performed_time_text tự do ở đây.
    performed_at: datetime

    # Canonical NextFarm IDs.
    # Không suy ra từ plot_text/season_text.
    context: NextFarmContext | None = None

    confirmed: bool = False
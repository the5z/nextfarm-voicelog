from typing import Optional

from pydantic import BaseModel


class ActivityData(BaseModel):
    activity: str
    animal: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    time: Optional[str] = None
    note: Optional[str] = None
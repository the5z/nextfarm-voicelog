from typing import Any, Optional

from pydantic import BaseModel


class ApiResponse(BaseModel):
    """
    Standard API response format.
    """

    success: bool
    message: str
    data: Optional[Any] = None
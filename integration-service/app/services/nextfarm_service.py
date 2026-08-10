from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.clients.nextfarm_client import NextFarmClient
from app.services.log_service import (
    find_log_by_client_record_id,
    serialize_log,
)
from app.services.nextfarm_mapper import (
    map_cultivation_log_to_nextfarm,
)


class NextFarmLogNotFoundError(LookupError):
    """
    Không tìm thấy nhật ký cần gửi sang NextFarm.
    """


def submit_saved_log_to_nextfarm(
    database_session: Session,
    client_record_id: str,
    *,
    nextfarm_client: NextFarmClient | None = None,
) -> dict[str, Any]:
    """
    Lấy nhật ký đã lưu trong PostgreSQL, chuyển đổi định dạng
    và gửi sang NextFarm.

    nextfarm_client có thể được truyền từ bên ngoài để phục vụ
    kiểm thử. Nếu không truyền, service tự tạo client từ .env.
    """

    normalized_client_record_id = (
        client_record_id.strip()
    )

    if not normalized_client_record_id:
        raise ValueError(
            "client_record_id không được để trống"
        )

    stored_log = find_log_by_client_record_id(
        database_session=database_session,
        client_record_id=normalized_client_record_id,
    )

    if stored_log is None:
        raise NextFarmLogNotFoundError(
            (
                "Không tìm thấy nhật ký có "
                f"client_record_id={normalized_client_record_id}"
            )
        )

    serialized_log = serialize_log(stored_log)

    mapped_payload = (
        map_cultivation_log_to_nextfarm(
            serialized_log
        )
    )

    owns_client = nextfarm_client is None

    client = (
        nextfarm_client
        if nextfarm_client is not None
        else NextFarmClient()
    )

    try:
        nextfarm_response = (
            client.submit_production_diary(
                mapped_payload
            )
        )
    finally:
        if owns_client:
            client.close()

    return {
        "success": bool(
            nextfarm_response.get(
                "success",
                False,
            )
        ),
        "client_record_id": (
            normalized_client_record_id
        ),
        "mode": nextfarm_response.get(
            "mode",
            client.config.mode,
        ),
        "status": str(
            nextfarm_response.get(
                "status",
                "unknown",
            )
        ),
        "status_code": int(
            nextfarm_response.get(
                "status_code",
                0,
            )
        ),
        "mapped_payload": mapped_payload,
        "nextfarm_response": nextfarm_response,
    }
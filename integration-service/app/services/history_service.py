from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.integration_history import (
    IntegrationHistoryModel,
)


def create_history(
    database_session: Session,
    *,
    event_type: str,
    client_record_id: str | None,
    request_payload: dict[str, Any] | None,
    response_payload: dict[str, Any] | None,
    status: str,
    http_status: int | None,
) -> IntegrationHistoryModel:
    """
    Lưu một bản ghi lịch sử Integration.
    """

    history = IntegrationHistoryModel(
        event_type=event_type,
        client_record_id=client_record_id,
        request_payload=request_payload,
        response_payload=response_payload,
        status=status,
        http_status=http_status,
    )

    database_session.add(history)
    database_session.commit()
    database_session.refresh(history)

    return history


def get_history(
    database_session: Session,
    *,
    client_record_id: str | None = None,
) -> list[IntegrationHistoryModel]:
    """
    Lấy lịch sử Integration.

    Có thể lọc theo client_record_id.
    Bản ghi mới nhất được trả về trước.
    """

    statement = select(
        IntegrationHistoryModel
    )

    if client_record_id is not None:
        statement = statement.where(
            IntegrationHistoryModel.client_record_id
            == client_record_id
        )

    statement = statement.order_by(
        IntegrationHistoryModel.id.desc()
    )

    return list(
        database_session.scalars(statement).all()
    )
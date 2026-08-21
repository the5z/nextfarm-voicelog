from fastapi import APIRouter, HTTPException

from app.schemas.activity import ActivityData
from app.schemas.bot_message import BotMessageRequest
from app.schemas.bot_session import BotSession
from app.services.bot_message_service import (
    apply_message_to_activity,
)
from app.services.bot_session_service import (
    create_session,
    get_session,
    update_session,
)


router = APIRouter(
    prefix="/api/v1/bot",
    tags=["Bot"],
)


@router.post(
    "/sessions",
    response_model=BotSession,
)
def create_bot_session(
    activity: ActivityData,
) -> BotSession:
    return create_session(
        activity
    )


@router.get(
    "/sessions/{session_id}",
    response_model=BotSession,
)
def get_bot_session(
    session_id: str,
) -> BotSession:
    session = get_session(
        session_id
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Bot session not found.",
        )

    return session


@router.patch(
    "/sessions/{session_id}",
    response_model=BotSession,
)
def update_bot_session(
    session_id: str,
    activity: ActivityData,
) -> BotSession:
    session = update_session(
        session_id,
        activity,
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Bot session not found.",
        )

    return session


@router.post(
    "/sessions/{session_id}/messages",
    response_model=BotSession,
)
def send_bot_message(
    session_id: str,
    request: BotMessageRequest,
) -> BotSession:
    session = get_session(
        session_id
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Bot session not found.",
        )

    updated_activity = (
        apply_message_to_activity(
            activity=session.collected_data,
            expected_field=session.expected_field,
            message=request.message,
        )
    )

    updated_session = update_session(
        session_id,
        updated_activity,
    )

    if updated_session is None:
        raise HTTPException(
            status_code=404,
            detail="Bot session not found.",
        )

    return updated_session
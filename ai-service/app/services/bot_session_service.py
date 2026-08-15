from uuid import uuid4

from app.schemas.activity import ActivityData
from app.schemas.bot_session import BotSession, BotSessionStatus
from app.services.bot_service import get_next_question


_sessions: dict[str, BotSession] = {}


def create_session(activity: ActivityData) -> BotSession:
    session_id = str(uuid4())

    status = (
        BotSessionStatus.COLLECTING
        if activity.requires_confirmation
        else BotSessionStatus.COMPLETED
    )

    session = BotSession(
        session_id=session_id,
        status=status,
        collected_data=activity,
        missing_fields=list(activity.missing_fields),
        warnings=list(activity.warnings),
        requires_confirmation=activity.requires_confirmation,
        next_question=get_next_question(activity),
    )

    _sessions[session_id] = session

    return session


def get_session(session_id: str) -> BotSession | None:
    return _sessions.get(session_id)


def merge_activity_data(
    current: ActivityData,
    update: ActivityData,
) -> ActivityData:
    activity_text = (
        update.activity_text
        if update.activity_text is not None
        else current.activity_text
    )

    lot_text = (
        update.lot_text
        if update.lot_text is not None
        else current.lot_text
    )

    materials = (
        update.materials
        if update.materials
        else current.materials
    )

    time_text = (
        update.time_text
        if update.time_text is not None
        else current.time_text
    )

    missing_fields = list(update.missing_fields)
    warnings = list(update.warnings)
    requires_confirmation = update.requires_confirmation

    return ActivityData(
        activity_text=activity_text,
        lot_text=lot_text,
        materials=materials,
        time_text=time_text,
        missing_fields=missing_fields,
        warnings=warnings,
        requires_confirmation=requires_confirmation,
    )


def update_session(
    session_id: str,
    activity_update: ActivityData,
) -> BotSession | None:
    session = get_session(session_id)

    if session is None:
        return None

    merged_activity = merge_activity_data(
        session.collected_data,
        activity_update,
    )

    status = (
        BotSessionStatus.COLLECTING
        if merged_activity.requires_confirmation
        else BotSessionStatus.COMPLETED
    )

    updated_session = BotSession(
        session_id=session.session_id,
        status=status,
        collected_data=merged_activity,
        missing_fields=list(merged_activity.missing_fields),
        warnings=list(merged_activity.warnings),
        requires_confirmation=merged_activity.requires_confirmation,
        next_question=get_next_question(merged_activity),
    )

    _sessions[session_id] = updated_session

    return updated_session
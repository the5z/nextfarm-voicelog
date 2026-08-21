from uuid import uuid4

from app.schemas.activity import ActivityData
from app.schemas.bot_session import (
    BotSession,
    BotSessionStatus,
)
from app.services.bot_service import (
    get_expected_field,
    get_next_question,
)
from app.services.confidence_service import (
    apply_confidence_rules,
)


_sessions: dict[str, BotSession] = {}


def build_session(
    session_id: str,
    activity: ActivityData,
) -> BotSession:
    # Mỗi lần build lại session, missing_fields phải được
    # tính lại từ snapshot ActivityData hiện tại.
    #
    # Nếu giữ missing_fields cũ, một field đã được người dùng
    # bổ sung vẫn có thể tiếp tục bị đánh dấu là thiếu.
    #
    # Không reset warnings ở đây vì warning có thể là
    # uncertainty thật do AI phát hiện.
    activity_for_validation = activity.model_copy(
        update={
            "missing_fields": [],
            "requires_confirmation": False,
        }
    )

    validated_activity = apply_confidence_rules(
        activity_for_validation
    )

    status = (
        BotSessionStatus.COLLECTING
        if validated_activity.requires_confirmation
        else BotSessionStatus.COMPLETED
    )

    expected_field = get_expected_field(
        validated_activity
    )

    return BotSession(
        session_id=session_id,
        status=status,
        collected_data=validated_activity,
        missing_fields=list(
            validated_activity.missing_fields
        ),
        warnings=list(
            validated_activity.warnings
        ),
        requires_confirmation=(
            validated_activity.requires_confirmation
        ),
        expected_field=expected_field,
        next_question=get_next_question(
            validated_activity
        ),
    )


def create_session(
    activity: ActivityData,
) -> BotSession:
    session_id = str(
        uuid4()
    )

    session = build_session(
        session_id,
        activity,
    )

    _sessions[
        session_id
    ] = session

    return session


def get_session(
    session_id: str,
) -> BotSession | None:
    return _sessions.get(
        session_id
    )


def update_session(
    session_id: str,
    activity_update: ActivityData,
) -> BotSession | None:
    session = get_session(
        session_id
    )

    if session is None:
        return None

    # Frontend / Bot Message flow gửi snapshot ActivityData
    # hiện tại.
    #
    # Giá trị null hoặc rỗng nghĩa là field hiện đang thiếu,
    # không được kế thừa dữ liệu cũ từ session trước.

    updated_session = build_session(
        session.session_id,
        activity_update,
    )

    _sessions[
        session_id
    ] = updated_session

    return updated_session
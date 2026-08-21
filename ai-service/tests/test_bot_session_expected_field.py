from app.schemas.activity import ActivityData
from app.services.bot_session_service import (
    create_session,
    update_session,
)


def test_create_session_sets_expected_field_for_missing_time():
    activity = ActivityData(
        activity_text="Bón phân",
        lot_text="Lô A",
        materials=[],
        time_text=None,
        missing_fields=[],
        warnings=[],
        requires_confirmation=False,
    )

    session = create_session(activity)

    assert session.status == "collecting"
    assert session.requires_confirmation is True
    assert session.expected_field == "time_text"
    assert "time_text" in session.missing_fields
    assert session.next_question == (
        "Bạn thực hiện hoạt động này lúc mấy giờ?"
    )


def test_update_session_removes_stale_time_and_sets_expected_field():
    initial_activity = ActivityData(
        activity_text="Bón phân",
        lot_text="Lô A",
        materials=[],
        time_text="08:00",
        missing_fields=[],
        warnings=[],
        requires_confirmation=False,
    )

    session = create_session(initial_activity)

    updated_activity = ActivityData(
        activity_text="Bón phân",
        lot_text="Lô A",
        materials=[],
        time_text=None,
        missing_fields=[],
        warnings=[],
        requires_confirmation=False,
    )

    updated_session = update_session(
        session.session_id,
        updated_activity,
    )

    assert updated_session is not None
    assert updated_session.status == "collecting"
    assert updated_session.expected_field == "time_text"
    assert "time_text" in updated_session.missing_fields


def test_update_session_completes_after_missing_time_is_supplied():
    initial_activity = ActivityData(
        activity_text="Bón phân",
        lot_text="Lô A",
        materials=[],
        time_text=None,
        missing_fields=[],
        warnings=[],
        requires_confirmation=False,
    )

    session = create_session(initial_activity)

    completed_activity = ActivityData(
        activity_text="Bón phân",
        lot_text="Lô A",
        materials=[],
        time_text="07:00",
        missing_fields=[],
        warnings=[],
        requires_confirmation=False,
    )

    completed_session = update_session(
        session.session_id,
        completed_activity,
    )

    assert completed_session is not None
    assert completed_session.status == "completed"
    assert completed_session.requires_confirmation is False
    assert completed_session.expected_field is None
    assert completed_session.missing_fields == []
    assert completed_session.next_question is None
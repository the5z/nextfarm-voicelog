from app.schemas.activity import ActivityData


QUESTION_BY_FIELD = {
    "activity_text": (
        "Bạn muốn ghi nhận hoạt động gì?"
    ),
    "lot_text": (
        "Bạn thực hiện hoạt động này ở lô nào?"
    ),
    "materials.material_text": (
        "Bạn đã sử dụng vật tư gì?"
    ),
    "materials.quantity": (
        "Bạn đã sử dụng số lượng bao nhiêu?"
    ),
    "materials.unit_text": (
        "Đơn vị của số lượng vật tư là gì?"
    ),
    "time_text": (
        "Bạn thực hiện hoạt động này lúc mấy giờ?"
    ),
}


def get_expected_field(
    activity: ActivityData,
) -> str | None:
    """
    Trả về field tiếp theo mà Voice Bot
    đang chờ người dùng bổ sung.
    """

    if not activity.requires_confirmation:
        return None

    for field in activity.missing_fields:
        if field in QUESTION_BY_FIELD:
            return field

    return None


def get_next_question(
    activity: ActivityData,
) -> str | None:
    """
    Sinh câu hỏi tiếp theo dựa trên
    field còn thiếu hoặc warning.
    """

    if not activity.requires_confirmation:
        return None

    expected_field = get_expected_field(
        activity
    )

    if expected_field is not None:
        return QUESTION_BY_FIELD[
            expected_field
        ]

    if activity.warnings:
        return (
            "Có thông tin chưa chắc chắn. "
            "Bạn vui lòng kiểm tra và xác nhận lại."
        )

    return (
        "Bạn vui lòng bổ sung hoặc xác nhận "
        "thông tin còn thiếu."
    )
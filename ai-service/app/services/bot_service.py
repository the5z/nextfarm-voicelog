from app.schemas.activity import ActivityData


QUESTION_BY_FIELD = {
    "activity_text": "Bạn đã thực hiện hoạt động gì?",
    "lot_text": "Bạn thực hiện ở lô nào?",
    "materials.material_text": "Bạn đã sử dụng vật tư gì?",
    "materials.quantity": "Bạn đã sử dụng số lượng bao nhiêu?",
    "materials.unit_text": "Đơn vị của số lượng vật tư là gì?",
    "time_text": "Bạn thực hiện hoạt động này lúc mấy giờ?",
}


def get_next_question(activity: ActivityData) -> str | None:
    if not activity.requires_confirmation:
        return None

    for field in activity.missing_fields:
        question = QUESTION_BY_FIELD.get(field)

        if question:
            return question

    if activity.warnings:
        return "Bạn có thể xác nhận lại thông tin vừa cung cấp không?"

    return "Bạn có thể bổ sung hoặc xác nhận lại thông tin còn thiếu không?"
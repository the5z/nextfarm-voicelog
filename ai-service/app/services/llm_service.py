from app.schemas.activity import ActivityData


def extract_activity(transcript: str) -> ActivityData:
    """
    Mock version.
    Sau này sẽ thay bằng lời gọi tới LLM.
    """

    return ActivityData(
        activity="feeding",
        animal="cow",
        quantity=20,
        unit="kg",
        time="07:00",
        note=transcript,
    )
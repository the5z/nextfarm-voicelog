from app.schemas.cultivation_log import CultivationLogInput


_logs: dict[str, dict] = {}


def create_log(
    payload: CultivationLogInput,
) -> tuple[dict, bool]:
    existing = _logs.get(payload.client_record_id)

    if existing is not None:
        return existing, False

    record = {
        "id": len(_logs) + 1,
        **payload.model_dump(mode="json"),
        "status": "saved",
    }

    _logs[payload.client_record_id] = record

    return record, True


def get_all_logs() -> list[dict]:
    return list(_logs.values())


def clear_logs() -> None:
    """Xóa dữ liệu tạm để các bài test độc lập với nhau."""
    _logs.clear()
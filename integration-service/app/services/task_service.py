from __future__ import annotations

from typing import Any, Literal

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.task import TaskModel
from app.schemas.task import (
    TaskCreateRequest,
    TaskInput,
)
from app.services.season_master_data_service import (
    resolve_season_text,
)
from sqlalchemy.orm import Session

TaskValidationCode = Literal[
    "UNKNOWN_SEASON",
]


class TaskValidationError(ValueError):
    def __init__(
        self,
        *,
        field: str,
        code: TaskValidationCode,
        message: str,
    ) -> None:
        super().__init__(message)

        self.field = field
        self.code = code
        self.message = message


def build_task_input(
    request: TaskCreateRequest,
    database_session: Session | None = None,
) -> TaskInput:
    """
    Chuyển dữ liệu CREATE_TASK đã xác nhận
    sang canonical TaskInput.

    season_text được resolve -> season_id.

    task_type_text, due_time_text và assignee_text
    chưa có canonical source nên Integration
    không tự suy diễn hoặc sinh mã.
    """

    season_result = resolve_season_text(
        request.season_text,
        database_session,
    )

    season_id = season_result.season_id

    if (
        not season_result.matched
        or not season_id
    ):
        raise TaskValidationError(
            field="season_text",
            code="UNKNOWN_SEASON",
            message=(
                "Không thể ánh xạ "
                f"'{request.season_text}' "
                "sang season_id chuẩn."
            ),
        )

    return TaskInput(
        client_record_id=(
            request.client_record_id
        ),
        season_id=season_id,
        task_name=request.task_name,
        task_type_text=(
            request.task_type_text
        ),
        due_time_text=(
            request.due_time_text
        ),
        assignee_text=(
            request.assignee_text
        ),
        photo_required=(
            request.photo_required
        ),
        note=request.note,
        confirmed=request.confirmed,
    )


def serialize_task(
    task: TaskModel,
) -> dict[str, Any]:
    return {
        "id": task.id,
        "client_record_id": (
            task.client_record_id
        ),
        "season_id": task.season_id,
        "task_name": task.task_name,
        "task_type_text": (
            task.task_type_text
        ),
        "due_time_text": (
            task.due_time_text
        ),
        "assignee_text": (
            task.assignee_text
        ),
        "photo_required": (
            task.photo_required
        ),
        "note": task.note,
        "confirmed": task.confirmed,
        "status": task.status,
        "created_at": (
            task.created_at.isoformat()
            if task.created_at is not None
            else None
        ),
    }


def find_task_by_client_record_id(
    database_session: Session,
    client_record_id: str,
) -> TaskModel | None:
    statement = (
        select(TaskModel)
        .where(
            TaskModel.client_record_id
            == client_record_id
        )
    )

    return database_session.scalar(
        statement
    )


def create_task(
    database_session: Session,
    payload: TaskInput,
) -> tuple[dict[str, Any], bool]:
    existing = (
        find_task_by_client_record_id(
            database_session,
            payload.client_record_id,
        )
    )

    if existing is not None:
        return (
            serialize_task(existing),
            False,
        )

    task = TaskModel(
        client_record_id=(
            payload.client_record_id
        ),
        season_id=payload.season_id,
        task_name=payload.task_name,
        task_type_text=(
            payload.task_type_text
        ),
        due_time_text=(
            payload.due_time_text
        ),
        assignee_text=(
            payload.assignee_text
        ),
        photo_required=(
            payload.photo_required
        ),
        note=payload.note,
        confirmed=payload.confirmed,
        status="saved",
    )

    database_session.add(task)

    try:
        database_session.commit()

    except IntegrityError:
        database_session.rollback()

        existing = (
            find_task_by_client_record_id(
                database_session,
                payload.client_record_id,
            )
        )

        if existing is not None:
            return (
                serialize_task(existing),
                False,
            )

        raise

    database_session.refresh(task)

    return (
        serialize_task(task),
        True,
    )


def update_task(
    database_session: Session,
    client_record_id: str,
    payload: TaskInput,
) -> dict[str, Any] | None:
    task = find_task_by_client_record_id(
        database_session,
        client_record_id,
    )

    if task is None:
        return None

    task.season_id = payload.season_id
    task.task_name = payload.task_name
    task.task_type_text = (
        payload.task_type_text
    )
    task.due_time_text = (
        payload.due_time_text
    )
    task.assignee_text = (
        payload.assignee_text
    )
    task.photo_required = (
        payload.photo_required
    )
    task.note = payload.note
    task.confirmed = payload.confirmed
    task.status = "saved"

    try:
        database_session.commit()

    except Exception:
        database_session.rollback()
        raise

    database_session.refresh(task)

    return serialize_task(task)


def get_task_by_client_record_id(
    database_session: Session,
    client_record_id: str,
) -> dict[str, Any] | None:
    task = find_task_by_client_record_id(
        database_session,
        client_record_id,
    )

    if task is None:
        return None

    return serialize_task(task)


def get_all_tasks(
    database_session: Session,
) -> list[dict[str, Any]]:
    statement = (
        select(TaskModel)
        .order_by(
            TaskModel.id.desc()
        )
    )

    tasks = (
        database_session
        .scalars(statement)
        .all()
    )

    return [
        serialize_task(task)
        for task in tasks
    ]


def clear_tasks(
    database_session: Session,
) -> None:
    """
    Chỉ dùng cleanup database kiểm thử.
    Không expose public endpoint.
    """

    database_session.execute(
        delete(TaskModel)
    )

    database_session.commit()
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.cultivation_log import (
    CultivationLogMaterialModel,
    CultivationLogModel,
)
from app.schemas.cultivation_log import CultivationLogInput


def decimal_to_number(value: Decimal) -> int | float:
    """
    Chuyển Decimal từ PostgreSQL thành kiểu số có thể trả về JSON.

    Ví dụ:
        Decimal("20.000") -> 20
        Decimal("20.500") -> 20.5
    """

    if value == value.to_integral_value():
        return int(value)

    return float(value)


def serialize_log(
    log: CultivationLogModel,
) -> dict[str, Any]:
    """
    Chuyển SQLAlchemy model thành dictionary để trả về API.
    """

    return {
        "id": log.id,
        "schema_version": log.schema_version,
        "client_record_id": log.client_record_id,
        "transcript": log.transcript,
        "context": {
            "tenant_id": log.tenant_id,
            "user_id": log.user_id,
            "season_id": log.season_id,
            "plot_id": log.plot_id,
            "task_id": log.task_id,
        }
        if all(
            value is not None
            for value in (
                log.tenant_id,
                log.user_id,
                log.season_id,
                log.plot_id,
                log.task_id,
            )
        )
        else None,
        "lot_code": log.lot_code,
        "activity_code": log.activity_code,
        "materials": [
            {
                "material_code": material.material_code,
                "quantity": decimal_to_number(
                    material.quantity
                ),
                "unit_code": material.unit_code,
            }
            for material in log.materials
        ],
        "performed_at": log.performed_at.isoformat(),
        "performer_code": log.performer_code,
        "notes": log.notes,
        "source": log.source,
        "confirmed": log.confirmed,
        "status": log.status,
        "created_at": (
            log.created_at.isoformat()
            if log.created_at is not None
            else None
        ),
    }


def find_log_by_client_record_id(
    database_session: Session,
    client_record_id: str,
) -> CultivationLogModel | None:
    """
    Tìm một nhật ký dựa trên client_record_id.

    client_record_id được dùng để chống lưu trùng khi thiết bị
    gửi lại cùng một bản ghi.
    """

    statement = (
        select(CultivationLogModel)
        .options(
            selectinload(
                CultivationLogModel.materials
            )
        )
        .where(
            CultivationLogModel.client_record_id
            == client_record_id
        )
    )

    return database_session.scalar(statement)


def create_log(
    database_session: Session,
    payload: CultivationLogInput,
) -> tuple[dict[str, Any], bool]:
    """
    Lưu một nhật ký vào PostgreSQL.

    Giá trị trả về:
        record: dữ liệu nhật ký
        created:
            True  -> vừa lưu mới
            False -> nhật ký đã tồn tại
    """

    existing_log = find_log_by_client_record_id(
        database_session=database_session,
        client_record_id=payload.client_record_id,
    )

    if existing_log is not None:
        return serialize_log(existing_log), False

    new_log = CultivationLogModel(
        schema_version=payload.schema_version,
        client_record_id=payload.client_record_id,
        transcript=payload.transcript,
        tenant_id=(
            payload.context.tenant_id
            if payload.context is not None
            else None
        ),
        user_id=(
            payload.context.user_id
            if payload.context is not None
            else None
        ),
        season_id=(
            payload.context.season_id
            if payload.context is not None
            else None
        ),
        plot_id=(
            payload.context.plot_id
            if payload.context is not None
            else None
        ),
        task_id=(
            payload.context.task_id
            if payload.context is not None
            else None
        ),
        lot_code=payload.lot_code,
        activity_code=payload.activity_code,
        performed_at=payload.performed_at,
        performer_code=payload.performer_code,
        notes=payload.notes,
        source=payload.source,
        confirmed=payload.confirmed,
        status="saved",
    )

    new_log.materials = [
        CultivationLogMaterialModel(
            material_code=material.material_code,
            quantity=material.quantity,
            unit_code=material.unit_code,
        )
        for material in payload.materials
    ]

    database_session.add(new_log)

    try:
        database_session.commit()

    except IntegrityError:
        database_session.rollback()

        # Trường hợp hai request cùng lúc gửi một client_record_id.
        existing_log = find_log_by_client_record_id(
            database_session=database_session,
            client_record_id=payload.client_record_id,
        )

        if existing_log is not None:
            return serialize_log(existing_log), False

        raise

    database_session.refresh(new_log)

    return serialize_log(new_log), True

def update_log(
    database_session: Session,
    client_record_id: str,
    payload: CultivationLogInput,
) -> dict[str, Any] | None:
    """
    Cập nhật một cultivation log đã tồn tại.

    PUT semantics:
    - client_record_id không thay đổi
    - cập nhật toàn bộ parent fields
    - thay toàn bộ materials[] bằng payload mới
    - commit trong cùng transaction

    Trả về None nếu không tìm thấy record.
    """

    existing_log = (
        find_log_by_client_record_id(
            database_session=database_session,
            client_record_id=client_record_id,
        )
    )

    if existing_log is None:
        return None

    # =========================================================
    # UPDATE PARENT
    # =========================================================

    existing_log.schema_version = (
        payload.schema_version
    )

    existing_log.transcript = (
        payload.transcript
    )

    existing_log.tenant_id = (
        payload.context.tenant_id
        if payload.context is not None
        else None
    )
    existing_log.user_id = (
        payload.context.user_id
        if payload.context is not None
        else None
    )
    existing_log.season_id = (
        payload.context.season_id
        if payload.context is not None
        else None
    )
    existing_log.plot_id = (
        payload.context.plot_id
        if payload.context is not None
        else None
    )
    existing_log.task_id = (
        payload.context.task_id
        if payload.context is not None
        else None
    )

    existing_log.lot_code = (
        payload.lot_code
    )

    existing_log.activity_code = (
        payload.activity_code
    )

    existing_log.performed_at = (
        payload.performed_at
    )

    existing_log.performer_code = (
        payload.performer_code
    )

    existing_log.notes = (
        payload.notes
    )

    existing_log.source = (
        payload.source
    )

    existing_log.confirmed = (
        payload.confirmed
    )

    existing_log.status = "saved"

    # =========================================================
    # REPLACE MATERIALS
    # =========================================================
    #
    # Không sửa riêng material đầu tiên.
    # PUT gửi full materials[] nên backend thay toàn bộ child rows.
    #

    database_session.execute(
        delete(
            CultivationLogMaterialModel
        ).where(
            CultivationLogMaterialModel.log_id
            == existing_log.id
        )
    )

    database_session.flush()

    new_materials = [
        CultivationLogMaterialModel(
            log_id=existing_log.id,
            material_code=(
                material.material_code
            ),
            quantity=(
                material.quantity
            ),
            unit_code=(
                material.unit_code
            ),
        )
        for material in payload.materials
    ]

    database_session.add_all(
        new_materials
    )

    try:
        database_session.commit()

    except Exception:
        database_session.rollback()
        raise

    # =========================================================
    # RELOAD UPDATED RECORD
    # =========================================================
    #
    # existing_log đã load materials[] trước đó.
    # Vì phía trên dùng bulk DELETE + INSERT nên relationship
    # materials có thể vẫn giữ collection cũ trong SQLAlchemy
    # Session.
    #
    # populate_existing=True buộc SQLAlchemy ghi đè lại
    # object/relationship bằng dữ liệu mới nhất từ database.
    #

    statement = (
        select(CultivationLogModel)
        .options(
            selectinload(
                CultivationLogModel.materials
            )
        )
        .where(
            CultivationLogModel.client_record_id
            == client_record_id
        )
        .execution_options(
            populate_existing=True
        )
    )

    updated_log = database_session.scalar(
        statement
    )

    if updated_log is None:
        return None

    return serialize_log(
        updated_log
    )

def get_all_logs(
    database_session: Session,
) -> list[dict[str, Any]]:
    """
    Lấy toàn bộ nhật ký đã lưu trong PostgreSQL.

    Nhật ký mới nhất được trả về trước.
    """

    statement = (
        select(CultivationLogModel)
        .options(
            selectinload(
                CultivationLogModel.materials
            )
        )
        .order_by(
            CultivationLogModel.id.desc()
        )
    )

    logs = database_session.scalars(statement).all()

    return [
        serialize_log(log)
        for log in logs
    ]


def clear_logs(
    database_session: Session,
) -> None:
    """
    Xóa dữ liệu nhật ký.

    Hàm này chủ yếu dùng trong môi trường kiểm thử.
    Không tạo endpoint công khai gọi hàm này.
    """

    database_session.execute(
        delete(CultivationLogMaterialModel)
    )

    database_session.execute(
        delete(CultivationLogModel)
    )

    database_session.commit()

def get_log_by_client_record_id(
    database_session: Session,
    client_record_id: str,
) -> dict[str, Any] | None:
    """
    Lấy chi tiết một nhật ký theo client_record_id.

    Trả về None nếu không tìm thấy nhật ký.
    """

    log = find_log_by_client_record_id(
        database_session=database_session,
        client_record_id=client_record_id,
    )

    if log is None:
        return None

    return serialize_log(log)
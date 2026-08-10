from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.schemas.cultivation_log import CultivationLogInput
from app.schemas.sync import SyncLogsRequest, SyncLogsResponse
from app.services.log_service import create_log


def get_client_record_id(
    raw_record: dict[str, Any],
    record_index: int,
) -> str:
    """
    Lấy client_record_id từ bản ghi thô.

    Nếu bản ghi không có client_record_id thì tạo mã tạm
    để frontend vẫn xác định được bản ghi nào bị lỗi.
    """

    client_record_id = raw_record.get("client_record_id")

    if isinstance(client_record_id, str):
        client_record_id = client_record_id.strip()

        if client_record_id:
            return client_record_id

    return f"unknown-record-{record_index + 1}"


def convert_validation_errors(
    validation_error: ValidationError,
) -> list[dict[str, str]]:
    """
    Chuyển lỗi Pydantic thành cấu trúc lỗi thống nhất
    để trả về cho frontend.
    """

    issues: list[dict[str, str]] = []

    for error in validation_error.errors():
        location = error.get("loc", ())

        field = ".".join(
            str(location_item)
            for location_item in location
        )

        if not field:
            field = "record"

        error_type = str(
            error.get(
                "type",
                "validation_error",
            )
        )

        message = str(
            error.get(
                "msg",
                "Dữ liệu không hợp lệ",
            )
        )

        issues.append(
            {
                "field": field,
                "code": error_type.upper(),
                "message": message,
            }
        )

    return issues


def build_failed_result(
    client_record_id: str,
    errors: list[dict[str, str]],
) -> dict[str, Any]:
    """
    Tạo kết quả cho một bản ghi đồng bộ thất bại.
    """

    return {
        "client_record_id": client_record_id,
        "success": False,
        "status": "failed",
        "data": None,
        "errors": errors,
    }


def build_success_result(
    client_record_id: str,
    record: dict[str, Any],
    created: bool,
) -> dict[str, Any]:
    """
    Tạo kết quả cho một bản ghi đồng bộ thành công.

    created=True:
        Bản ghi vừa được lưu mới.

    created=False:
        Bản ghi đã tồn tại từ trước.
    """

    sync_status = (
        "saved"
        if created
        else "already_exists"
    )

    return {
        "client_record_id": client_record_id,
        "success": True,
        "status": sync_status,
        "data": record,
        "errors": [],
    }


def sync_logs(
    database_session: Session,
    payload: SyncLogsRequest,
) -> SyncLogsResponse:
    """
    Đồng bộ nhiều nhật ký từ thiết bị lên PostgreSQL.

    Mỗi bản ghi được xử lý độc lập:

    - Bản ghi hợp lệ và đã xác nhận sẽ được lưu.
    - Bản ghi đã tồn tại sẽ trả về already_exists.
    - Bản ghi lỗi sẽ trả về failed.
    - Một bản ghi lỗi không làm hỏng toàn bộ lô đồng bộ.
    """

    results: list[dict[str, Any]] = []

    saved_count = 0
    duplicated_count = 0
    failed_count = 0

    for record_index, raw_record in enumerate(
        payload.records
    ):
        if not isinstance(raw_record, dict):
            client_record_id = (
                f"unknown-record-{record_index + 1}"
            )

            results.append(
                build_failed_result(
                    client_record_id=client_record_id,
                    errors=[
                        {
                            "field": "record",
                            "code": "INVALID_RECORD_TYPE",
                            "message": (
                                "Mỗi bản ghi đồng bộ phải "
                                "là một JSON object"
                            ),
                        }
                    ],
                )
            )

            failed_count += 1
            continue

        client_record_id = get_client_record_id(
            raw_record=raw_record,
            record_index=record_index,
        )

        try:
            validated_record = (
                CultivationLogInput.model_validate(
                    raw_record
                )
            )

        except ValidationError as validation_error:
            results.append(
                build_failed_result(
                    client_record_id=client_record_id,
                    errors=convert_validation_errors(
                        validation_error
                    ),
                )
            )

            failed_count += 1
            continue

        if not validated_record.confirmed:
            results.append(
                build_failed_result(
                    client_record_id=client_record_id,
                    errors=[
                        {
                            "field": "confirmed",
                            "code": "UNCONFIRMED_RECORD",
                            "message": (
                                "Nhật ký chưa được người "
                                "dùng xác nhận"
                            ),
                        }
                    ],
                )
            )

            failed_count += 1
            continue

        try:
            stored_record, created = create_log(
                database_session=database_session,
                payload=validated_record,
            )

        except SQLAlchemyError:
            database_session.rollback()

            results.append(
                build_failed_result(
                    client_record_id=client_record_id,
                    errors=[
                        {
                            "field": "database",
                            "code": "DATABASE_ERROR",
                            "message": (
                                "Không thể lưu bản ghi "
                                "vào cơ sở dữ liệu"
                            ),
                        }
                    ],
                )
            )

            failed_count += 1
            continue

        results.append(
            build_success_result(
                client_record_id=client_record_id,
                record=stored_record,
                created=created,
            )
        )

        if created:
            saved_count += 1
        else:
            duplicated_count += 1

    total_records = len(payload.records)

    return SyncLogsResponse(
        success=failed_count == 0,
        device_id=payload.device_id,
        synced_at=payload.synced_at,
        summary={
            "total": total_records,
            "saved": saved_count,
            "duplicated": duplicated_count,
            "failed": failed_count,
        },
        results=results,
    )
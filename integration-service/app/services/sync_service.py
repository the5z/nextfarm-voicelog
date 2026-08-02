from typing import Any

from pydantic import ValidationError

from app.schemas.cultivation_log import CultivationLogInput
from app.schemas.responses import IssueItem
from app.schemas.sync import (
    SyncLogsRequest,
    SyncLogsResponse,
    SyncRecordResult,
    SyncSummary,
)
from app.services.log_service import create_log


def convert_validation_errors(
    error: ValidationError,
) -> list[IssueItem]:
    """
    Chuyển lỗi Pydantic thành định dạng lỗi chung của hệ thống.
    """

    issues: list[IssueItem] = []

    for item in error.errors():
        location = item.get("loc", ())
        field = ".".join(str(part) for part in location)

        issues.append(
            IssueItem(
                field=field or "record",
                code=str(
                    item.get("type", "INVALID_DATA")
                ).upper(),
                message=str(
                    item.get(
                        "msg",
                        "Dữ liệu không hợp lệ",
                    )
                ),
            )
        )

    return issues


def get_client_record_id(
    raw_record: dict[str, Any],
) -> str | None:
    """
    Đọc client_record_id an toàn từ dữ liệu thô.
    """

    value = raw_record.get("client_record_id")

    if value is None:
        return None

    return str(value)


def sync_logs(
    payload: SyncLogsRequest,
) -> SyncLogsResponse:
    """
    Đồng bộ từng nhật ký độc lập.

    Quy tắc:
    - Dữ liệu không hợp lệ: failed.
    - Chưa xác nhận: failed.
    - client_record_id đã có: already_exists.
    - Hợp lệ và chưa tồn tại: saved.
    """

    results: list[SyncRecordResult] = []

    saved_count = 0
    duplicated_count = 0
    failed_count = 0

    for raw_record in payload.records:
        raw_record_id = get_client_record_id(raw_record)

        # Kiểm tra schema riêng cho từng bản ghi.
        try:
            validated_record = (
                CultivationLogInput.model_validate(raw_record)
            )
        except ValidationError as error:
            failed_count += 1

            results.append(
                SyncRecordResult(
                    client_record_id=raw_record_id,
                    status="failed",
                    log_id=None,
                    errors=convert_validation_errors(error),
                )
            )

            continue

        # Chưa xác nhận thì không được lưu.
        if not validated_record.confirmed:
            failed_count += 1

            results.append(
                SyncRecordResult(
                    client_record_id=(
                        validated_record.client_record_id
                    ),
                    status="failed",
                    log_id=None,
                    errors=[
                        IssueItem(
                            field="confirmed",
                            code="UNCONFIRMED_RECORD",
                            message=(
                                "Nhật ký chưa được người dùng "
                                "xác nhận"
                            ),
                        )
                    ],
                )
            )

            continue

        # Dùng chung logic chống trùng hiện tại.
        stored_record, created = create_log(
            validated_record
        )

        if created:
            saved_count += 1

            results.append(
                SyncRecordResult(
                    client_record_id=(
                        validated_record.client_record_id
                    ),
                    status="saved",
                    log_id=stored_record["id"],
                    errors=[],
                )
            )
        else:
            duplicated_count += 1

            results.append(
                SyncRecordResult(
                    client_record_id=(
                        validated_record.client_record_id
                    ),
                    status="already_exists",
                    log_id=stored_record["id"],
                    errors=[],
                )
            )

    total = len(payload.records)

    return SyncLogsResponse(
        # false khi có ít nhất một bản ghi thất bại.
        success=failed_count == 0,
        device_id=payload.device_id,
        summary=SyncSummary(
            total=total,
            saved=saved_count,
            duplicated=duplicated_count,
            failed=failed_count,
        ),
        results=results,
    )
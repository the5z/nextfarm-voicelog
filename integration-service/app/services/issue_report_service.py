from __future__ import annotations

from typing import Any, Literal

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.issue_report import (
    IssueReportModel,
)
from app.schemas.issue_report import (
    IssueReportCreateRequest,
    IssueReportInput,
)
from app.services.normalization_service import (
    resolve_master_data,
)


IssueReportValidationCode = Literal[
    "UNKNOWN_PLOT",
    "INVALID_ISSUE_TYPE",
    "INVALID_SEVERITY",
]


ALLOWED_ISSUE_TYPES = {
    "Sâu",
    "Bệnh",
    "Thời tiết",
    "Tưới tiêu",
    "Khác",
}


ALLOWED_SEVERITIES = {
    "Thấp",
    "Vừa",
    "Cao",
    "Nguy cấp",
}


class IssueReportValidationError(
    ValueError
):
    """
    Lỗi khi structured data của
    CREATE_ISSUE_REPORT không thể
    chuyển thành canonical data.
    """

    def __init__(
        self,
        *,
        field: str,
        code: IssueReportValidationCode,
        message: str,
    ) -> None:
        super().__init__(message)

        self.field = field
        self.code = code
        self.message = message


def resolve_plot_code(
    plot_text: str,
) -> str:
    """
    Chuyển plot_text thành canonical
    plot/lot code bằng master data hiện có.

    Không suy diễn.
    Không fallback sang giá trị khác.
    """

    normalized_text = (
        str(plot_text or "")
        .strip()
    )

    result = resolve_master_data(
        "lot",
        normalized_text,
    )

    matched = bool(
        result.get("matched")
    )

    canonical_code = result.get(
        "code"
    )

    if (
        not matched
        or not canonical_code
    ):
        raise IssueReportValidationError(
            field="plot_text",
            code="UNKNOWN_PLOT",
            message=(
                f"Không thể ánh xạ "
                f"'{normalized_text}' "
                "sang mã lô/khu vực chuẩn."
            ),
        )

    return (
        str(canonical_code)
        .strip()
        .upper()
    )


def build_issue_report_input(
    request: IssueReportCreateRequest,
) -> IssueReportInput:
    """
    Chuyển structured CREATE_ISSUE_REPORT
    thành canonical IssueReportInput.

    Không:
    - đọc transcript
    - NLP
    - AI confidence
    - tự sinh description
    """

    issue_type = (
        request.issue_type_text.strip()
    )

    if issue_type not in ALLOWED_ISSUE_TYPES:
        raise IssueReportValidationError(
            field="issue_type_text",
            code="INVALID_ISSUE_TYPE",
            message=(
                "issue_type_text chỉ được là: "
                "Sâu, Bệnh, Thời tiết, "
                "Tưới tiêu hoặc Khác."
            ),
        )

    severity = (
        request.severity_text.strip()
    )

    if severity not in ALLOWED_SEVERITIES:
        raise IssueReportValidationError(
            field="severity_text",
            code="INVALID_SEVERITY",
            message=(
                "severity_text chỉ được là: "
                "Thấp, Vừa, Cao hoặc Nguy cấp."
            ),
        )

    plot_code = resolve_plot_code(
        request.plot_text
    )

    return IssueReportInput(
        client_record_id=(
            request.client_record_id
        ),
        plot_code=plot_code,
        issue_type=issue_type,
        severity=severity,
        description=request.description,
        photo=request.photo,
        note=request.note,
        confirmed=request.confirmed,
    )


def serialize_issue_report(
    report: IssueReportModel,
) -> dict[str, Any]:
    return {
        "id": report.id,
        "client_record_id": (
            report.client_record_id
        ),
        "plot_code": report.plot_code,
        "issue_type": report.issue_type,
        "severity": report.severity,
        "description": report.description,
        "photo": report.photo,
        "note": report.note,
        "confirmed": report.confirmed,
        "status": report.status,
        "created_at": (
            report.created_at.isoformat()
            if report.created_at is not None
            else None
        ),
    }


def find_issue_report_by_client_record_id(
    database_session: Session,
    client_record_id: str,
) -> IssueReportModel | None:
    statement = (
        select(IssueReportModel)
        .where(
            IssueReportModel.client_record_id
            == client_record_id
        )
    )

    return database_session.scalar(
        statement
    )


def create_issue_report(
    database_session: Session,
    payload: IssueReportInput,
) -> tuple[dict[str, Any], bool]:
    """
    Tạo issue report mới.

    client_record_id bảo đảm
    idempotency khi request được gửi lại.
    """

    existing_report = (
        find_issue_report_by_client_record_id(
            database_session=database_session,
            client_record_id=(
                payload.client_record_id
            ),
        )
    )

    if existing_report is not None:
        return (
            serialize_issue_report(
                existing_report
            ),
            False,
        )

    report = IssueReportModel(
        client_record_id=(
            payload.client_record_id
        ),
        plot_code=payload.plot_code,
        issue_type=payload.issue_type,
        severity=payload.severity,
        description=payload.description,
        photo=payload.photo,
        note=payload.note,
        confirmed=payload.confirmed,
        status="saved",
    )

    database_session.add(report)

    try:
        database_session.commit()

    except IntegrityError:
        database_session.rollback()

        existing_report = (
            find_issue_report_by_client_record_id(
                database_session=(
                    database_session
                ),
                client_record_id=(
                    payload.client_record_id
                ),
            )
        )

        if existing_report is not None:
            return (
                serialize_issue_report(
                    existing_report
                ),
                False,
            )

        raise

    database_session.refresh(report)

    return (
        serialize_issue_report(report),
        True,
    )


def update_issue_report(
    database_session: Session,
    client_record_id: str,
    payload: IssueReportInput,
) -> dict[str, Any] | None:
    report = (
        find_issue_report_by_client_record_id(
            database_session=database_session,
            client_record_id=client_record_id,
        )
    )

    if report is None:
        return None

    report.plot_code = payload.plot_code
    report.issue_type = payload.issue_type
    report.severity = payload.severity
    report.description = payload.description
    report.photo = payload.photo
    report.note = payload.note
    report.confirmed = payload.confirmed
    report.status = "saved"

    try:
        database_session.commit()

    except Exception:
        database_session.rollback()
        raise

    database_session.refresh(report)

    return serialize_issue_report(
        report
    )


def get_issue_report_by_client_record_id(
    database_session: Session,
    client_record_id: str,
) -> dict[str, Any] | None:
    report = (
        find_issue_report_by_client_record_id(
            database_session=database_session,
            client_record_id=client_record_id,
        )
    )

    if report is None:
        return None

    return serialize_issue_report(
        report
    )


def get_all_issue_reports(
    database_session: Session,
) -> list[dict[str, Any]]:
    statement = (
        select(IssueReportModel)
        .order_by(
            IssueReportModel.id.desc()
        )
    )

    reports = (
        database_session
        .scalars(statement)
        .all()
    )

    return [
        serialize_issue_report(report)
        for report in reports
    ]


def clear_issue_reports(
    database_session: Session,
) -> None:
    """
    Cleanup dùng cho test database.
    Không expose thành public endpoint.
    """

    database_session.execute(
        delete(IssueReportModel)
    )

    database_session.commit()
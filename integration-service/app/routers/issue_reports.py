from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.issue_report import (
    IssueReportCreateRequest,
    IssueReportGetResponse,
    IssueReportListResponse,
    IssueReportSaveResponse,
)
from app.services.history_service import (
    create_history,
)
from app.services.issue_report_service import (
    IssueReportValidationError,
    build_issue_report_input,
    create_issue_report,
    get_all_issue_reports,
    get_issue_report_by_client_record_id,
    update_issue_report,
)


router = APIRouter(
    prefix="/api/issue-reports",
    tags=["Issue Reports"],
)


@router.get("/test")
def test_issue_reports_router() -> dict[str, str]:
    return {
        "status": "ok",
        "message": (
            "Issue reports router "
            "is working"
        ),
    }


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=IssueReportSaveResponse,
)
def save_issue_report(
    payload: IssueReportCreateRequest,

    database_session: Session = Depends(
        get_db
    ),
) -> IssueReportSaveResponse:
    request_payload = (
        payload.model_dump(
            mode="json"
        )
    )

    if not payload.confirmed:
        error_detail = {
            "code":
                "UNCONFIRMED_RECORD",
            "message": (
                "Báo cáo sự cố chưa được "
                "người dùng xác nhận."
            ),
        }

        create_history(
            database_session=database_session,
            event_type="save_issue_report",
            client_record_id=(
                payload.client_record_id
            ),
            request_payload=request_payload,
            response_payload={
                "detail": error_detail,
            },
            status="failed",
            http_status=(
                status.HTTP_400_BAD_REQUEST
            ),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=error_detail,
        )

    try:
        canonical_payload = (
            build_issue_report_input(
                payload,
                database_session,
            )
        )

    except IssueReportValidationError as error:
        error_detail = {
            "code":
                "ISSUE_REPORT_VALIDATION_FAILED",
            "field":
                error.field,
            "reason_code":
                error.code,
            "message":
                error.message,
        }

        create_history(
            database_session=database_session,
            event_type="save_issue_report",
            client_record_id=(
                payload.client_record_id
            ),
            request_payload=request_payload,
            response_payload={
                "detail": error_detail,
            },
            status="failed",
            http_status=(
                status.HTTP_400_BAD_REQUEST
            ),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=error_detail,
        ) from error

    record, created = (
        create_issue_report(
            database_session=(
                database_session
            ),
            payload=canonical_payload,
        )
    )

    response = IssueReportSaveResponse(
        success=True,
        status=(
            "saved"
            if created
            else "already_exists"
        ),
        data=record,
    )

    create_history(
        database_session=database_session,
        event_type="save_issue_report",
        client_record_id=(
            payload.client_record_id
        ),
        request_payload=request_payload,
        response_payload=(
            response.model_dump(
                mode="json"
            )
        ),
        status="success",
        http_status=(
            status.HTTP_201_CREATED
        ),
    )

    return response


@router.put(
    "/{client_record_id}",
    response_model=IssueReportSaveResponse,
)
def update_saved_issue_report(
    client_record_id: str,
    payload: IssueReportCreateRequest,

    database_session: Session = Depends(
        get_db
    ),
) -> IssueReportSaveResponse:
    request_payload = (
        payload.model_dump(
            mode="json"
        )
    )

    if (
        client_record_id
        != payload.client_record_id
    ):
        error_detail = {
            "code":
                "CLIENT_RECORD_ID_MISMATCH",
            "message": (
                "client_record_id trong URL "
                "không khớp với payload."
            ),
        }

        create_history(
            database_session=database_session,
            event_type="update_issue_report",
            client_record_id=client_record_id,
            request_payload=request_payload,
            response_payload={
                "detail": error_detail,
            },
            status="failed",
            http_status=(
                status.HTTP_400_BAD_REQUEST
            ),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=error_detail,
        )

    existing_report = (
        get_issue_report_by_client_record_id(
            database_session=(
                database_session
            ),
            client_record_id=(
                client_record_id
            ),
        )
    )

    if existing_report is None:
        error_detail = {
            "code":
                "ISSUE_REPORT_NOT_FOUND",
            "message":
                "Không tìm thấy báo cáo sự cố.",
        }

        create_history(
            database_session=database_session,
            event_type="update_issue_report",
            client_record_id=client_record_id,
            request_payload=request_payload,
            response_payload={
                "detail": error_detail,
            },
            status="failed",
            http_status=(
                status.HTTP_404_NOT_FOUND
            ),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=error_detail,
        )

    if not payload.confirmed:
        error_detail = {
            "code":
                "UNCONFIRMED_RECORD",
            "message": (
                "Báo cáo sự cố chưa được "
                "người dùng xác nhận."
            ),
        }

        create_history(
            database_session=database_session,
            event_type="update_issue_report",
            client_record_id=client_record_id,
            request_payload=request_payload,
            response_payload={
                "detail": error_detail,
            },
            status="failed",
            http_status=(
                status.HTTP_400_BAD_REQUEST
            ),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=error_detail,
        )

    try:
        canonical_payload = (
            build_issue_report_input(
                payload,
                database_session,
            )
        )

    except IssueReportValidationError as error:
        error_detail = {
            "code":
                "ISSUE_REPORT_VALIDATION_FAILED",
            "field":
                error.field,
            "reason_code":
                error.code,
            "message":
                error.message,
        }

        create_history(
            database_session=database_session,
            event_type="update_issue_report",
            client_record_id=client_record_id,
            request_payload=request_payload,
            response_payload={
                "detail": error_detail,
            },
            status="failed",
            http_status=(
                status.HTTP_400_BAD_REQUEST
            ),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=error_detail,
        ) from error

    updated_report = (
        update_issue_report(
            database_session=(
                database_session
            ),
            client_record_id=(
                client_record_id
            ),
            payload=canonical_payload,
        )
    )

    if updated_report is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail={
                "code":
                    "ISSUE_REPORT_NOT_FOUND",
                "message":
                    "Không tìm thấy báo cáo sự cố.",
            },
        )

    response = IssueReportSaveResponse(
        success=True,
        status="updated",
        data=updated_report,
    )

    create_history(
        database_session=database_session,
        event_type="update_issue_report",
        client_record_id=client_record_id,
        request_payload=request_payload,
        response_payload=(
            response.model_dump(
                mode="json"
            )
        ),
        status="success",
        http_status=status.HTTP_200_OK,
    )

    return response


@router.get(
    "",
    response_model=IssueReportListResponse,
)
def list_issue_reports(
    database_session: Session = Depends(
        get_db
    ),
) -> IssueReportListResponse:
    records = get_all_issue_reports(
        database_session=(
            database_session
        )
    )

    return IssueReportListResponse(
        success=True,
        data=records,
    )


@router.get(
    "/{client_record_id}",
    response_model=IssueReportGetResponse,
)
def get_issue_report(
    client_record_id: str,

    database_session: Session = Depends(
        get_db
    ),
) -> IssueReportGetResponse:
    record = (
        get_issue_report_by_client_record_id(
            database_session=(
                database_session
            ),
            client_record_id=(
                client_record_id
            ),
        )
    )

    if record is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail={
                "code":
                    "ISSUE_REPORT_NOT_FOUND",
                "message":
                    "Không tìm thấy báo cáo sự cố.",
            },
        )

    return IssueReportGetResponse(
        success=True,
        data=record,
    )
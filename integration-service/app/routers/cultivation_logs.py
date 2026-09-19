from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.cultivation_log import (
    CultivationLogInput,
)
from app.schemas.dynamic_form_bridge import (
    DynamicWorkLogSaveRequest,
)
from app.services.dynamic_form_adapter_service import (
    DynamicFormCanonicalResolutionError,
    build_cultivation_log_input,
)
from app.schemas.responses import (
    GetLogResponse,
    ListLogsResponse,
    SaveLogResponse,
    ValidationResponse,
)
from app.services.business_validation_service import (
    validate_business_rules,
)
from app.services.history_service import (
    create_history,
)
from app.services.log_service import (
    create_log,
    get_all_logs,
    get_log_by_client_record_id,
    update_log,
)


router = APIRouter(
    prefix="/api/cultivation-logs",
    tags=["Cultivation Logs"],
)


@router.get("/test")
def test_cultivation_logs_router() -> dict[str, str]:
    """
    Kiểm tra router nhật ký
    có hoạt động hay không.
    """

    return {
        "status": "ok",
        "message": (
            "Cultivation logs router "
            "is working"
        ),
    }


@router.post(
    "/validate",
    response_model=ValidationResponse,
)
def validate_cultivation_log(
    payload: CultivationLogInput,
    database_session: Session = Depends(
        get_db
    ),
) -> ValidationResponse:
    """
    Canonical validation endpoint.

    Pydantic xử lý:
    - schema
    - type
    - required fields
    - quantity constraints

    Business Rule Engine xử lý:
    - activity code
    - lot code
    - material code
    - unit code
    - activity requirements
    - confirmation rules

    Endpoint này chỉ validate,
    không ghi database.
    """

    result = validate_business_rules(
        payload,
        database_session,
    )
    return ValidationResponse(
        valid=bool(
            result["valid"]
        ),

        errors=result["errors"],

        warnings=result["warnings"],

        rule_version=str(
            result["rule_version"]
        ),

        requires_confirmation=bool(
            result[
                "requires_confirmation"
            ]
        ),

        normalized_data=(
            payload.model_dump(
                mode="json"
            )
        ),
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SaveLogResponse,
)
def save_cultivation_log(
    payload: CultivationLogInput,

    database_session: Session = Depends(
        get_db
    ),
) -> SaveLogResponse:
    """
    Lưu nhật ký vào PostgreSQL.

    Quan trọng:
    Backend luôn chạy lại
    business validation trước khi lưu.

    Không tin rằng frontend đã
    validate đúng.
    """

    request_payload = (
        payload.model_dump(
            mode="json"
        )
    )

    # =========================================================
    # BACKEND BUSINESS VALIDATION
    # =========================================================

    validation = (
        validate_business_rules(
            payload,
            database_session,
        )
    )


    # =========================================================
    # USER CONFIRMATION REQUIRED
    # =========================================================

    if not payload.confirmed:
        error_detail = {
            "code":
                "UNCONFIRMED_RECORD",

            "message": (
                "Nhật ký chưa được "
                "người dùng xác nhận."
            ),

            "rule_version":
                validation[
                    "rule_version"
                ],
        }

        create_history(
            database_session=(
                database_session
            ),

            event_type=(
                "save_cultivation_log"
            ),

            client_record_id=(
                payload.client_record_id
            ),

            request_payload=(
                request_payload
            ),

            response_payload={
                "detail":
                    error_detail,
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


    # =========================================================
    # BUSINESS VALIDATION FAILED
    # =========================================================

    if not validation["valid"]:
        error_detail = {
            "code":
                "BUSINESS_VALIDATION_FAILED",

            "message": (
                "Dữ liệu không đạt "
                "business validation."
            ),

            "rule_version":
                validation[
                    "rule_version"
                ],

            "errors":
                validation[
                    "errors"
                ],

            "warnings":
                validation[
                    "warnings"
                ],
        }

        create_history(
            database_session=(
                database_session
            ),

            event_type=(
                "save_cultivation_log"
            ),

            client_record_id=(
                payload.client_record_id
            ),

            request_payload=(
                request_payload
            ),

            response_payload={
                "detail":
                    error_detail,
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


    # =========================================================
    # SAVE
    # =========================================================

    record, created = create_log(
        database_session=(
            database_session
        ),

        payload=payload,
    )

    response = SaveLogResponse(
        success=True,

        status=(
            "saved"
            if created
            else "already_exists"
        ),

        data=record,
    )


    # =========================================================
    # HISTORY
    # =========================================================

    create_history(
        database_session=(
            database_session
        ),

        event_type=(
            "save_cultivation_log"
        ),

        client_record_id=(
            payload.client_record_id
        ),

        request_payload=(
            request_payload
        ),

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

@router.post(
    "/from-dynamic-form",
    status_code=status.HTTP_201_CREATED,
    response_model=SaveLogResponse,
)
def save_dynamic_work_log(
    payload: DynamicWorkLogSaveRequest,

    database_session: Session = Depends(
        get_db
    ),
) -> SaveLogResponse:
    """
    Bridge:
    Dynamic Form V3.1
        -> canonical CultivationLogInput
        -> existing cultivation-log save flow.

    Integration responsibilities:
    - resolve *_text -> canonical code
    - preserve canonical NextFarm context
    - delegate business validation
      và confirmation cho save flow hiện có

    Không:
    - parse transcript
    - NLP
    - AI confidence
    - suy diễn NextFarm IDs
    """

    try:
        canonical_payload = (
            build_cultivation_log_input(
                payload.dynamic_form,
                client_record_id=(
                    payload.client_record_id
                ),
                performed_at=(
                    payload.performed_at
                ),
                context=payload.context,
                confirmed=payload.confirmed,
                database_session=database_session,
            )
        )

    except (
        DynamicFormCanonicalResolutionError
    ) as error:
        error_detail = {
            "code":
                "DYNAMIC_FORM_RESOLUTION_FAILED",

            "field":
                error.field,

            "reason_code":
                error.code,

            "message":
                error.message,
        }

        create_history(
            database_session=(
                database_session
            ),

            event_type=(
                "save_dynamic_work_log"
            ),

            client_record_id=(
                payload.client_record_id
            ),

            request_payload=(
                payload.model_dump(
                    mode="json"
                )
            ),

            response_payload={
                "detail":
                    error_detail,
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

    # Quan trọng:
    # Không viết lại business validation,
    # confirmation gate hoặc persistence.
    #
    # Delegate về canonical save flow
    # hiện có.
    return save_cultivation_log(
        payload=canonical_payload,
        database_session=database_session,
    )
@router.put(
    "/{client_record_id}",
    response_model=SaveLogResponse,
)
def update_cultivation_log(
    client_record_id: str,
    payload: CultivationLogInput,

    database_session: Session = Depends(
        get_db
    ),
) -> SaveLogResponse:
    """
    Cập nhật một cultivation log đã tồn tại.

    Backend không tin frontend:
    - record phải tồn tại
    - URL/body client_record_id phải khớp
    - user phải confirmed
    - business validation phải pass
    - materials[] được thay toàn bộ
    """

    request_payload = (
        payload.model_dump(
            mode="json"
        )
    )

    # =========================================================
    # CLIENT RECORD ID MUST MATCH
    # =========================================================

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
            database_session=(
                database_session
            ),

            event_type=(
                "update_cultivation_log"
            ),

            client_record_id=(
                client_record_id
            ),

            request_payload=(
                request_payload
            ),

            response_payload={
                "detail":
                    error_detail,
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

    # =========================================================
    # RECORD MUST EXIST
    # =========================================================

    existing_record = (
        get_log_by_client_record_id(
            database_session=(
                database_session
            ),

            client_record_id=(
                client_record_id
            ),
        )
    )

    if existing_record is None:
        error_detail = {
            "code":
                "CULTIVATION_LOG_NOT_FOUND",

            "message":
                "Không tìm thấy nhật ký.",
        }

        create_history(
            database_session=(
                database_session
            ),

            event_type=(
                "update_cultivation_log"
            ),

            client_record_id=(
                client_record_id
            ),

            request_payload=(
                request_payload
            ),

            response_payload={
                "detail":
                    error_detail,
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

    # =========================================================
    # BACKEND BUSINESS VALIDATION
    # =========================================================

    validation = (
        validate_business_rules(
            payload,
            database_session,
        )
    )

    # =========================================================
    # USER CONFIRMATION
    # =========================================================

    if not payload.confirmed:
        error_detail = {
            "code":
                "UNCONFIRMED_RECORD",

            "message": (
                "Nhật ký chưa được "
                "người dùng xác nhận."
            ),

            "rule_version":
                validation[
                    "rule_version"
                ],
        }

        create_history(
            database_session=(
                database_session
            ),

            event_type=(
                "update_cultivation_log"
            ),

            client_record_id=(
                client_record_id
            ),

            request_payload=(
                request_payload
            ),

            response_payload={
                "detail":
                    error_detail,
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

    # =========================================================
    # BUSINESS VALIDATION FAILED
    # =========================================================

    if not validation["valid"]:
        error_detail = {
            "code":
                "BUSINESS_VALIDATION_FAILED",

            "message": (
                "Dữ liệu không đạt "
                "business validation."
            ),

            "rule_version":
                validation[
                    "rule_version"
                ],

            "errors":
                validation[
                    "errors"
                ],

            "warnings":
                validation[
                    "warnings"
                ],
        }

        create_history(
            database_session=(
                database_session
            ),

            event_type=(
                "update_cultivation_log"
            ),

            client_record_id=(
                client_record_id
            ),

            request_payload=(
                request_payload
            ),

            response_payload={
                "detail":
                    error_detail,
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

    # =========================================================
    # UPDATE
    # =========================================================

    updated_record = update_log(
        database_session=(
            database_session
        ),

        client_record_id=(
            client_record_id
        ),

        payload=payload,
    )

    if updated_record is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),

            detail={
                "code":
                    "CULTIVATION_LOG_NOT_FOUND",

                "message":
                    "Không tìm thấy nhật ký.",
            },
        )

    response = SaveLogResponse(
        success=True,
        status="updated",
        data=updated_record,
    )

    # =========================================================
    # HISTORY SUCCESS
    # =========================================================

    create_history(
        database_session=(
            database_session
        ),

        event_type=(
            "update_cultivation_log"
        ),

        client_record_id=(
            client_record_id
        ),

        request_payload=(
            request_payload
        ),

        response_payload=(
            response.model_dump(
                mode="json"
            )
        ),

        status="success",

        http_status=(
            status.HTTP_200_OK
        ),
    )

    return response

@router.get(
    "",
    response_model=ListLogsResponse,
)
def list_cultivation_logs(
    database_session: Session = Depends(
        get_db
    ),
) -> ListLogsResponse:
    """
    Lấy danh sách nhật ký
    từ PostgreSQL.
    """

    records = get_all_logs(
        database_session=(
            database_session
        )
    )

    return ListLogsResponse(
        success=True,
        data=records,
    )


@router.get(
    "/{client_record_id}",
    response_model=GetLogResponse,
)
def get_cultivation_log(
    client_record_id: str,

    database_session: Session = Depends(
        get_db
    ),
) -> GetLogResponse:
    """
    Lấy một nhật ký theo
    client_record_id.
    """

    record = (
        get_log_by_client_record_id(
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
                    "CULTIVATION_LOG_NOT_FOUND",

                "message":
                    "Không tìm thấy nhật ký.",
            },
        )

    return GetLogResponse(
        success=True,
        data=record,
    )
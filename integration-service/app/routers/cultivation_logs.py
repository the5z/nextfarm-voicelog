from fastapi import APIRouter

from app.schemas.cultivation_log import CultivationLogInput


router = APIRouter(
    prefix="/api/cultivation-logs",
    tags=["Cultivation Logs"],
)


@router.post("/validate")
def validate_cultivation_log(
    payload: CultivationLogInput,
) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []

    if not payload.confirmed:
        warnings.append(
            {
                "field": "confirmed",
                "code": "UNCONFIRMED_RECORD",
                "message": "Nhật ký chưa được người dùng xác nhận",
            }
        )

    if not payload.materials:
        warnings.append(
            {
                "field": "materials",
                "code": "EMPTY_MATERIALS",
                "message": "Nhật ký chưa có thông tin vật tư",
            }
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "normalized_data": payload.model_dump(mode="json"),
    }
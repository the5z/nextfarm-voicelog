from fastapi import APIRouter

from app.schemas.dynamic_form import (
    DynamicFormRequest,
    DynamicFormResponse,
)
from app.services.dynamic_form_service import extract_dynamic_form


router = APIRouter(
    prefix="/api/v1/dynamic-form",
    tags=["Dynamic Form"],
)


@router.post(
    "/extract",
    response_model=DynamicFormResponse,
)
def extract_form(
    request: DynamicFormRequest,
) -> DynamicFormResponse:
    return extract_dynamic_form(
        operation=request.operation,
        transcript=request.transcript,
        current_fields=request.current_fields,
        context=request.context,
    )

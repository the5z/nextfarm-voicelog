from app.schemas.master_data import (
    MasterDataType,
    ResolveCultivationRequest,
    ResolveCultivationResponse,
    ResolveMasterDataResponse,
    ResolvedCultivationMaterial,
)
from app.services.normalization_service import (
    normalize_text,
    resolve_master_data,
)


def _missing_resolution(
    field_name: str,
) -> ResolveMasterDataResponse:
    return ResolveMasterDataResponse(
        matched=False,
        code=None,
        name=None,
        confidence=0.0,
        match_type="none",
        matched_text=None,
        requires_confirmation=True,
        normalized_text="",
        message=f"Chưa có dữ liệu cho {field_name}.",
    )


def _resolve_optional(
    data_type: MasterDataType,
    text: str | None,
    field_name: str,
) -> ResolveMasterDataResponse:
    if text is None or not normalize_text(text):
        return _missing_resolution(field_name)

    result = resolve_master_data(
        data_type=data_type,
        text=text,
    )

    return ResolveMasterDataResponse.model_validate(
        result
    )


def resolve_cultivation_master_data(
    request: ResolveCultivationRequest,
) -> ResolveCultivationResponse:
    activity = _resolve_optional(
        data_type="activity",
        text=request.activity_text,
        field_name="activity_text",
    )

    lot = _resolve_optional(
        data_type="lot",
        text=request.lot_text,
        field_name="lot_text",
    )

    materials: list[
        ResolvedCultivationMaterial
    ] = []

    for item in request.materials:
        material = _resolve_optional(
            data_type="material",
            text=item.material_text,
            field_name="material_text",
        )

        unit = _resolve_optional(
            data_type="unit",
            text=item.unit_text,
            field_name="unit_text",
        )

        materials.append(
            ResolvedCultivationMaterial(
                material=material,
                quantity=item.quantity,
                unit=unit,
            )
        )

    requires_confirmation = (
        activity.requires_confirmation
        or lot.requires_confirmation
        or any(
            (
                item.material.requires_confirmation
                or item.unit.requires_confirmation
                or item.quantity is None
            )
            for item in materials
        )
    )

    return ResolveCultivationResponse(
        activity=activity,
        lot=lot,
        materials=materials,
        time_text=request.time_text,
        requires_confirmation=requires_confirmation,
    )
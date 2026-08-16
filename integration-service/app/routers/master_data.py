from fastapi import APIRouter

from app.data.master_data import (
    ACTIVITIES,
    LOTS,
    MATERIALS,
    UNITS,
)
from app.schemas.master_data import (
    MasterDataItem,
    ResolveCultivationRequest,
    ResolveCultivationResponse,
    ResolveMasterDataRequest,
    ResolveMasterDataResponse,
)
from app.services.master_data_service import (
    resolve_cultivation_master_data,
)
from app.services.normalization_service import (
    resolve_master_data,
)


router = APIRouter(
    prefix="/api/master-data",
    tags=["Master Data"],
)


def _build_items(records) -> list[MasterDataItem]:
    return [
        MasterDataItem(
            code=record["code"],
            name=record["name"],
            aliases=record.get("aliases", []),
        )
        for record in records
    ]


@router.get(
    "/activities",
    response_model=list[MasterDataItem],
)
def get_activities() -> list[MasterDataItem]:
    return _build_items(ACTIVITIES)


@router.get(
    "/units",
    response_model=list[MasterDataItem],
)
def get_units() -> list[MasterDataItem]:
    return _build_items(UNITS)


@router.get(
    "/lots",
    response_model=list[MasterDataItem],
)
def get_lots() -> list[MasterDataItem]:
    return _build_items(LOTS)


@router.get(
    "/materials",
    response_model=list[MasterDataItem],
)
def get_materials() -> list[MasterDataItem]:
    return _build_items(MATERIALS)


@router.post(
    "/resolve",
    response_model=ResolveMasterDataResponse,
)
def resolve_master_data_endpoint(
    request: ResolveMasterDataRequest,
) -> ResolveMasterDataResponse:
    result = resolve_master_data(
        data_type=request.data_type,
        text=request.text,
    )

    return ResolveMasterDataResponse.model_validate(
        result
    )


@router.post(
    "/resolve-cultivation",
    response_model=ResolveCultivationResponse,
)
def resolve_cultivation_endpoint(
    request: ResolveCultivationRequest,
) -> ResolveCultivationResponse:
    return resolve_cultivation_master_data(
        request
    )
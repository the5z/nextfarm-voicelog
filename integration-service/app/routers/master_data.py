from fastapi import APIRouter

from app.data.master_data import (
    ACTIVITIES,
    LOTS,
    MATERIALS,
    UNITS,
)
from app.schemas.master_data import (
    MasterDataItem,
    ResolveMasterDataRequest,
    ResolveMasterDataResponse,
)
from app.services.normalization_service import resolve_master_data


router = APIRouter(
    prefix="/api/master-data",
    tags=["Master Data"],
)


def build_master_data_items(
    records: list[dict[str, str | list[str]]],
) -> list[MasterDataItem]:
    return [
        MasterDataItem(**record)
        for record in records
    ]


@router.get(
    "/activities",
    response_model=list[MasterDataItem],
)
def get_activities() -> list[MasterDataItem]:
    return build_master_data_items(ACTIVITIES)


@router.get(
    "/units",
    response_model=list[MasterDataItem],
)
def get_units() -> list[MasterDataItem]:
    return build_master_data_items(UNITS)


@router.get(
    "/lots",
    response_model=list[MasterDataItem],
)
def get_lots() -> list[MasterDataItem]:
    return build_master_data_items(LOTS)


@router.get(
    "/materials",
    response_model=list[MasterDataItem],
)
def get_materials() -> list[MasterDataItem]:
    return build_master_data_items(MATERIALS)


@router.post(
    "/resolve",
    response_model=ResolveMasterDataResponse,
)
def resolve_value(
    payload: ResolveMasterDataRequest,
) -> ResolveMasterDataResponse:
    result = resolve_master_data(
        data_type=payload.data_type,
        text=payload.text,
    )

    return ResolveMasterDataResponse(**result)
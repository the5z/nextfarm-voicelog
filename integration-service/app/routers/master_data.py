from fastapi import APIRouter

from app.data.master_data import ACTIVITIES, UNITS
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


@router.get(
    "/activities",
    response_model=list[MasterDataItem],
)
def get_activities() -> list[MasterDataItem]:
    return [
        MasterDataItem(**item)
        for item in ACTIVITIES
    ]


@router.get(
    "/units",
    response_model=list[MasterDataItem],
)
def get_units() -> list[MasterDataItem]:
    return [
        MasterDataItem(**item)
        for item in UNITS
    ]


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
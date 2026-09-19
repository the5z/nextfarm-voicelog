from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
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
from app.schemas.season_master_data import (
    ResolveSeasonRequest,
    ResolveSeasonResponse,
    SeasonMasterDataItem,
)
from app.schemas.crop_master_data import (
    CropMasterDataItem,
    ResolveCropRequest,
    ResolveCropResponse,
)
from app.schemas.region_master_data import (
    RegionMasterDataItem,
    ResolveRegionRequest,
    ResolveRegionResponse,
)
from app.services.master_data_service import (
    resolve_cultivation_master_data,
)
from app.services.normalization_service import (
    resolve_master_data,
)
from app.services.season_master_data_service import (
    SeasonMasterDataConfigurationError,
    load_season_master_data,
    resolve_season_text,
)
from app.services.crop_master_data_service import (
    CropMasterDataConfigurationError,
    load_crop_master_data,
    resolve_crop_text,
)
from app.services.region_master_data_service import (
    RegionMasterDataConfigurationError,
    load_region_master_data,
    resolve_region_text,
)
from app.services.plot_master_data_service import (
    load_plot_master_data,
    resolve_plot_text,
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
def get_lots(
    database_session: Session = Depends(
        get_db
    ),
) -> list[MasterDataItem]:
    return _build_items(
        load_plot_master_data(
            database_session
        )
    )


@router.get(
    "/materials",
    response_model=list[MasterDataItem],
)
def get_materials() -> list[MasterDataItem]:
    return _build_items(MATERIALS)

@router.get(
    "/crops",
    response_model=list[
        CropMasterDataItem
    ],
)
def get_crops(
    database_session: Session = Depends(
        get_db
    ),
) -> list[CropMasterDataItem]:
    try:
        return load_crop_master_data(
            database_session
        )

    except (
        CropMasterDataConfigurationError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "code": (
                    "CROP_MASTER_DATA_UNAVAILABLE"
                ),
                "message": str(error),
            },
        ) from error


@router.post(
    "/resolve-crop",
    response_model=ResolveCropResponse,
)
def resolve_crop_endpoint(
    request: ResolveCropRequest,
    database_session: Session = Depends(
        get_db
    ),
) -> ResolveCropResponse:
    try:
        return resolve_crop_text(
            request.text,
            database_session,
        )

    except (
        CropMasterDataConfigurationError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "code": (
                    "CROP_MASTER_DATA_UNAVAILABLE"
                ),
                "message": str(error),
            },
        ) from error


@router.get(
    "/regions",
    response_model=list[
        RegionMasterDataItem
    ],
)
def get_regions(
) -> list[RegionMasterDataItem]:
    try:
        return load_region_master_data()

    except (
        RegionMasterDataConfigurationError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "code": (
                    "REGION_MASTER_DATA_UNAVAILABLE"
                ),
                "message": str(error),
            },
        ) from error


@router.post(
    "/resolve-region",
    response_model=ResolveRegionResponse,
)
def resolve_region_endpoint(
    request: ResolveRegionRequest,
) -> ResolveRegionResponse:
    try:
        return resolve_region_text(
            request.text
        )

    except (
        RegionMasterDataConfigurationError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "code": (
                    "REGION_MASTER_DATA_UNAVAILABLE"
                ),
                "message": str(error),
            },
        ) from error


@router.get(
    "/seasons",
    response_model=list[
        SeasonMasterDataItem
    ],
)
def get_seasons(
    database_session: Session = Depends(
        get_db
    ),
) -> list[SeasonMasterDataItem]:
    try:
        return load_season_master_data(
            database_session
        )
    except (
        SeasonMasterDataConfigurationError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "code": (
                    "SEASON_MASTER_DATA_UNAVAILABLE"
                ),
                "message": str(error),
            },
        ) from error


@router.post(
    "/resolve-season",
    response_model=ResolveSeasonResponse,
)
def resolve_season_endpoint(
    request: ResolveSeasonRequest,
    database_session: Session = Depends(
        get_db
    ),
) -> ResolveSeasonResponse:
    try:
        return resolve_season_text(
            request.text,
            database_session,
        )

    except (
        SeasonMasterDataConfigurationError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "code": (
                    "SEASON_MASTER_DATA_UNAVAILABLE"
                ),
                "message": str(error),
            },
        ) from error

@router.post(
    "/resolve",
    response_model=ResolveMasterDataResponse,
)
def resolve_master_data_endpoint(
    request: ResolveMasterDataRequest,
    database_session: Session = Depends(
        get_db
    ),
) -> ResolveMasterDataResponse:
    if request.data_type == "lot":
        result = resolve_plot_text(
            request.text,
            database_session,
        )
    else:
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
    database_session: Session = Depends(
        get_db
    ),
) -> ResolveCultivationResponse:
    return resolve_cultivation_master_data(
        request,
        database_session,
    )
from __future__ import annotations

import json
import os

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crop_type import (
    CropTypeModel,
)
from app.schemas.crop_master_data import (
    CropMasterDataItem,
    ResolveCropResponse,
)
from app.services.normalization_service import (
    calculate_similarity,
    normalize_text,
)


CROP_MASTER_DATA_ENV = (
    "NEXTFARM_CROPS_JSON"
)

FUZZY_MATCH_THRESHOLD = 0.82


class CropMasterDataConfigurationError(
    RuntimeError
):
    pass


def _validate_unique_items(
    items: list[CropMasterDataItem],
) -> None:
    seen_ids: set[str] = set()

    seen_terms: dict[
        str,
        str,
    ] = {}

    for item in items:
        if item.crop_id in seen_ids:
            raise CropMasterDataConfigurationError(
                (
                    "Trùng crop_id trong "
                    "nguồn dữ liệu cây trồng: "
                    f"{item.crop_id}"
                )
            )

        seen_ids.add(
            item.crop_id
        )

        for term in [
            item.name,
            *item.aliases,
        ]:
            normalized_term = (
                normalize_text(term)
            )

            if not normalized_term:
                continue

            previous_owner = (
                seen_terms.get(
                    normalized_term
                )
            )

            if (
                previous_owner is not None
                and previous_owner
                != item.crop_id
            ):
                raise CropMasterDataConfigurationError(
                    (
                        "Tên/alias cây trồng "
                        "bị trùng giữa nhiều "
                        "crop_id: "
                        f"'{term}'."
                    )
                )

            seen_terms[
                normalized_term
            ] = item.crop_id


def load_configured_crop_master_data(
) -> list[CropMasterDataItem]:
    """
    Đọc nguồn cây trồng canonical
    từ NEXTFARM_CROPS_JSON.

    Không có cấu hình vẫn hợp lệ nếu
    Integration DB đã có cây trồng.
    """

    raw_value = os.getenv(
        CROP_MASTER_DATA_ENV
    )

    if (
        raw_value is None
        or not raw_value.strip()
    ):
        return []

    try:
        raw_items = json.loads(
            raw_value
        )

    except json.JSONDecodeError as error:
        raise CropMasterDataConfigurationError(
            (
                "NEXTFARM_CROPS_JSON "
                "không phải JSON hợp lệ."
            )
        ) from error

    if not isinstance(
        raw_items,
        list,
    ):
        raise CropMasterDataConfigurationError(
            (
                "NEXTFARM_CROPS_JSON "
                "phải là một JSON array."
            )
        )

    try:
        items = [
            CropMasterDataItem.model_validate(
                raw_item
            )
            for raw_item in raw_items
        ]

    except ValidationError as error:
        raise CropMasterDataConfigurationError(
            (
                "Dữ liệu cây trồng canonical "
                "không đúng schema."
            )
        ) from error

    _validate_unique_items(
        items
    )

    return items


def _load_persisted_crops(
    database_session: Session | None,
) -> list[CropMasterDataItem]:
    if database_session is None:
        return []

    statement = (
        select(CropTypeModel)
        .where(
            CropTypeModel.status
            == "saved"
        )
        .order_by(
            CropTypeModel.id.asc()
        )
    )

    records = (
        database_session
        .scalars(statement)
        .all()
    )

    return [
        CropMasterDataItem(
            crop_id=record.crop_id,
            name=record.crop_name,
            aliases=[],
        )
        for record in records
    ]


def load_crop_master_data(
    database_session: Session | None = None,
) -> list[CropMasterDataItem]:
    """
    Trả nguồn cây trồng hợp nhất:

    - NEXTFARM_CROPS_JSON
    - cây trồng đã lưu trong Integration DB
    """

    items = [
        *load_configured_crop_master_data(),
        *_load_persisted_crops(
            database_session
        ),
    ]

    if not items:
        raise CropMasterDataConfigurationError(
            (
                "Chưa có nguồn dữ liệu cây trồng. "
                "Hãy cấu hình NEXTFARM_CROPS_JSON "
                "hoặc tạo cây trồng trong Integration."
            )
        )

    _validate_unique_items(
        items
    )

    return items


def resolve_crop_text(
    text: str,
    database_session: Session | None = None,
) -> ResolveCropResponse:
    normalized_input = normalize_text(
        text
    )

    items = load_crop_master_data(
        database_session
    )

    # 1. Exact name
    for item in items:
        if (
            normalized_input
            == normalize_text(
                item.name
            )
        ):
            return ResolveCropResponse(
                matched=True,
                crop_id=item.crop_id,
                name=item.name,
                confidence=1.0,
                match_type="exact",
                matched_text=item.name,
                requires_confirmation=False,
                normalized_text=(
                    normalized_input
                ),
                message=(
                    "Đã khớp chính xác cây trồng."
                ),
            )

    # 2. Alias
    for item in items:
        for alias in item.aliases:
            if (
                normalized_input
                == normalize_text(alias)
            ):
                return ResolveCropResponse(
                    matched=True,
                    crop_id=item.crop_id,
                    name=item.name,
                    confidence=1.0,
                    match_type="alias",
                    matched_text=alias,
                    requires_confirmation=False,
                    normalized_text=(
                        normalized_input
                    ),
                    message=(
                        "Đã khớp bí danh cây trồng."
                    ),
                )

    # 3. Fuzzy
    best_item: (
        CropMasterDataItem | None
    ) = None

    best_matched_text: (
        str | None
    ) = None

    best_score = 0.0

    for item in items:
        for candidate in [
            item.name,
            *item.aliases,
        ]:
            score = calculate_similarity(
                text,
                candidate,
            )

            if score > best_score:
                best_score = score
                best_item = item
                best_matched_text = (
                    candidate
                )

    if (
        best_item is not None
        and best_matched_text is not None
        and best_score
        >= FUZZY_MATCH_THRESHOLD
    ):
        return ResolveCropResponse(
            matched=True,
            crop_id=best_item.crop_id,
            name=best_item.name,
            confidence=round(
                best_score,
                4,
            ),
            match_type="fuzzy",
            matched_text=(
                best_matched_text
            ),
            requires_confirmation=True,
            normalized_text=(
                normalized_input
            ),
            message=(
                "Đã tìm thấy cây trồng gần đúng. "
                "Cần người dùng xác nhận."
            ),
        )

    return ResolveCropResponse(
        matched=False,
        crop_id=None,
        name=None,
        confidence=0.0,
        match_type="none",
        matched_text=None,
        requires_confirmation=True,
        normalized_text=(
            normalized_input
        ),
        message=(
            "Không tìm thấy cây trồng phù hợp "
            "trong nguồn dữ liệu canonical."
        ),
    )
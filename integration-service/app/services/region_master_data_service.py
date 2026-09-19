from __future__ import annotations

import json
import os

from pydantic import ValidationError

from app.schemas.region_master_data import (
    RegionMasterDataItem,
    ResolveRegionResponse,
)
from app.services.normalization_service import (
    calculate_similarity,
    normalize_text,
)


REGION_MASTER_DATA_ENV = (
    "NEXTFARM_REGIONS_JSON"
)

FUZZY_MATCH_THRESHOLD = 0.82


class RegionMasterDataConfigurationError(
    RuntimeError
):
    """
    Nguồn dữ liệu khu vực canonical
    chưa có hoặc không hợp lệ.
    """


def _validate_unique_items(
    items: list[RegionMasterDataItem],
) -> None:
    seen_ids: set[str] = set()

    seen_terms: dict[
        str,
        str,
    ] = {}

    for item in items:
        if item.region_id in seen_ids:
            raise (
                RegionMasterDataConfigurationError(
                    (
                        "Trùng region_id trong "
                        "NEXTFARM_REGIONS_JSON: "
                        f"{item.region_id}"
                    )
                )
            )

        seen_ids.add(
            item.region_id
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
                != item.region_id
            ):
                raise (
                    RegionMasterDataConfigurationError(
                        (
                            "Tên/alias khu vực "
                            "bị trùng giữa nhiều "
                            "region_id: "
                            f"'{term}'."
                        )
                    )
                )

            seen_terms[
                normalized_term
            ] = item.region_id


def load_region_master_data(
) -> list[RegionMasterDataItem]:
    """
    Đọc dữ liệu khu vực chuẩn.

    Integration không tự tạo region_id.
    """

    raw_value = os.getenv(
        REGION_MASTER_DATA_ENV
    )

    if (
        raw_value is None
        or not raw_value.strip()
    ):
        raise (
            RegionMasterDataConfigurationError(
                (
                    "Chưa cấu hình "
                    "NEXTFARM_REGIONS_JSON."
                )
            )
        )

    try:
        raw_items = json.loads(
            raw_value
        )

    except json.JSONDecodeError as error:
        raise (
            RegionMasterDataConfigurationError(
                (
                    "NEXTFARM_REGIONS_JSON "
                    "không phải JSON hợp lệ."
                )
            )
        ) from error

    if not isinstance(
        raw_items,
        list,
    ):
        raise (
            RegionMasterDataConfigurationError(
                (
                    "NEXTFARM_REGIONS_JSON "
                    "phải là một JSON array."
                )
            )
        )

    try:
        items = [
            RegionMasterDataItem.model_validate(
                raw_item
            )
            for raw_item in raw_items
        ]

    except ValidationError as error:
        raise (
            RegionMasterDataConfigurationError(
                (
                    "Dữ liệu khu vực canonical "
                    "không đúng schema."
                )
            )
        ) from error

    _validate_unique_items(
        items
    )

    return items


def resolve_region_text(
    text: str,
) -> ResolveRegionResponse:
    """
    Ánh xạ region_text sang region_id chuẩn.

    Không tự tạo ID nếu không tìm thấy.
    """

    normalized_input = normalize_text(
        text
    )

    items = load_region_master_data()

    for item in items:
        if (
            normalized_input
            == normalize_text(
                item.name
            )
        ):
            return ResolveRegionResponse(
                matched=True,
                region_id=item.region_id,
                name=item.name,
                confidence=1.0,
                match_type="exact",
                matched_text=item.name,
                requires_confirmation=False,
                normalized_text=(
                    normalized_input
                ),
                message=(
                    "Đã khớp chính xác khu vực."
                ),
            )

    for item in items:
        for alias in item.aliases:
            if (
                normalized_input
                == normalize_text(alias)
            ):
                return ResolveRegionResponse(
                    matched=True,
                    region_id=item.region_id,
                    name=item.name,
                    confidence=1.0,
                    match_type="alias",
                    matched_text=alias,
                    requires_confirmation=False,
                    normalized_text=(
                        normalized_input
                    ),
                    message=(
                        "Đã khớp bí danh khu vực."
                    ),
                )

    best_item: (
        RegionMasterDataItem | None
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
        return ResolveRegionResponse(
            matched=True,
            region_id=(
                best_item.region_id
            ),
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
                "Đã tìm thấy khu vực gần đúng. "
                "Cần người dùng xác nhận."
            ),
        )

    return ResolveRegionResponse(
        matched=False,
        region_id=None,
        name=None,
        confidence=0.0,
        match_type="none",
        matched_text=None,
        requires_confirmation=True,
        normalized_text=(
            normalized_input
        ),
        message=(
            "Không tìm thấy khu vực phù hợp "
            "trong nguồn dữ liệu canonical."
        ),
    )
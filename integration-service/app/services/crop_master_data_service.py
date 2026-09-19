from __future__ import annotations

import json
import os

from pydantic import ValidationError

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
    """
    Cấu hình nguồn cây trồng canonical
    không hợp lệ.
    """


def load_crop_master_data(
) -> list[CropMasterDataItem]:
    """
    Đọc cây trồng canonical từ biến môi trường.

    Integration không tự sinh crop_id.
    """

    raw_value = os.getenv(
        CROP_MASTER_DATA_ENV
    )

    if (
        raw_value is None
        or not raw_value.strip()
    ):
        raise CropMasterDataConfigurationError(
            (
                "Chưa cấu hình "
                "NEXTFARM_CROPS_JSON."
            )
        )

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

    items: list[
        CropMasterDataItem
    ] = []

    try:
        for raw_item in raw_items:
            items.append(
                CropMasterDataItem.model_validate(
                    raw_item
                )
            )

    except ValidationError as error:
        raise CropMasterDataConfigurationError(
            (
                "Dữ liệu cây trồng canonical "
                "không đúng schema."
            )
        ) from error

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
                    "NEXTFARM_CROPS_JSON: "
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

    return items


def resolve_crop_text(
    text: str,
) -> ResolveCropResponse:
    """
    Resolve crop_text sang crop_id canonical.

    Không tự sinh ID khi không tìm thấy.
    """

    normalized_input = normalize_text(
        text
    )

    items = load_crop_master_data()

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
        candidates = [
            item.name,
            *item.aliases,
        ]

        for candidate in candidates:
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

    # 4. Không tìm thấy
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
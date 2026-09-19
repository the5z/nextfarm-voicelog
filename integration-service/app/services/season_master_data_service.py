from __future__ import annotations

import json
import os

from pydantic import ValidationError

from app.schemas.season_master_data import (
    ResolveSeasonResponse,
    SeasonMasterDataItem,
)
from app.services.normalization_service import (
    calculate_similarity,
    normalize_text,
)


SEASON_MASTER_DATA_ENV = (
    "NEXTFARM_SEASONS_JSON"
)

FUZZY_MATCH_THRESHOLD = 0.82


class SeasonMasterDataConfigurationError(
    RuntimeError
):
    """
    Cấu hình nguồn mùa vụ canonical không hợp lệ.
    """


def load_season_master_data(
) -> list[SeasonMasterDataItem]:
    """
    Đọc danh sách mùa vụ canonical từ biến môi trường.

    Integration không tự sinh season_id.
    """

    raw_value = os.getenv(
        SEASON_MASTER_DATA_ENV
    )

    if (
        raw_value is None
        or not raw_value.strip()
    ):
        raise SeasonMasterDataConfigurationError(
            (
                "Chưa cấu hình "
                "NEXTFARM_SEASONS_JSON."
            )
        )

    try:
        raw_items = json.loads(
            raw_value
        )

    except json.JSONDecodeError as error:
        raise SeasonMasterDataConfigurationError(
            (
                "NEXTFARM_SEASONS_JSON "
                "không phải JSON hợp lệ."
            )
        ) from error

    if not isinstance(raw_items, list):
        raise SeasonMasterDataConfigurationError(
            (
                "NEXTFARM_SEASONS_JSON "
                "phải là một JSON array."
            )
        )

    items: list[
        SeasonMasterDataItem
    ] = []

    try:
        for raw_item in raw_items:
            items.append(
                SeasonMasterDataItem.model_validate(
                    raw_item
                )
            )

    except ValidationError as error:
        raise SeasonMasterDataConfigurationError(
            (
                "Dữ liệu mùa vụ canonical "
                "không đúng schema."
            )
        ) from error

    seen_ids: set[str] = set()

    seen_terms: dict[
        str,
        str,
    ] = {}

    for item in items:
        if item.season_id in seen_ids:
            raise SeasonMasterDataConfigurationError(
                (
                    "Trùng season_id trong "
                    "NEXTFARM_SEASONS_JSON: "
                    f"{item.season_id}"
                )
            )

        seen_ids.add(
            item.season_id
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
                != item.season_id
            ):
                raise (
                    SeasonMasterDataConfigurationError(
                        (
                            "Tên/alias mùa vụ "
                            "bị trùng giữa nhiều "
                            "season_id: "
                            f"'{term}'."
                        )
                    )
                )

            seen_terms[
                normalized_term
            ] = item.season_id

    return items


def resolve_season_text(
    text: str,
) -> ResolveSeasonResponse:
    """
    Resolve season_text sang season_id canonical.

    Không tự sinh ID nếu không tìm thấy.
    """

    normalized_input = normalize_text(
        text
    )

    items = load_season_master_data()

    for item in items:
        if (
            normalized_input
            == normalize_text(
                item.name
            )
        ):
            return ResolveSeasonResponse(
                matched=True,
                season_id=(
                    item.season_id
                ),
                name=item.name,
                confidence=1.0,
                match_type="exact",
                matched_text=item.name,
                requires_confirmation=False,
                normalized_text=(
                    normalized_input
                ),
                message=(
                    "Đã khớp chính xác mùa vụ."
                ),
            )

    for item in items:
        for alias in item.aliases:
            if (
                normalized_input
                == normalize_text(alias)
            ):
                return ResolveSeasonResponse(
                    matched=True,
                    season_id=(
                        item.season_id
                    ),
                    name=item.name,
                    confidence=1.0,
                    match_type="alias",
                    matched_text=alias,
                    requires_confirmation=False,
                    normalized_text=(
                        normalized_input
                    ),
                    message=(
                        "Đã khớp bí danh mùa vụ."
                    ),
                )

    best_item: (
        SeasonMasterDataItem | None
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
        and best_matched_text
        is not None
        and best_score
        >= FUZZY_MATCH_THRESHOLD
    ):
        return ResolveSeasonResponse(
            matched=True,
            season_id=(
                best_item.season_id
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
                "Đã tìm thấy mùa vụ gần đúng. "
                "Cần người dùng xác nhận."
            ),
        )

    return ResolveSeasonResponse(
        matched=False,
        season_id=None,
        name=None,
        confidence=0.0,
        match_type="none",
        matched_text=None,
        requires_confirmation=True,
        normalized_text=(
            normalized_input
        ),
        message=(
            "Không tìm thấy mùa vụ phù hợp "
            "trong nguồn dữ liệu canonical."
        ),
    )
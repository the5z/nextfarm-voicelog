from __future__ import annotations

import json
import os

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.season import SeasonModel
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
    pass


def _validate_unique_items(
    items: list[SeasonMasterDataItem],
) -> None:
    seen_ids: set[str] = set()
    seen_terms: dict[str, str] = {}

    for item in items:
        if item.season_id in seen_ids:
            raise SeasonMasterDataConfigurationError(
                (
                    "Trùng season_id trong "
                    "nguồn dữ liệu mùa vụ: "
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
                raise SeasonMasterDataConfigurationError(
                    (
                        "Tên/alias mùa vụ bị trùng "
                        "giữa nhiều season_id: "
                        f"'{term}'."
                    )
                )

            seen_terms[
                normalized_term
            ] = item.season_id


def load_configured_season_master_data(
) -> list[SeasonMasterDataItem]:
    """
    Đọc nguồn canonical được cấu hình.

    Không cấu hình là hợp lệ nếu DB đã có
    mùa vụ được tạo bởi Integration.
    """

    raw_value = os.getenv(
        SEASON_MASTER_DATA_ENV
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
        raise SeasonMasterDataConfigurationError(
            (
                "NEXTFARM_SEASONS_JSON "
                "không phải JSON hợp lệ."
            )
        ) from error

    if not isinstance(
        raw_items,
        list,
    ):
        raise SeasonMasterDataConfigurationError(
            (
                "NEXTFARM_SEASONS_JSON "
                "phải là một JSON array."
            )
        )

    try:
        items = [
            SeasonMasterDataItem.model_validate(
                raw_item
            )
            for raw_item in raw_items
        ]

    except ValidationError as error:
        raise SeasonMasterDataConfigurationError(
            (
                "Dữ liệu mùa vụ canonical "
                "không đúng schema."
            )
        ) from error

    _validate_unique_items(
        items
    )

    return items


def _load_persisted_seasons(
    database_session: Session | None,
) -> list[SeasonMasterDataItem]:
    if database_session is None:
        return []

    statement = (
        select(SeasonModel)
        .where(
            SeasonModel.status
            == "saved"
        )
        .order_by(
            SeasonModel.id.asc()
        )
    )

    records = (
        database_session
        .scalars(statement)
        .all()
    )

    return [
        SeasonMasterDataItem(
            season_id=record.season_id,
            name=record.season_name,
            aliases=[],
        )
        for record in records
    ]


def load_season_master_data(
    database_session: Session | None = None,
) -> list[SeasonMasterDataItem]:
    """
    Trả nguồn mùa vụ hợp nhất:

    - cấu hình NEXTFARM_SEASONS_JSON
    - mùa vụ đã lưu trong Integration DB
    """

    items = [
        *load_configured_season_master_data(),
        *_load_persisted_seasons(
            database_session
        ),
    ]

    if not items:
        raise SeasonMasterDataConfigurationError(
            (
                "Chưa có nguồn dữ liệu mùa vụ. "
                "Hãy cấu hình NEXTFARM_SEASONS_JSON "
                "hoặc tạo mùa vụ trong Integration."
            )
        )

    _validate_unique_items(
        items
    )

    return items


def resolve_season_text(
    text: str,
    database_session: Session | None = None,
) -> ResolveSeasonResponse:
    normalized_input = normalize_text(
        text
    )

    items = load_season_master_data(
        database_session
    )

    for item in items:
        if (
            normalized_input
            == normalize_text(
                item.name
            )
        ):
            return ResolveSeasonResponse(
                matched=True,
                season_id=item.season_id,
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
                    season_id=item.season_id,
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
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.master_data import LOTS
from app.models.plot import PlotModel
from app.services.normalization_service import (
    calculate_similarity,
    normalize_text,
)


FUZZY_MATCH_THRESHOLD = 0.82


def load_plot_master_data(
    database_session: Session | None = None,
) -> list[dict[str, object]]:
    items: list[
        dict[str, object]
    ] = [
        {
            "code": record["code"],
            "name": record["name"],
            "aliases": list(
                record.get(
                    "aliases",
                    [],
                )
            ),
        }
        for record in LOTS
    ]

    if database_session is None:
        return items

    records = (
        database_session
        .scalars(
            select(PlotModel)
            .where(
                PlotModel.status
                == "saved"
            )
            .order_by(
                PlotModel.id.asc()
            )
        )
        .all()
    )

    items.extend(
        {
            "code": record.plot_code,
            "name": (
                record.plot_name_or_code
            ),
            "aliases": [],
        }
        for record in records
    )

    return items


def resolve_plot_text(
    text: str,
    database_session: Session | None = None,
) -> dict[str, object]:
    normalized_input = normalize_text(
        text
    )

    items = load_plot_master_data(
        database_session
    )

    for item in items:
        name = str(
            item["name"]
        )

        code = str(
            item["code"]
        )

        if (
            normalized_input
            == normalize_text(name)
        ):
            return {
                "matched": True,
                "code": code,
                "name": name,
                "confidence": 1.0,
                "match_type": "exact",
                "matched_text": name,
                "requires_confirmation": False,
                "normalized_text":
                    normalized_input,
                "message":
                    "Đã khớp chính xác thửa đất.",
            }

        if (
            normalized_input
            == normalize_text(code)
        ):
            return {
                "matched": True,
                "code": code,
                "name": name,
                "confidence": 1.0,
                "match_type": "exact",
                "matched_text": code,
                "requires_confirmation": False,
                "normalized_text":
                    normalized_input,
                "message":
                    "Đã khớp chính xác mã thửa đất.",
            }

    for item in items:
        code = str(
            item["code"]
        )

        name = str(
            item["name"]
        )

        aliases = list(
            item.get(
                "aliases",
                [],
            )
        )

        for alias in aliases:
            alias_text = str(alias)

            if (
                normalized_input
                == normalize_text(
                    alias_text
                )
            ):
                return {
                    "matched": True,
                    "code": code,
                    "name": name,
                    "confidence": 1.0,
                    "match_type": "alias",
                    "matched_text":
                        alias_text,
                    "requires_confirmation":
                        False,
                    "normalized_text":
                        normalized_input,
                    "message":
                        "Đã khớp bí danh thửa đất.",
                }

    best_item: (
        dict[str, object] | None
    ) = None

    best_matched_text: (
        str | None
    ) = None

    best_score = 0.0

    for item in items:
        candidates = [
            str(item["name"]),
            *[
                str(alias)
                for alias in item.get(
                    "aliases",
                    [],
                )
            ],
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
        return {
            "matched": True,
            "code": str(
                best_item["code"]
            ),
            "name": str(
                best_item["name"]
            ),
            "confidence": round(
                best_score,
                4,
            ),
            "match_type": "fuzzy",
            "matched_text":
                best_matched_text,
            "requires_confirmation": True,
            "normalized_text":
                normalized_input,
            "message": (
                "Đã tìm thấy thửa đất "
                "gần đúng. Cần người dùng "
                "xác nhận."
            ),
        }

    return {
        "matched": False,
        "code": None,
        "name": None,
        "confidence": 0.0,
        "match_type": "none",
        "matched_text": None,
        "requires_confirmation": True,
        "normalized_text":
            normalized_input,
        "message": (
            "Không tìm thấy thửa đất "
            "phù hợp."
        ),
    }
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Literal

from app.data.master_data import (
    ACTIVITIES,
    AMBIGUOUS_TERMS,
    UNITS,
    MasterDataRecord,
)


MasterDataType = Literal["activity", "unit"]


def normalize_text(value: str) -> str:
    """
    Chuẩn hóa văn bản nhưng vẫn giữ dấu tiếng Việt.

    Ví dụ:
        "  Rải   Phân! " -> "rải phân"
    """
    normalized = unicodedata.normalize("NFC", value)
    normalized = normalized.lower().strip()
    normalized = re.sub(r"[^\w\s-]", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized


def remove_vietnamese_accents(value: str) -> str:
    """
    Bỏ dấu để so sánh các biến thể như:
        ký, kí, ky
        thuốc, thuoc
    """
    decomposed = unicodedata.normalize("NFD", value)

    without_marks = "".join(
        char
        for char in decomposed
        if unicodedata.category(char) != "Mn"
    )

    return without_marks.replace("đ", "d").replace("Đ", "D")


def create_lookup_key(value: str) -> str:
    normalized = normalize_text(value)
    return remove_vietnamese_accents(normalized)


def get_records(data_type: MasterDataType) -> list[MasterDataRecord]:
    if data_type == "activity":
        return ACTIVITIES

    return UNITS


def resolve_master_data(
    data_type: MasterDataType,
    text: str,
) -> dict:
    """
    Tìm mã chuẩn từ một từ hoặc cụm từ địa phương.

    Ưu tiên:
    1. Khớp chính xác mã, tên hoặc alias.
    2. Khớp gần đúng để gợi ý.
    3. Không tự đổi các đơn vị mơ hồ.
    """
    normalized_text = normalize_text(text)
    lookup_key = create_lookup_key(text)

    ambiguous_message = AMBIGUOUS_TERMS.get(lookup_key)

    if data_type == "unit" and ambiguous_message is not None:
        return {
            "matched": False,
            "code": None,
            "name": None,
            "confidence": 0.0,
            "requires_confirmation": True,
            "normalized_text": normalized_text,
            "message": ambiguous_message,
        }

    records = get_records(data_type)

    # Khớp chính xác.
    for record in records:
        candidates = [
            record["code"],
            record["name"],
            *record["aliases"],
        ]

        candidate_keys = {
            create_lookup_key(candidate)
            for candidate in candidates
        }

        if lookup_key in candidate_keys:
            return {
                "matched": True,
                "code": record["code"],
                "name": record["name"],
                "confidence": 1.0,
                "requires_confirmation": False,
                "normalized_text": normalized_text,
                "message": "Đã chuẩn hóa chính xác.",
            }

    # Tìm kết quả gần giống nhất.
    best_record: MasterDataRecord | None = None
    best_score = 0.0

    for record in records:
        candidates = [
            record["name"],
            *record["aliases"],
        ]

        for candidate in candidates:
            candidate_key = create_lookup_key(candidate)

            score = SequenceMatcher(
                None,
                lookup_key,
                candidate_key,
            ).ratio()

            if score > best_score:
                best_score = score
                best_record = record

    if best_record is not None and best_score >= 0.82:
        return {
            "matched": True,
            "code": best_record["code"],
            "name": best_record["name"],
            "confidence": round(best_score, 2),
            "requires_confirmation": True,
            "normalized_text": normalized_text,
            "message": "Tìm thấy giá trị gần giống; cần người dùng xác nhận.",
        }

    return {
        "matched": False,
        "code": None,
        "name": None,
        "confidence": round(best_score, 2),
        "requires_confirmation": True,
        "normalized_text": normalized_text,
        "message": "Không tìm thấy giá trị phù hợp trong danh mục.",
    }
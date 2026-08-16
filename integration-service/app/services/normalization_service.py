from difflib import SequenceMatcher
import re
import unicodedata

from app.data.master_data import (
    ACTIVITIES,
    AMBIGUOUS_TERMS,
    LOTS,
    MATERIALS,
    UNITS,
)
from app.schemas.master_data import MasterDataType


FUZZY_MATCH_THRESHOLD = 0.82


MASTER_DATA_BY_TYPE = {
    "activity": ACTIVITIES,
    "unit": UNITS,
    "lot": LOTS,
    "material": MATERIALS,
}


def normalize_text(text: str) -> str:
    """
    Chuẩn hóa text để so sánh:
    - lowercase
    - bỏ dấu tiếng Việt
    - đổi đ -> d
    - bỏ ký tự thừa
    - gom khoảng trắng
    """
    text = text.strip().lower()
    text = text.replace("đ", "d")

    text = unicodedata.normalize("NFD", text)

    text = "".join(
        char
        for char in text
        if unicodedata.category(char) != "Mn"
    )

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def calculate_similarity(
    left: str,
    right: str,
) -> float:
    left_normalized = normalize_text(left)
    right_normalized = normalize_text(right)

    return SequenceMatcher(
        None,
        left_normalized,
        right_normalized,
    ).ratio()


def _is_ambiguous_term(text: str) -> bool:
    """
    Kiểm tra các từ nghiệp vụ/đơn vị mơ hồ như:
    xị, công, sào...

    Không tự động map những từ này sang business code.
    """
    normalized_input = normalize_text(text)

    if isinstance(AMBIGUOUS_TERMS, dict):
        for key, value in AMBIGUOUS_TERMS.items():
            if normalized_input == normalize_text(str(key)):
                return True

            # Hỗ trợ trường hợp value chỉ là chính thuật ngữ.
            if isinstance(value, str):
                if normalized_input == normalize_text(value):
                    return True

        return False

    for item in AMBIGUOUS_TERMS:
        if normalized_input == normalize_text(str(item)):
            return True

    return False


def _none_result(
    normalized_text: str,
) -> dict:
    return {
        "matched": False,
        "code": None,
        "name": None,
        "confidence": 0.0,
        "match_type": "none",
        "matched_text": None,
        "requires_confirmation": True,
        "normalized_text": normalized_text,
        "message": (
            "Không tìm thấy giá trị phù hợp trong danh mục."
        ),
    }


def _ambiguous_result(
    normalized_text: str,
) -> dict:
    return {
        "matched": False,
        "code": None,
        "name": None,
        "confidence": 0.0,
        "match_type": "ambiguous",
        "matched_text": None,
        "requires_confirmation": True,
        "normalized_text": normalized_text,
        "message": (
            "Giá trị này có thể khác nhau theo khu vực. "
            "Cần người dùng xác nhận."
        ),
    }


def resolve_master_data(
    data_type: MasterDataType,
    text: str,
) -> dict:
    normalized_input = normalize_text(text)

    if not normalized_input:
        return _none_result(
            normalized_text=normalized_input
        )

    # Đơn vị/cụm từ mơ hồ phải được chặn trước fuzzy matching.
    if _is_ambiguous_term(text):
        return _ambiguous_result(
            normalized_text=normalized_input
        )

    records = MASTER_DATA_BY_TYPE[data_type]

    # ---------------------------------------------------------
    # 1. EXACT MATCH VỚI NAME
    # ---------------------------------------------------------
    for record in records:
        name = record["name"]

        if normalized_input == normalize_text(name):
            return {
                "matched": True,
                "code": record["code"],
                "name": name,
                "confidence": 1.0,
                "match_type": "exact",
                "matched_text": name,
                "requires_confirmation": False,
                "normalized_text": normalized_input,
                "message": "Đã khớp chính xác.",
            }

    # ---------------------------------------------------------
    # 2. EXACT MATCH VỚI ALIAS
    # ---------------------------------------------------------
    for record in records:
        for alias in record.get("aliases", []):
            if normalized_input == normalize_text(alias):
                return {
                    "matched": True,
                    "code": record["code"],
                    "name": record["name"],
                    "confidence": 1.0,
                    "match_type": "alias",
                    "matched_text": alias,
                    "requires_confirmation": False,
                    "normalized_text": normalized_input,
                    "message": (
                        "Đã khớp bí danh nghiệp vụ."
                    ),
                }

    # ---------------------------------------------------------
    # 3. FUZZY MATCH
    # ---------------------------------------------------------
    best_record = None
    best_matched_text = None
    best_score = 0.0

    for record in records:
        candidates = [
            record["name"],
            *record.get("aliases", []),
        ]

        for candidate in candidates:
            score = calculate_similarity(
                text,
                candidate,
            )

            if score > best_score:
                best_score = score
                best_record = record
                best_matched_text = candidate

    if (
        best_record is not None
        and best_matched_text is not None
        and best_score >= FUZZY_MATCH_THRESHOLD
    ):
        return {
            "matched": True,
            "code": best_record["code"],
            "name": best_record["name"],
            "confidence": round(best_score, 4),
            "match_type": "fuzzy",
            "matched_text": best_matched_text,
            "requires_confirmation": True,
            "normalized_text": normalized_input,
            "message": (
                "Đã tìm thấy dữ liệu gần đúng. "
                "Cần người dùng xác nhận."
            ),
        }

    # ---------------------------------------------------------
    # 4. KHÔNG MATCH
    # ---------------------------------------------------------
    return _none_result(
        normalized_text=normalized_input
    )